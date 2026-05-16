import sqlite3
from src.config import DB_PATH, TABLE_NAME

def read_schema(table_name: str = TABLE_NAME, sample_limit: int = 3):
    conn=sqlite3.connect(DB_PATH); conn.row_factory=sqlite3.Row; cur=conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})"); columns=cur.fetchall()
    if not columns: conn.close(); raise ValueError(f"Table not found: {table_name}")
    col_defs=[{"name":c["name"],"type":c["type"]} for c in columns]
    cur.execute(f"SELECT * FROM {table_name} LIMIT ?", (sample_limit,))
    samples=[dict(r) for r in cur.fetchall()]; conn.close()
    return {"table_name":table_name,"columns":col_defs,"sample_rows":samples}

def schema_to_text(schema: dict) -> str:
    lines=[f"Table: {schema['table_name']}","Columns:"]
    for c in schema["columns"]: lines.append(f"- {c['name']} ({c['type']})")
    lines.append("Sample Rows:")
    for row in schema["sample_rows"]: lines.append(str(row))
    return "\n".join(lines)
