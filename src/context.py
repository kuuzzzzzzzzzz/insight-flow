from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class QueryContext:
    question: str
    task_type: str = "sql_query"
    sql: str = ""
    result_summary: str = ""
    chart_path: Optional[str] = None
    insight: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
