from typing import TypedDict, Optional

class AgentState(TypedDict):
    db_alert: dict           # original alert from MongoDB
    severity: str            # filled by triage agent
    timeline: list           # filled by log analysis agent
    threat_intel: dict       # filled by threat intel agent
    relevant_docs: list      # filled by RAG agent
    agent_report: str              # filled by report agent
    investigation_status: str              # current stage of investigation