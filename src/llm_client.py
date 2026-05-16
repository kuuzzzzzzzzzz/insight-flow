"""DeepSeek client wrapper via OpenAI-compatible SDK."""
from __future__ import annotations

from openai import OpenAI

from src.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL


class LLMClient:
    """Read configuration from env and call DeepSeek when key is available."""

    def __init__(self) -> None:
        self.api_key = DEEPSEEK_API_KEY
        self.base_url = DEEPSEEK_BASE_URL
        self.model = DEEPSEEK_MODEL
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url) if self.api_key else None

    def available(self) -> bool:
        return self.client is not None

    def mode_name(self) -> str:
        return "DeepSeek API 模式" if self.available() else "fallback 本地模拟模式"

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        if not self.client:
            raise RuntimeError("DeepSeek API key is missing.")
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return (resp.choices[0].message.content or "").strip()
