from src.agents.base_agent import BaseAgent
from src.chart_generator import generate_chart
class ChartAgent(BaseAgent):
    def __init__(self): super().__init__("chart_agent")
    def run(self, df, question): return generate_chart(df, question)
