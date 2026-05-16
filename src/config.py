"""Global configuration for Mini AirDA Plus."""
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
DEMO_DIR = DATA_DIR / "demo"
PROCESSED_DIR = DATA_DIR / "processed"
DATABASE_DIR = BASE_DIR / "database"
DB_PATH = DATABASE_DIR / "mini_airda.db"
DB_URL = f"sqlite:///{DB_PATH}"
OUTPUTS_DIR = BASE_DIR / "outputs"
CHARTS_DIR = BASE_DIR / "charts"
MEMORY_DIR = BASE_DIR / "memory"
QUERY_HISTORY_PATH = MEMORY_DIR / "query_history.json"
PROMPTS_DIR = BASE_DIR / "prompts"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
TABLE_NAME = "video_growth_metrics"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
for p in [RAW_DIR, DEMO_DIR, PROCESSED_DIR, DATABASE_DIR, OUTPUTS_DIR, CHARTS_DIR, MEMORY_DIR]:
    p.mkdir(parents=True, exist_ok=True)
if not QUERY_HISTORY_PATH.exists():
    QUERY_HISTORY_PATH.write_text("[]", encoding="utf-8")
