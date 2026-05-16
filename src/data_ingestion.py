from __future__ import annotations

from datetime import datetime

import numpy as np
from sqlalchemy import create_engine

from src.config import DB_URL, TABLE_NAME, PROCESSED_DIR
from src.connectors.bilibili_connector import BilibiliFetchError, fetch_bilibili_up_videos
from src.connectors.csv_connector import load_csv
from src.connectors.demo_connector import generate_demo_data
from src.metric_calculator import calculate_growth_metrics, standardize_columns


def ingest_data(source="demo", csv_path=None, bilibili_input: str | None = None):
    if source == "demo":
        df = load_csv(generate_demo_data())
    elif source == "csv":
        if not csv_path:
            raise ValueError("csv_path is required when source='csv'")
        df = load_csv(csv_path)
    elif source == "bilibili":
        if not bilibili_input:
            raise BilibiliFetchError("source=bilibili 时 bilibili_input 不能为空。")
        raw_df = fetch_bilibili_up_videos(bilibili_input, limit=30)
        raw_df = _enrich_bilibili_raw(raw_df)
        engine = create_engine(DB_URL)
        raw_df.to_sql("bilibili_video_metrics", con=engine, if_exists="replace", index=False)
        df = _transform_bilibili_to_growth(raw_df)
    else:
        raise ValueError("source must be 'demo' or 'csv' or 'bilibili'")

    df = standardize_columns(df)
    processed = calculate_growth_metrics(df)
    # extra day7 retention metric for frontend use
    processed["day7_retention_rate"] = np.where(
        processed["new_user_count"] == 0,
        0,
        processed["day7_active_user_count"] / processed["new_user_count"],
    ).round(4)

    processed.to_csv(PROCESSED_DIR / "processed_growth_data.csv", index=False, encoding="utf-8-sig")
    processed.to_sql(TABLE_NAME, con=create_engine(DB_URL), if_exists="replace", index=False)
    return processed


def _enrich_bilibili_raw(df):
    out = df.copy()
    out["content_category"] = out["video_title"].apply(_classify_title)
    out["source"] = "bilibili"
    return out


def _classify_title(title: str) -> str:
    t = (title or "").lower()
    rules = [
        (["教程", "入门", "学习", "教学"], "教程"),
        (["测评", "开箱", "体验", "评测"], "测评"),
        (["游戏", "lol", "王者", "原神", "steam"], "游戏"),
        (["知识", "科普", "原理", "解释"], "知识"),
        (["生活", "日常", "vlog"], "生活"),
        (["搞笑", "沙雕", "名场面"], "搞笑"),
        (["ai", "python", "编程", "科技", "数码"], "科技"),
    ]
    for keys, cat in rules:
        if any(k in t for k in keys):
            return cat
    return "其他"


def _transform_bilibili_to_growth(raw_df):
    rng = np.random.default_rng(20240513)
    df = raw_df.copy()

    # engagement strength from real interaction density
    base_view = np.maximum(df["view_count"].astype(float), 1.0)
    inter_score = (
        df["like_count"] * 1.0
        + df["coin_count"] * 1.8
        + df["favorite_count"] * 2.2
        + df["comment_count"] * 1.5
        + df["share_count"] * 2.0
        + df["danmaku_count"] * 0.8
    ) / base_view
    inter_norm = np.clip(inter_score / (inter_score.quantile(0.85) + 1e-6), 0.15, 2.0)

    view_count = np.maximum(df["view_count"].astype(int), 1)
    impression_count = (view_count * (1.8 + 0.7 * (1.0 / inter_norm))).astype(int)
    viewer_count = np.maximum((view_count * (0.72 + 0.12 * inter_norm)).astype(int), 1)
    valid_viewer_count = np.maximum((viewer_count * (0.50 + 0.25 * inter_norm)).astype(int), 1)
    complete_view_count = np.maximum((view_count * (0.28 + 0.22 * inter_norm)).astype(int), 1)

    engaged_user_count = np.maximum((viewer_count * np.clip(0.10 + 0.35 * inter_norm, 0.08, 0.75)).astype(int), 1)
    profile_visit_count = np.maximum((viewer_count * np.clip(0.04 + 0.14 * inter_norm, 0.03, 0.35)).astype(int), 1)
    follow_count = np.maximum((profile_visit_count * np.clip(0.09 + 0.22 * inter_norm, 0.06, 0.6)).astype(int), 1)

    active_user_count = np.maximum((viewer_count * np.clip(0.55 + 0.20 * inter_norm, 0.45, 0.95)).astype(int), 1)
    new_user_count = np.maximum((viewer_count * np.clip(0.12 + 0.28 * (1.0 / inter_norm), 0.08, 0.6)).astype(int), 1)
    return_user_count = np.maximum(active_user_count - new_user_count, 0)

    next_day_active_user_count = np.maximum((new_user_count * np.clip(0.16 + 0.30 * inter_norm, 0.1, 0.7)).astype(int), 1)
    day7_active_user_count = np.maximum((new_user_count * np.clip(0.08 + 0.24 * inter_norm, 0.05, 0.5)).astype(int), 1)

    avg_watch_duration = np.round(np.clip(df["duration"].astype(float) * (0.22 + 0.25 * inter_norm), 6, 220), 2)

    out = {
        "date": [datetime.now().strftime("%Y-%m-%d")] * len(df),
        "video_id": df["bvid"],
        "video_title": df["video_title"],
        "content_category": df["content_category"],
        "impression_count": impression_count,
        "view_count": view_count,
        "viewer_count": viewer_count,
        "valid_viewer_count": valid_viewer_count,
        "complete_view_count": complete_view_count,
        "like_count": df["like_count"].astype(int),
        "comment_count": df["comment_count"].astype(int),
        "share_count": df["share_count"].astype(int),
        "collect_count": df["favorite_count"].astype(int),
        "engaged_user_count": engaged_user_count,
        "profile_visit_count": profile_visit_count,
        "follow_count": follow_count,
        "active_user_count": active_user_count,
        "new_user_count": new_user_count,
        "return_user_count": return_user_count,
        "next_day_active_user_count": next_day_active_user_count,
        "day7_active_user_count": day7_active_user_count,
        "avg_watch_duration": avg_watch_duration,
    }

    import pandas as pd

    return pd.DataFrame(out)
