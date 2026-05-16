import numpy as np
import pandas as pd
REQUIRED_COLUMNS=["date","video_id","video_title","content_category","impression_count","view_count","viewer_count","valid_viewer_count","complete_view_count","like_count","comment_count","share_count","collect_count","engaged_user_count","profile_visit_count","follow_count","active_user_count","new_user_count","return_user_count","next_day_active_user_count","day7_active_user_count","avg_watch_duration"]
NUMERIC_COLUMNS=[c for c in REQUIRED_COLUMNS if c not in {"date","video_id","video_title","content_category"}]
def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df=df.copy(); df.columns=[c.strip().lower() for c in df.columns]
    missing=[c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing: raise ValueError(f"Missing required columns: {missing}")
    df=df[REQUIRED_COLUMNS]
    df["date"]=pd.to_datetime(df["date"], errors="coerce").dt.date.astype(str)
    for col in NUMERIC_COLUMNS: df[col]=pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df
def _safe_div(a,b): return np.where(b==0,0,a/b)
def calculate_growth_metrics(df: pd.DataFrame) -> pd.DataFrame:
    out=df.copy()
    out["play_rate"]=_safe_div(out["view_count"],out["impression_count"])
    out["valid_view_rate"]=_safe_div(out["valid_viewer_count"],out["viewer_count"])
    out["completion_rate"]=_safe_div(out["complete_view_count"],out["view_count"])
    out["engagement_user_rate"]=_safe_div(out["engaged_user_count"],out["viewer_count"])
    out["profile_visit_rate"]=_safe_div(out["profile_visit_count"],out["viewer_count"])
    out["follow_conversion_rate"]=_safe_div(out["follow_count"],out["profile_visit_count"])
    out["new_user_ratio"]=_safe_div(out["new_user_count"],out["viewer_count"])
    out["next_day_retention_rate"]=_safe_div(out["next_day_active_user_count"],out["new_user_count"])
    out["day7_retention_rate"]=_safe_div(out["day7_active_user_count"],out["new_user_count"])
    for c in ["play_rate","valid_view_rate","completion_rate","engagement_user_rate","profile_visit_rate","follow_conversion_rate","new_user_ratio","next_day_retention_rate","day7_retention_rate"]: out[c]=out[c].round(4)
    return out
