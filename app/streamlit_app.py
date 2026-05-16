import random
import re
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.connectors.demo_connector import generate_demo_data
from src.llm_client import LLMClient
from src.main import run_pipeline
from src.memory_manager import load_history


def apply_light_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: #ffffff;
            color: #0f172a;
        }
        .card {
            background: #ffffff;
            border: 1px solid #d1d5db;
            border-radius: 14px;
            padding: 14px 16px;
            margin-bottom: 12px;
        }
        .metric-card {
            background: #f8fafc;
            border: 1px solid #d1d5db;
            border-radius: 12px;
            padding: 12px;
        }
        .small-title {
            color: #2563eb;
            font-size: 0.85rem;
            margin-bottom: 6px;
        }
        .main-title {
            color: #0f172a;
            font-weight: 700;
            font-size: 2rem;
            margin-bottom: 4px;
        }
        .subtitle {
            color: #334155;
            font-size: 1rem;
            margin-bottom: 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def infer_core_metric_cards(question: str, sql: str) -> list[dict]:
    s = sql.lower()

    if "高播放低关注" in question or "follow_per_view" in s:
        return [
            {"name": "view_count", "formula": "原始字段", "meaning": "播放量"},
            {"name": "follow_count", "formula": "原始字段", "meaning": "关注数"},
            {"name": "follow_per_view", "formula": "follow_count / view_count", "meaning": "播放到关注转化率"},
        ]
    if "关注转化率" in question or "follow_conversion_rate" in s:
        return [
            {"name": "profile_visit_count", "formula": "原始字段", "meaning": "主页访问数"},
            {"name": "follow_count", "formula": "原始字段", "meaning": "关注数"},
            {
                "name": "follow_conversion_rate",
                "formula": "follow_count / profile_visit_count",
                "meaning": "主页访问到关注转化率",
            },
        ]
    if "新增" in question or "new_user" in s:
        return [
            {"name": "new_user_count", "formula": "原始字段", "meaning": "新增用户数"},
            {"name": "viewer_count", "formula": "原始字段", "meaning": "观看用户数"},
            {"name": "new_user_ratio", "formula": "new_user_count / viewer_count", "meaning": "新用户占比"},
        ]
    return [
        {"name": "play_rate", "formula": "view_count / impression_count", "meaning": "曝光到播放转化率"},
        {
            "name": "follow_conversion_rate",
            "formula": "follow_count / profile_visit_count",
            "meaning": "主页访问到关注转化率",
        },
        {
            "name": "next_day_retention_rate",
            "formula": "next_day_active_user_count / new_user_count",
            "meaning": "次日留存率",
        },
    ]


def split_insight_sections(insight: str) -> dict[str, str]:
    sections = {
        "核心发现": "",
        "数据解释": "",
        "可能原因": "",
        "增长建议": "",
    }
    pattern = r"(?:^|\n)\s*[0-9]+\.\s*(核心发现|数据解释|可能原因|增长建议)\s*\n"
    matches = list(re.finditer(pattern, insight))
    if not matches:
        sections["核心发现"] = insight.strip()
        return sections

    for i, m in enumerate(matches):
        title = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(insight)
        sections[title] = insight[start:end].strip()
    return sections


st.set_page_config(page_title="Mini AirDA Plus", layout="wide")
apply_light_theme()

if "question_input" not in st.session_state:
    st.session_state.question_input = ""
if "placeholder_example" not in st.session_state:
    st.session_state.placeholder_example = random.choice(
        [
            "哪些视频高播放低关注？",
            "最近 7 天关注转化率趋势如何？",
            "哪个内容分类带来的新增用户最多？",
            "哪个环节流失最大？",
        ]
    )

mode_text = LLMClient().mode_name()

with st.sidebar:
    st.title("Mini AirDA Plus")
    st.caption(f"当前模式：{mode_text}")

    st.markdown("---")
    source = st.radio(
        "数据源选择",
        ["Demo 数据", "上传 CSV", "抖音链接 Beta", "B站链接 Beta"],
    )

    with st.expander("用户增长指标体系", expanded=False):
        st.markdown("曝光 → 播放 → 有效观看 → 互动 → 主页访问 → 关注 → 留存")
        st.markdown("- play_rate：播放率")
        st.markdown("- completion_rate：完播率")
        st.markdown("- engagement_user_rate：互动用户率")
        st.markdown("- follow_conversion_rate：关注转化率")
        st.markdown("- next_day_retention_rate：次日留存率")

    with st.expander("项目架构流程", expanded=False):
        st.markdown(
            "自然语言问题\n"
            "→ Planner\n"
            "→ SQLAgent\n"
            "→ SQLGuard\n"
            "→ SQLite\n"
            "→ ChartAgent\n"
            "→ InsightAgent\n"
            "→ 分析报告"
        )

    st.markdown("---")
    st.caption("Python / Streamlit / SQLite / Pandas / DeepSeek API")

st.markdown('<div class="main-title">Mini AirDA Plus｜AI 数据分析 Agent</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">输入自然语言问题，自动生成 SQL、图表和中文增长分析结论。</div>',
    unsafe_allow_html=True,
)

question = st.text_area(
    "请输入你的分析问题",
    value=st.session_state.question_input,
    placeholder=f"例如：{st.session_state.placeholder_example}",
    height=120,
)
st.session_state.question_input = question

csv_path = None
if source == "上传 CSV":
    uploaded = st.file_uploader("上传 CSV 文件", type=["csv"])
    if uploaded is not None:
        save_path = PROJECT_ROOT / "data" / "raw" / uploaded.name
        save_path.write_bytes(uploaded.getvalue())
        csv_path = str(save_path)
elif source == "Demo 数据":
    generate_demo_data()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="card"><div class="small-title">当前模式</div><div>{mode_text}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="card"><div class="small-title">数据源</div><div>{source}</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="card"><div class="small-title">数据库</div><div>SQLite 已连接</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="card"><div class="small-title">分析链路</div><div>SQL + 图表 + 中文结论</div></div>', unsafe_allow_html=True)

run = st.button("生成分析报告", type="primary", use_container_width=True)

if run:
    if source in ["抖音链接 Beta", "B站链接 Beta"]:
        st.warning("当前版本暂未接入真实链接解析，已预留 Connector 扩展位。")
    else:
        result = run_pipeline(
            question=question,
            source="demo" if source == "Demo 数据" else "csv",
            csv_path=csv_path,
        )

        st.subheader("1. 本次分析问题")
        st.markdown(f"<div class='card'>{question}</div>", unsafe_allow_html=True)

        st.subheader("2. 本次使用的核心指标")
        metrics = infer_core_metric_cards(question, result["sql"])
        mcols = st.columns(len(metrics))
        for idx, metric in enumerate(metrics):
            mcols[idx].markdown(
                (
                    "<div class='metric-card'>"
                    f"<div class='small-title'>{metric['name']}</div>"
                    f"<div><b>公式：</b>{metric['formula']}</div>"
                    f"<div><b>含义：</b>{metric['meaning']}</div>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

        st.subheader("3. 查询结果表格")
        st.dataframe(result["result_df"], use_container_width=True)

        st.subheader("4. 图表展示")
        if result["chart_path"]:
            st.image(result["chart_path"], caption="自动生成图表")
        else:
            st.info("当前结果未生成图表")

        st.subheader("5. 中文分析结论")
        sections = split_insight_sections(result["insight"])
        tabs = st.tabs(["核心发现", "数据解释", "可能原因", "增长建议"])
        tab_names = ["核心发现", "数据解释", "可能原因", "增长建议"]
        for i, tab_name in enumerate(tab_names):
            with tabs[i]:
                st.markdown(f"<div class='card'>{sections.get(tab_name, '').strip() or '暂无内容'}</div>", unsafe_allow_html=True)

        st.subheader("6. 生成 SQL")
        st.code(result["sql"], language="sql")

st.subheader("7. 历史记录")
with st.expander("历史分析记录", expanded=False):
    history = load_history()
    st.dataframe(
        pd.DataFrame(history[::-1])
        if history
        else pd.DataFrame(columns=["question", "sql", "result_summary", "chart_path", "insight", "timestamp"]),
        use_container_width=True,
    )
