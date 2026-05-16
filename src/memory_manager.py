import json
from datetime import datetime
from src.config import QUERY_HISTORY_PATH

def load_history():
    if not QUERY_HISTORY_PATH.exists(): return []
    try: return json.loads(QUERY_HISTORY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError: return []

def save_record(question, sql, result_summary, chart_path, insight):
    history=load_history()
    history.append({"question":question,"sql":sql,"result_summary":result_summary,"chart_path":chart_path,"insight":insight,"timestamp":datetime.now().isoformat(timespec="seconds")})
    QUERY_HISTORY_PATH.write_text(json.dumps(history[-50:], ensure_ascii=False, indent=2), encoding="utf-8")
