from datetime import datetime
import matplotlib.pyplot as plt
from src.config import CHARTS_DIR
plt.rcParams["font.sans-serif"]=["Microsoft YaHei","SimHei","Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"]=False

def _detect_chart_type(df, question=""):
    if "漏斗" in question or "流失" in question: return "funnel"
    numeric=df.select_dtypes(include="number").columns.tolist(); non=[c for c in df.columns if c not in numeric]
    if len(numeric)>=2: return "scatter"
    if len(numeric)==1 and len(non)>=1:
        if "趋势" in question or "7天" in question or "date" in " ".join(df.columns).lower(): return "line"
        if len(df)<=6: return "pie"
        return "bar"
    return "bar"

def generate_chart(df, question=""):
    if df.empty: return None
    t=_detect_chart_type(df, question)
    out=CHARTS_DIR / f"chart_{t}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.figure(figsize=(10,6)); numeric=df.select_dtypes(include="number").columns.tolist(); non=[c for c in df.columns if c not in numeric]
    if t=="line" and numeric:
        x=non[0] if non else df.index; plt.plot(df[x], df[numeric[0]], marker="o"); plt.xticks(rotation=30); plt.title("趋势分析")
    elif t=="pie" and numeric and non:
        plt.pie(df[numeric[0]], labels=df[non[0]], autopct="%1.1f%%"); plt.title("占比分析")
    elif t=="scatter" and len(numeric)>=2:
        plt.scatter(df[numeric[0]], df[numeric[1]], alpha=0.7); plt.xlabel(numeric[0]); plt.ylabel(numeric[1]); plt.title("相关性分析")
    elif t=="funnel":
        steps=["impression_count","view_count","valid_viewer_count","engaged_user_count","profile_visit_count","follow_count"]
        exist=[s for s in steps if s in df.columns]
        if not exist: plt.text(0.3,0.5,"漏斗图所需字段不存在")
        else:
            values=[float(df[s].sum()) for s in exist]; y=list(range(len(exist)))[::-1]
            for i,(step,val) in enumerate(zip(exist,values)): plt.barh(y[i],val)
            plt.yticks(y,exist); plt.title("增长漏斗")
    else:
        if numeric:
            x=non[0] if non else df.index; plt.bar(df[x], df[numeric[0]]); plt.xticks(rotation=30); plt.title("对比分析")
        else: plt.text(0.3,0.5,"无可视化数值字段")
    plt.tight_layout(); plt.savefig(out, dpi=150); plt.close(); return out
