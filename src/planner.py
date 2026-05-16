def classify_task(question: str) -> str:
    if "质量" in question or "缺失" in question:
        return "data_quality"
    if "解释" in question or "指标" in question:
        return "metric_explanation"
    if "漏斗" in question or "流失" in question:
        return "growth_funnel"
    if "报告" in question:
        return "report_generation"
    if "图" in question or "趋势" in question:
        return "chart_analysis"
    return "sql_query"
