"""FastAPI backend for InsightFlow (frontend separation)."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Force non-GUI backend in API server context to avoid Tk thread issues.
os.environ.setdefault("MPLBACKEND", "Agg")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.schemas import AnalyzeRequest, AnalyzeResponse, MetricItem, MetricSystem
from src.connectors.bilibili_connector import BilibiliFetchError
from src.llm_client import LLMClient
from src.main import SQLGenerationError, run_pipeline

app = FastAPI(title="InsightFlow Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

METRIC_CHAIN = "曝光 → 播放 → 有效观看 → 互动 → 主页访问 → 关注 → 留存"
FIELD_LABEL_MAP = {
    "video_title": "视频标题",
    "content_category": "内容分类",
    "view_count": "播放量",
    "total_views": "播放量",
    "like_count": "点赞数",
    "favorite_count": "收藏数",
    "comment_count": "评论数",
    "share_count": "分享数",
    "danmaku_count": "弹幕数",
    "new_user_count": "新增用户数",
    "play_rate": "播放率",
    "completion_rate": "完播率",
    "engagement_user_rate": "互动用户率",
    "profile_visit_rate": "主页访问率",
    "follow_conversion_rate": "关注转化率",
    "new_user_ratio": "新用户占比",
    "next_day_retention_rate": "次日留存率",
    "day7_retention_rate": "7日留存率",
    "growth_score": "综合增长得分",
}

METRIC_CATALOG: Dict[str, MetricItem] = {
    "play_rate": MetricItem(name="play_rate", label="播放率", formula="view_count / impression_count", meaning="曝光到播放的转化率"),
    "valid_view_rate": MetricItem(name="valid_view_rate", label="有效观看率", formula="valid_viewer_count / viewer_count", meaning="观看用户中有效观看占比"),
    "completion_rate": MetricItem(name="completion_rate", label="完播率", formula="complete_view_count / view_count", meaning="播放到完播的转化率"),
    "engagement_user_rate": MetricItem(name="engagement_user_rate", label="互动用户率", formula="engaged_user_count / viewer_count", meaning="观看用户中互动用户占比"),
    "profile_visit_rate": MetricItem(name="profile_visit_rate", label="主页访问率", formula="profile_visit_count / viewer_count", meaning="观看用户访问主页比例"),
    "follow_conversion_rate": MetricItem(name="follow_conversion_rate", label="关注转化率", formula="follow_count / profile_visit_count", meaning="主页访问后的关注转化率"),
    "new_user_ratio": MetricItem(name="new_user_ratio", label="新用户占比", formula="new_user_count / viewer_count", meaning="观看用户中新用户占比"),
    "next_day_retention_rate": MetricItem(name="next_day_retention_rate", label="次日留存率", formula="next_day_active_user_count / new_user_count", meaning="新用户次日活跃比例"),
    "view_count": MetricItem(name="view_count", label="播放量", formula="", meaning="衡量视频播放规模"),
    "follow_count": MetricItem(name="follow_count", label="关注数", formula="", meaning="衡量关注规模"),
    "profile_visit_count": MetricItem(name="profile_visit_count", label="主页访问数", formula="", meaning="衡量主页导流规模"),
    "viewer_count": MetricItem(name="viewer_count", label="观看用户数", formula="", meaning="衡量观看用户规模"),
    "new_user_count": MetricItem(name="new_user_count", label="新增用户数", formula="", meaning="衡量新增用户规模"),
    "follow_per_view": MetricItem(name="follow_per_view", label="播放到关注转化率", formula="follow_count / view_count", meaning="播放到关注的转化效率"),
}


def infer_metrics_used(question: str, sql: str) -> List[MetricItem]:
    q = question.lower()
    s = sql.lower()
    if "高播放低关注" in question or "follow_per_view" in s:
        keys = ["view_count", "follow_count", "follow_per_view"]
    elif "关注转化率" in question or "follow_conversion_rate" in s:
        keys = ["profile_visit_count", "follow_count", "follow_conversion_rate"]
    elif "新增" in question or "new_user" in s:
        keys = ["new_user_count", "viewer_count", "new_user_ratio"]
    else:
        keys = ["play_rate", "follow_conversion_rate", "next_day_retention_rate"]
    return [METRIC_CATALOG[k] for k in keys]


def split_insight_sections(insight) -> Dict[str, str]:
    sections = {"核心发现": "暂无内容", "数据解释": "暂无内容", "可能原因": "暂无内容", "增长建议": "暂无内容"}
    alias_map = {
        "核心发现": ["核心发现"],
        "数据解释": ["数据解释", "数据解读", "数据解释（按漏斗环节拆解）"],
        "可能原因": ["可能原因", "可能原因分析", "原因分析"],
        "增长建议": ["增长建议", "增长建议与优化方向", "优化建议", "建议"],
    }

    def _canon_title(title: str) -> str | None:
        t = (title or "").strip()
        for k, aliases in alias_map.items():
            if any(a in t for a in aliases):
                return k
        return None

    def _parse_text(text: str) -> Dict[str, str]:
        out = {"核心发现": "", "数据解释": "", "可能原因": "", "增长建议": ""}
        if not text or not text.strip():
            return out
        normalized = text.replace("\r\n", "\n")
        heading_regex = (
            r"(?m)^\s*"
            r"(?:#{1,6}\s*)?"
            r"(?:\*\*)?"
            r"(?:[一二三四五六七八九十]+\s*[、.．:：]\s*|\d+\s*[、.．:：]\s*)?"
            r"(?P<title>核心发现|数据解释(?:（按漏斗环节拆解）)?|数据解读|可能原因(?:分析)?|原因分析|增长建议(?:与优化方向)?|优化建议|建议)"
            r"(?:\*\*)?"
            r"\s*$"
        )
        matches = list(re.finditer(heading_regex, normalized))
        if not matches:
            out["核心发现"] = normalized.strip()
            return out

        for i, m in enumerate(matches):
            canonical = _canon_title(m.group("title") or "")
            if not canonical:
                continue
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(normalized)
            content = normalized[start:end].strip()
            if content:
                out[canonical] = (out[canonical] + "\n\n" + content).strip() if out[canonical] else content
        return out

    # 1) dict input: normalize by keys first
    if isinstance(insight, dict):
        merged_parts = []
        for k, v in insight.items():
            canonical = _canon_title(str(k))
            if canonical and str(v).strip():
                merged_parts.append(f"{canonical}\n{str(v).strip()}")
        parsed = _parse_text("\n\n".join(merged_parts))
        for k in sections.keys():
            if parsed.get(k):
                sections[k] = parsed[k]
        return sections

    # 2) string input
    text = str(insight or "").strip()
    parsed = _parse_text(text)
    for k in sections.keys():
        if parsed.get(k):
            sections[k] = parsed[k]
    return sections


def build_chart_payload(question: str, df):
    if df.empty:
        return "bar", []

    q = question.lower()
    cols = list(df.columns)
    numeric_cols = [c for c in cols if str(df[c].dtype).startswith(("int", "float"))]
    dim_cols = [c for c in cols if c not in numeric_cols]
    preferred_rate_metrics = [
        "play_rate",
        "completion_rate",
        "engagement_user_rate",
        "profile_visit_rate",
        "follow_conversion_rate",
        "next_day_retention_rate",
        "valid_view_rate",
        "new_user_ratio",
    ]
    question_metric_map = {
        "new_user_count": ["new_user_count"],
        "新增用户数": ["new_user_count"],
        "new_user_ratio": ["new_user_ratio"],
        "新用户占比": ["new_user_ratio"],
        "play_rate": ["play_rate"],
        "播放率": ["play_rate"],
        "completion_rate": ["completion_rate"],
        "完播率": ["completion_rate"],
        "engagement_user_rate": ["engagement_user_rate"],
        "互动用户率": ["engagement_user_rate"],
        "profile_visit_rate": ["profile_visit_rate"],
        "主页访问率": ["profile_visit_rate"],
        "follow_conversion_rate": ["follow_conversion_rate"],
        "关注转化率": ["follow_conversion_rate"],
        "next_day_retention_rate": ["next_day_retention_rate"],
        "次日留存率": ["next_day_retention_rate"],
        "valid_view_rate": ["valid_view_rate"],
        "有效观看率": ["valid_view_rate"],
    }

    # Multi-series chart for growth-rate analysis.
    # 1) prioritize metrics explicitly mentioned in question
    # 2) fallback to preferred_rate_metrics
    q_lower = q.lower()
    selected_metrics: List[str] = []
    for key, mapped in question_metric_map.items():
        if key.lower() in q_lower:
            for m in mapped:
                if m in df.columns and m not in selected_metrics:
                    selected_metrics.append(m)

    if len(selected_metrics) < 2:
        for m in preferred_rate_metrics:
            if m in df.columns and m not in selected_metrics:
                selected_metrics.append(m)

    selected_metrics = selected_metrics[:5]

    if len(selected_metrics) >= 2:
        if "video_title" in df.columns:
            x_col = "video_title"
        elif "video_id" in df.columns:
            x_col = "video_id"
        elif "date" in df.columns:
            x_col = "date"
        elif dim_cols:
            x_col = dim_cols[0]
        else:
            x_col = None

        if x_col:
            x_axis = [str(v) for v in df[x_col].tolist()]
        else:
            x_axis = [str(i + 1) for i in range(len(df))]

        series = []
        for col in selected_metrics:
            series.append(
                {
                    "name": col,
                    "data": [float(v) if v is not None else 0.0 for v in df[col].tolist()],
                }
            )

        chart_type = "line" if ("趋势" in q or "date" in [c.lower() for c in df.columns]) else "bar"
        return chart_type, {"xAxis": x_axis, "series": series}

    if "漏斗" in q or "流失" in q:
        steps = ["impression_count", "view_count", "valid_viewer_count", "engaged_user_count", "profile_visit_count", "follow_count"]
        data = [{"name": s, "value": float(df[s].sum())} for s in steps if s in df.columns]
        return "funnel", data

    if len(numeric_cols) == 1 and dim_cols:
        dim = dim_cols[0]
        val = numeric_cols[0]
        if "趋势" in q or dim.lower() == "date":
            return "line", [{"x": str(r[dim]), "y": float(r[val])} for _, r in df.iterrows()]
        if len(df) <= 8:
            return "pie", [{"name": str(r[dim]), "value": float(r[val])} for _, r in df.iterrows()]
        return "bar", [{"x": str(r[dim]), "y": float(r[val])} for _, r in df.iterrows()]

    if len(numeric_cols) >= 2:
        x = dim_cols[0] if dim_cols else df.index.name or "index"
        y = numeric_cols[0]
        tmp = df.reset_index() if x == "index" else df
        return "bar", [{"x": str(r[x]), "y": float(r[y])} for _, r in tmp.iterrows()]

    first_col = cols[0]
    return "bar", [{"x": str(i), "y": 0, "label": str(v)} for i, v in enumerate(df[first_col].tolist())]


def build_charts_payload(question: str, df) -> List[Dict]:
    """Build up to 4 business charts: scale, efficiency, growth score, funnel."""
    charts: List[Dict] = []
    if df.empty:
        return charts

    dfx = df.head(10).copy()
    x_candidates = ["video_title", "video_id", "content_category", "date"]
    x_col = next((c for c in x_candidates if c in dfx.columns), None)
    x_axis = [str(v) for v in dfx[x_col].tolist()] if x_col else [str(i + 1) for i in range(len(dfx))]

    def _series(metric_cols: List[str], frame) -> List[Dict]:
        out = []
        for col in metric_cols:
            if col not in frame.columns:
                continue
            vals = [float(v) if v is not None else 0.0 for v in frame[col].tolist()]
            out.append({"name": FIELD_LABEL_MAP.get(col, col), "data": vals})
        return out

    # 1) 规模指标对比
    scale_fields = ["view_count", "total_views", "like_count", "favorite_count", "comment_count", "share_count", "danmaku_count", "new_user_count"]
    existing_scale = [c for c in scale_fields if c in dfx.columns]
    if existing_scale:
        # avoid duplicate "播放量" when both total_views and view_count are present
        if "total_views" in existing_scale and "view_count" in existing_scale:
            existing_scale = [c for c in existing_scale if c != "view_count"]
        existing_scale = existing_scale[:5]
        charts.append(
            {
                "title": "规模指标对比",
                "chart_type": "bar",
                "chart_data": {"xAxis": x_axis, "series": _series(existing_scale, dfx)},
            }
        )

    # 2) 效率指标对比
    rate_fields = [
        "play_rate",
        "completion_rate",
        "engagement_user_rate",
        "profile_visit_rate",
        "follow_conversion_rate",
        "new_user_ratio",
        "next_day_retention_rate",
        "day7_retention_rate",
    ]
    existing_rates = [c for c in rate_fields if c in dfx.columns][:5]
    if len(existing_rates) >= 2:
        charts.append(
            {
                "title": "效率指标对比",
                "chart_type": "bar",
                "chart_data": {"xAxis": x_axis, "series": _series(existing_rates, dfx)},
            }
        )

    # 3) 综合增长得分排行
    if "growth_score" in dfx.columns:
        rank_x_candidates = ["video_title", "video_id", "content_category"]
        rank_x_col = next((c for c in rank_x_candidates if c in dfx.columns), None)
        rank_df = dfx.sort_values(by="growth_score", ascending=False).head(10).copy()
        rank_x = [str(v) for v in rank_df[rank_x_col].tolist()] if rank_x_col else [str(i + 1) for i in range(len(rank_df))]
        charts.append(
            {
                "title": "综合增长得分排行",
                "chart_type": "bar",
                "chart_data": {
                    "xAxis": rank_x,
                    "series": _series(["growth_score"], rank_df),
                },
            }
        )

    # 4) 增长漏斗分析
    funnel_fields = [
        ("impression_count", "曝光"),
        ("view_count", "播放"),
        ("valid_viewer_count", "有效观看"),
        ("engaged_user_count", "互动"),
        ("profile_visit_count", "主页访问"),
        ("follow_count", "关注"),
    ]
    available_funnel = [(field, label) for field, label in funnel_fields if field in df.columns]
    if len(available_funnel) >= 3:
        funnel_data = [{"name": label, "value": float(df[field].sum())} for field, label in available_funnel]
        charts.append({"title": "增长漏斗分析", "chart_type": "funnel", "chart_data": funnel_data})

    return charts[:4]


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "project": "InsightFlow"}


@app.get("/mode")
def mode() -> Dict[str, str]:
    return {"mode": LLMClient().mode_name()}


@app.post("/analyze")
def analyze(payload: AnalyzeRequest):
    if payload.source == "douyin":
        raise HTTPException(status_code=400, detail="当前版本暂未接入真实链接解析，已预留 Connector 扩展位。")

    if payload.source == "bilibili" and not (payload.bilibili_input or "").strip():
        return {
            "error": "B站数据拉取失败：请输入 B站 UP 主 UID 或主页链接",
            "detail": "source=bilibili 时 bilibili_input 不能为空",
            "source": "bilibili",
            "input": payload.bilibili_input or "",
        }

    try:
        result = run_pipeline(
            question=payload.question,
            source=payload.source,
            bilibili_input=payload.bilibili_input,
        )
    except BilibiliFetchError as e:
        return {
            "error": f"B站数据拉取失败：{e}",
            "detail": str(e),
            "source": "bilibili",
            "input": payload.bilibili_input or "",
        }
    except SQLGenerationError as e:
        return {"error": "SQL 生成失败，请换个问题重试", "raw_sql": e.raw_sql}
    except ValueError as e:
        if payload.source == "bilibili":
            return {
                "error": f"B站数据拉取失败：{e}",
                "detail": str(e),
                "source": "bilibili",
                "input": payload.bilibili_input or "",
            }
        return {"error": "SQL 生成失败，请换个问题重试", "raw_sql": str(e)}

    df = result["result_df"].head(50).copy()

    charts = build_charts_payload(payload.question, df)
    if charts:
        chart_type = charts[0]["chart_type"]
        chart_data = charts[0]["chart_data"]
    else:
        chart_type, chart_data = build_chart_payload(payload.question, df)

    response = AnalyzeResponse(
        question=payload.question,
        mode=LLMClient().mode_name(),
        metrics_used=infer_metrics_used(payload.question, result["sql"]),
        metric_system=MetricSystem(
            chain=METRIC_CHAIN,
            metrics=[
                METRIC_CATALOG["play_rate"],
                METRIC_CATALOG["valid_view_rate"],
                METRIC_CATALOG["completion_rate"],
                METRIC_CATALOG["engagement_user_rate"],
                METRIC_CATALOG["profile_visit_rate"],
                METRIC_CATALOG["follow_conversion_rate"],
                METRIC_CATALOG["new_user_ratio"],
                METRIC_CATALOG["next_day_retention_rate"],
            ],
        ),
        sql=result["sql"],
        table_columns=df.columns.tolist(),
        table_rows=df.to_dict(orient="records"),
        charts=charts,
        chart_type=chart_type,
        chart_data=chart_data,
        insight=split_insight_sections(result["insight"]),
    )
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)

