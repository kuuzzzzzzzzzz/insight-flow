from pathlib import Path
import numpy as np
import pandas as pd
from src.config import OUTPUTS_DIR

def generate_data_quality_report(df: pd.DataFrame) -> Path:
    row_count,col_count=df.shape
    missing=df.isna().sum().sort_values(ascending=False)
    duplicates=int(df.duplicated().sum())
    numeric_cols=df.select_dtypes(include=[np.number]).columns
    outlier_info={}
    for c in numeric_cols:
        q1=df[c].quantile(0.25); q3=df[c].quantile(0.75); iqr=q3-q1
        if iqr==0: outlier_info[c]=0; continue
        low=q1-1.5*iqr; high=q3+1.5*iqr
        outlier_info[c]=int(((df[c]<low)|(df[c]>high)).sum())
    lines=["# 数据质量报告","",f"- 行数: {row_count}",f"- 列数: {col_count}",f"- 重复值数量: {duplicates}","","## 字段类型"]
    for c,t in df.dtypes.items(): lines.append(f"- {c}: {t}")
    lines += ["", "## 缺失值", ""]
    for c,v in missing.items(): lines.append(f"- {c}: {int(v)}")
    lines += ["", "## 异常值(IQR)", ""]
    for c,v in outlier_info.items(): lines.append(f"- {c}: {v}")
    out_path=OUTPUTS_DIR / "data_quality_report.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
