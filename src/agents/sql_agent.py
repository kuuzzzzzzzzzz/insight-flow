"""SQL agent for DeepSeek SQL generation with local fallback."""
from __future__ import annotations

import re

from src.agents.base_agent import BaseAgent
from src.config import PROMPTS_DIR, TABLE_NAME
from src.llm_client import LLMClient

SQLITE_FORBIDDEN_PATTERNS = [
    r"\bANY_VALUE\s*\(",
    r"\bDATE_SUB\s*\(",
    r"\bINTERVAL\b",
    r"\bILIKE\b",
    r"\bREGEXP\b",
    r"\bQUALIFY\b",
    r"\bARRAY_AGG\s*\(",
    r"\bSTRING_AGG\s*\(",
    r"\bBOOL_OR\s*\(",
    r"\bBOOL_AND\s*\(",
    r"\bEXTRACT\s*\(",
    r"\bTOP\s+\d+\b",
]
COMPLEX_KEYWORDS = [
    "最好",
    "最差",
    "前10",
    "综合",
    "完整分析",
    "卡在哪个环节",
    "增长链路",
    "优化建议",
    "同时展示",
    "多指标",
]


class SQLAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("sql_agent")
        self.llm = LLMClient()

    def _fallback_sql(self, question: str) -> str:
        if "高播放低关注" in question:
            return (
                f"SELECT video_id, video_title, view_count, follow_count, "
                f"ROUND(CAST(follow_count AS REAL)/NULLIF(view_count,0),4) AS follow_per_view "
                f"FROM {TABLE_NAME} ORDER BY view_count DESC, follow_per_view ASC LIMIT 20"
            )
        if "新增" in question and "分类" in question:
            return (
                f"SELECT content_category, SUM(new_user_count) AS new_users "
                f"FROM {TABLE_NAME} GROUP BY content_category ORDER BY new_users DESC"
            )
        if "7" in question and "关注" in question and "趋势" in question:
            return (
                f"SELECT date, ROUND(AVG(follow_conversion_rate),4) AS follow_conversion_rate "
                f"FROM {TABLE_NAME} GROUP BY date ORDER BY date DESC LIMIT 7"
            )
        if "流失" in question or "漏斗" in question:
            return (
                f"SELECT SUM(impression_count) impression_count, SUM(view_count) view_count, "
                f"SUM(valid_viewer_count) valid_viewer_count, SUM(engaged_user_count) engaged_user_count, "
                f"SUM(profile_visit_count) profile_visit_count, SUM(follow_count) follow_count "
                f"FROM {TABLE_NAME}"
            )
        return f"SELECT * FROM {TABLE_NAME} LIMIT 20"

    def _extract_sql(self, raw: str) -> str:
        text = raw.strip()
        if "```" in text:
            parts = text.split("```")
            for part in parts:
                p = part.strip()
                if p.lower().startswith("sql"):
                    p = p[3:].strip()
                if p.upper().startswith("SELECT") or p.upper().startswith("WITH"):
                    return p
        if text.lower().startswith("sql"):
            text = text[3:].strip(": \n")
        return text

    def _is_sqlite_compatible(self, sql: str) -> bool:
        s = (sql or "").strip()
        if not s:
            return False
        for pattern in SQLITE_FORBIDDEN_PATTERNS:
            if re.search(pattern, s, flags=re.IGNORECASE):
                return False
        return True

    def _is_complex_question(self, question: str) -> bool:
        q = (question or "").strip()
        q_norm = re.sub(r"\s+", "", q).lower()
        keywords = [k.replace(" ", "").lower() for k in COMPLEX_KEYWORDS]
        hit_count = sum(1 for k in keywords if k and k in q_norm)
        if hit_count >= 1:
            return True
        # fallback: long multi-target analytics requests
        if len(q_norm) >= 80:
            return True
        if len(q_norm) >= 60 and ("视频维度" in q_norm or "留存率" in q_norm or "增长分析" in q_norm):
            return True
        return False

    def _rewrite_complex_question(self) -> str:
        return (
            "请按视频维度查询最近30个视频，返回 video_id、video_title、content_category、"
            "view_count、play_rate、completion_rate、engagement_user_rate、profile_visit_rate、"
            "follow_conversion_rate、new_user_ratio、next_day_retention_rate、day7_retention_rate，"
            "并计算 growth_score。growth_score = play_rate*0.2 + completion_rate*0.2 + "
            "engagement_user_rate*0.2 + profile_visit_rate*0.15 + follow_conversion_rate*0.15 + "
            "next_day_retention_rate*0.1。按 growth_score DESC 排序，返回前10条。"
            "仅使用 Schema 中存在的字段，不存在的字段忽略。只输出一条 SQLite SELECT 或 WITH...SELECT SQL。"
        )

    def _build_complex_stable_sql(self, schema_text: str) -> str:
        table = TABLE_NAME
        candidates = [
            ("video_id", "video_id", None),
            ("video_title", "MIN(video_title) AS video_title", None),
            ("content_category", "MIN(content_category) AS content_category", None),
            ("impression_count", "SUM(impression_count) AS impression_count", None),
            ("view_count", "SUM(view_count) AS view_count", None),
            ("valid_viewer_count", "SUM(valid_viewer_count) AS valid_viewer_count", None),
            ("engaged_user_count", "SUM(engaged_user_count) AS engaged_user_count", None),
            ("profile_visit_count", "SUM(profile_visit_count) AS profile_visit_count", None),
            ("follow_count", "SUM(follow_count) AS follow_count", None),
            ("play_rate", "ROUND(AVG(play_rate), 4) AS play_rate", 0.2),
            ("completion_rate", "ROUND(AVG(completion_rate), 4) AS completion_rate", 0.2),
            ("engagement_user_rate", "ROUND(AVG(engagement_user_rate), 4) AS engagement_user_rate", 0.2),
            ("profile_visit_rate", "ROUND(AVG(profile_visit_rate), 4) AS profile_visit_rate", 0.15),
            ("follow_conversion_rate", "ROUND(AVG(follow_conversion_rate), 4) AS follow_conversion_rate", 0.15),
            ("new_user_ratio", "ROUND(AVG(new_user_ratio), 4) AS new_user_ratio", None),
            ("next_day_retention_rate", "ROUND(AVG(next_day_retention_rate), 4) AS next_day_retention_rate", 0.1),
            ("day7_retention_rate", "ROUND(AVG(day7_retention_rate), 4) AS day7_retention_rate", None),
        ]
        existing = {f for f, _, _ in candidates if f == "video_id" or f in schema_text}
        select_parts = []
        score_terms = []
        for field, expr, weight in candidates:
            if field in existing:
                select_parts.append(expr if field != "video_id" else "video_id")
                if weight is not None:
                    score_terms.append(f"COALESCE(AVG({field}), 0) * {weight}")
        score_expr = " + ".join(score_terms) if score_terms else "0"
        select_clause = ",\n  ".join(select_parts + [f"ROUND(({score_expr}), 4) AS growth_score"])
        return (
            f"SELECT\n  {select_clause}\n"
            f"FROM {table}\n"
            f"WHERE date >= date((SELECT MAX(date) FROM {table}), '-30 days')\n"
            f"GROUP BY video_id\n"
            f"ORDER BY growth_score DESC\n"
            f"LIMIT 10"
        )

    def generate_sql(self, question: str, schema_text: str, metric_knowledge: str) -> str:
        if not self.llm.available():
            return self._fallback_sql(question)

        if self._is_complex_question(question):
            return self._build_complex_stable_sql(schema_text)

        sql_question = question
        system = (PROMPTS_DIR / "sql_prompt.txt").read_text(encoding="utf-8")
        user = (
            f"用户原始问题:\n{question}\n\n"
            f"用于生成SQL的问题:\n{sql_question}\n\n"
            f"数据库Schema:\n{schema_text}\n\n"
            f"指标知识:\n{metric_knowledge}\n"
        )
        sql = self.llm.chat(system_prompt=system, user_prompt=user, temperature=0.0)
        extracted = self._extract_sql(sql)
        if self._is_sqlite_compatible(extracted):
            return extracted

        repair_user = (
            user
            + "\n\n请重写为严格 SQLite 可执行 SQL。"
              "禁止 ANY_VALUE/DATE_SUB/INTERVAL/ILIKE/REGEXP/QUALIFY/"
              "ARRAY_AGG/STRING_AGG/BOOL_OR/BOOL_AND/EXTRACT/TOP。"
              "若 GROUP BY 包含文本字段，请将文本字段放入 GROUP BY 或使用 MIN/MAX。"
              "只输出一条 SELECT 或 WITH...SELECT SQL。"
        )
        repaired = self.llm.chat(system_prompt=system, user_prompt=repair_user, temperature=0.0)
        return self._extract_sql(repaired)
