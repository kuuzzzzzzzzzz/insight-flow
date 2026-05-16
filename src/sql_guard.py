import re

FORBIDDEN = {"DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE", "REPLACE", "PRAGMA", "ATTACH", "DETACH"}


def check_sql_safe(sql: str):
    s = sql.strip().strip(";")
    if not s:
        raise ValueError("Empty SQL is not allowed.")

    # Allow read-only query forms:
    # 1) SELECT ...
    # 2) WITH ... SELECT ... (CTE that ultimately selects)
    if re.match(r"^SELECT\b", s, flags=re.IGNORECASE):
        pass
    elif re.match(r"^WITH\b", s, flags=re.IGNORECASE):
        if not re.search(r"\)\s*SELECT\b", s, flags=re.IGNORECASE | re.DOTALL):
            raise ValueError("Only SELECT/CTE SELECT queries are allowed.")
    else:
        raise ValueError("Only SELECT/CTE SELECT queries are allowed.")

    upper = re.sub(r"\s+", " ", s.upper())
    for kw in FORBIDDEN:
        if re.search(rf"\b{kw}\b", upper):
            raise ValueError(f"Forbidden keyword detected: {kw}")
