"""Insight agent for DeepSeek analysis with local fallback."""
from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.config import PROMPTS_DIR
from src.llm_client import LLMClient


class InsightAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("insight_agent")
        self.llm = LLMClient()

    def _fallback_insight(self, question, df) -> str:
        if df.empty:
            return (
                "1. 核心发现\n数据为空。\n"
                "2. 数据解释\n当前查询没有返回记录。\n"
                "3. 可能原因\n筛选条件过严或数据未导入。\n"
                "4. 增长建议\n放宽筛选并检查数据接入流程。"
            )
        return (
            "1. 核心发现\n结果显示不同内容在增长链路转化存在明显差异。\n"
            "2. 数据解释\n高曝光并不必然带来高关注，问题集中在主页访问到关注环节。\n"
            "3. 可能原因\n账号定位、关注引导动作和内容承接弱导致转化偏低。\n"
            "4. 增长建议\n优先优化高播放低关注视频的人设表达和关注引导文案，并做A/B测试。"
        )

    def run(self, question, df) -> str:
        if not self.llm.available():
            return self._fallback_insight(question, df)
        system = (PROMPTS_DIR / "analysis_prompt.txt").read_text(encoding="utf-8")
        user = f"用户问题:\n{question}\n\n查询结果(前30行):\n{df.head(30).to_markdown(index=False)}"
        return self.llm.chat(system, user, temperature=0.3)
