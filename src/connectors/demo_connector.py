from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from src.config import DEMO_DIR
CONTENT_CATEGORIES = ["剧情", "知识", "测评", "搞笑", "生活", "运动"]
def generate_demo_data(rows: int = 140, seed: int = 42):
    rng = np.random.default_rng(seed)
    start_date = datetime.now().date() - timedelta(days=29)
    records = []
    for i in range(rows):
        d = start_date + timedelta(days=int(i % 30))
        category = CONTENT_CATEGORIES[i % len(CONTENT_CATEGORIES)]
        impression = int(rng.integers(3000, 50000))
        view = int(impression * rng.uniform(0.15, 0.55))
        viewer = max(1, int(view * rng.uniform(0.65, 0.95)))
        valid_viewer = int(viewer * rng.uniform(0.45, 0.85))
        complete_view = int(view * rng.uniform(0.2, 0.7))
        engaged_user = int(viewer * rng.uniform(0.08, 0.45))
        profile_visit = int(viewer * rng.uniform(0.03, 0.2))
        follow = int(profile_visit * rng.uniform(0.08, 0.45))
        records.append({
            "date": d.isoformat(),"video_id": f"VID_{1000+i}","video_title": f"{category}短视频_{i+1}","content_category": category,
            "impression_count": impression,"view_count": view,"viewer_count": viewer,"valid_viewer_count": valid_viewer,
            "complete_view_count": complete_view,"like_count": int(view*rng.uniform(0.03,0.2)),"comment_count": int(view*rng.uniform(0.005,0.04)),
            "share_count": int(view*rng.uniform(0.003,0.025)),"collect_count": int(view*rng.uniform(0.004,0.03)),
            "engaged_user_count": engaged_user,"profile_visit_count": profile_visit,"follow_count": follow,
            "active_user_count": int(viewer*rng.uniform(0.5,0.95)),"new_user_count": int(viewer*rng.uniform(0.08,0.5)),
            "return_user_count": int(viewer*rng.uniform(0.2,0.6)),"next_day_active_user_count": int(max(1,int(viewer*rng.uniform(0.08,0.5)))*rng.uniform(0.12,0.55)),
            "day7_active_user_count": int(max(1,int(viewer*rng.uniform(0.08,0.5)))*rng.uniform(0.06,0.35)),"avg_watch_duration": round(float(rng.uniform(8.0,74.0)),2)
        })
    df = pd.DataFrame(records)
    output_path = DEMO_DIR / "demo_growth_data.csv"
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output_path
