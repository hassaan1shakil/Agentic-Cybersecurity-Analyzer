from agents.plan_agent import get_plan_sequence
from agents.scan_agent import run_scan_agent
# from agents.fix_agent import FixAgent
# from agents.explain_agent import ExplainAgent
# from agents.compliance_agent import ComplianceAgent
# from agents.report_agent import ReportAgent
# from agents.narration_agent import NarrationAgent
from app.core.celery_app import celery

# needs a lot of error handling
# send appropriate updates through celery/redis
# the final audio file should be stored in a location accessible by the frontend (or sent through ftp)

@celery.task(name="app.langchain_logic.run_pipeline.run_chain")
def run_chain(data: dict):
    
    plan = get_plan_sequence(data.prompt)
    state = {}  # Storing Intermediate Results
    
    for agent_name in plan:
        if agent_name == "ScanAgent":
            state["scan_results"] = run_scan_agent(data.source, data.scan_type)
            
        elif agent_name == "FixAgent":
            state["fix_results"] = FixAgent.run(state["scan_results"])
            
        elif agent_name == "ExplainAgent":
            state["explanations"] = ExplainAgent.run(state["fix_results"])
            
        elif agent_name == "ComplianceAgent":
            comp_input = {
                "scan_results": state["scan_results"],
                "explanations": state.get("explanations", {})
            }
            state["compliance"] = ComplianceAgent.run(comp_input)
            
        elif agent_name == "ReportAgent":
            report_input = {
                "explanations": state.get("explanations", {}),
                "compliance": state.get("compliance", {})
            }
            rep = ReportAgent.run(report_input)
            state["english_report"] = rep["english_report"]
            state["urdu_report"] = rep["urdu_report"]
            
        elif agent_name == "NarrationAgent":
            state["audio_path"] = NarrationAgent.run(state["urdu_report"])["audio_path"]
            
        else:
            raise ValueError(f"Unknown agent: {agent_name}") 
    
    
    # this needs to return the long summary + audio file for the short summary
    return {"status": "completed", "result": f"Processed: {data}"}