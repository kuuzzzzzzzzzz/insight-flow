from src.agents.base_agent import BaseAgent
from src.data_quality import generate_data_quality_report
class DataQualityAgent(BaseAgent):
    def __init__(self): super().__init__("data_quality_agent")
    def run(self, df): return generate_data_quality_report(df)
