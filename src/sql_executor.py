import pandas as pd
from sqlalchemy import create_engine
from src.config import DB_URL, OUTPUTS_DIR

def execute_sql(sql: str) -> pd.DataFrame:
    df=pd.read_sql_query(sql, create_engine(DB_URL))
    df.to_csv(OUTPUTS_DIR / "query_result.csv", index=False, encoding="utf-8-sig")
    return df
