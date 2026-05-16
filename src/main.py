import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.chart_agent import ChartAgent
from src.agents.data_quality_agent import DataQualityAgent
from src.agents.insight_agent import InsightAgent
from src.agents.sql_agent import SQLAgent
from src.config import KNOWLEDGE_DIR, OUTPUTS_DIR
from src.data_ingestion import ingest_data
from src.llm_client import LLMClient
from src.memory_manager import save_record
from src.planner import classify_task
from src.schema_reader import read_schema, schema_to_text
from src.sql_executor import execute_sql
from src.sql_guard import check_sql_safe


class SQLGenerationError(ValueError):
    """Raised when model SQL cannot be cleaned into a safe SELECT statement."""

    def __init__(self, message: str, raw_sql: str = "") -> None:
        super().__init__(message)
        self.raw_sql = raw_sql


def sanitize_sql_output(raw_sql: str) -> str:
    """Extract SELECT/CTE query and strip markdown/explanation text."""
    text = (raw_sql or "").strip()
    if not text:
        return ""

    text = re.sub(r"```sql", "", text, flags=re.IGNORECASE)
    text = text.replace("```", "")

    m_with = re.search(r"\bWITH\b", text, flags=re.IGNORECASE)
    m_select = re.search(r"\bSELECT\b", text, flags=re.IGNORECASE)
    if m_with and (not m_select or m_with.start() <= m_select.start()):
        text = text[m_with.start() :].strip()
    elif m_select:
        text = text[m_select.start() :].strip()
    else:
        return text.strip()

    semi = text.find(";")
    if semi != -1:
        text = text[: semi + 1]

    return text.strip()


def _is_select_or_cte_select(sql: str) -> bool:
    s = (sql or "").strip()
    return bool(
        re.match(r"^SELECT\b", s, flags=re.IGNORECASE)
        or re.match(r"^WITH\b", s, flags=re.IGNORECASE)
    )


def run_pipeline(
    question: str,
    source: str = "demo",
    csv_path: str | None = None,
    bilibili_input: str | None = None,
):
    processed_df = ingest_data(source=source, csv_path=csv_path, bilibili_input=bilibili_input)
    dq_path = DataQualityAgent().run(processed_df)
    task_type = classify_task(question)

    schema_text = schema_to_text(read_schema())
    metric_knowledge = (KNOWLEDGE_DIR / "metric_definitions.md").read_text(encoding="utf-8")

    raw_sql = SQLAgent().generate_sql(question=question, schema_text=schema_text, metric_knowledge=metric_knowledge)
    sql = sanitize_sql_output(raw_sql)
    if not _is_select_or_cte_select(sql):
        raise SQLGenerationError("SQL 生成失败，请换个问题重试", raw_sql=raw_sql)

    check_sql_safe(sql)

    try:
        result_df = execute_sql(sql)
    except Exception:
        raise SQLGenerationError("SQL 生成失败，请换个问题重试", raw_sql=raw_sql)
    chart_path = ChartAgent().run(result_df, question)
    insight = InsightAgent().run(question, result_df)

    (OUTPUTS_DIR / "analysis_report.md").write_text(insight, encoding="utf-8")
    summary = f"rows={len(result_df)}, columns={list(result_df.columns)}"
    save_record(question, sql, summary, str(chart_path) if chart_path else "", insight)

    return {
        "task_type": task_type,
        "sql": sql,
        "result_df": result_df,
        "chart_path": str(chart_path) if chart_path else "",
        "insight": insight,
        "data_quality_report": str(dq_path),
    }


def main():
    parser = argparse.ArgumentParser(description="Mini AirDA Plus")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--csv", type=str, default=None)
    parser.add_argument("--bilibili-input", type=str, default=None)
    parser.add_argument("--question", type=str, default="哪个视频高播放低关注？")
    args = parser.parse_args()

    print(f"当前模式：{LLMClient().mode_name()}")

    if args.bilibili_input:
        source = "bilibili"
    else:
        source = "demo" if args.demo or not args.csv else "csv"
    result = run_pipeline(
        question=args.question,
        source=source,
        csv_path=args.csv,
        bilibili_input=args.bilibili_input,
    )

    print("=== Mini AirDA Plus ===")
    print(f"Task Type: {result['task_type']}")
    print(f"SQL: {result['sql']}")
    print(f"Chart: {result['chart_path']}")
    print("Insight:\n" + result["insight"])


if __name__ == "__main__":
    main()
