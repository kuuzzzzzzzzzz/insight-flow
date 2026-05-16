"""Pydantic schemas for Mini AirDA Plus backend API."""
from __future__ import annotations

from typing import Dict, List, Literal, Union

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    question: str = Field(..., min_length=1)
    source: Literal["demo", "csv", "douyin", "bilibili"] = "demo"
    bilibili_input: str | None = None


class MetricItem(BaseModel):
    name: str
    label: str
    formula: str
    meaning: str


class MetricSystem(BaseModel):
    chain: str
    metrics: List[MetricItem]


class AnalyzeResponse(BaseModel):
    question: str
    mode: str
    metrics_used: List[MetricItem]
    metric_system: MetricSystem
    sql: str
    table_columns: List[str]
    table_rows: List[Dict]
    charts: List[Dict] = []
    chart_type: Literal["bar", "line", "pie", "funnel"]
    chart_data: Union[List[Dict], Dict]
    insight: Dict[str, str]
