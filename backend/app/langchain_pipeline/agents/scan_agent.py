import os
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain.agents import initialize_agent, Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents.agent_types import AgentType
from langchain.chat_models.base import BaseChatModel

from langchain_pipeline.tools.code_scanner import code_scanner
from langchain_pipeline.tools.web_scanner import web_scanner

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

llm: BaseChatModel = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    google_api_key=GOOGLE_API_KEY 
)

class ScanInput(BaseModel):
    url: str

tools = [
    Tool.from_function(
        func=code_scanner,
        name="code_scanner",
        description="Scans the provided public GitHub repository URL for security issues using Semgrep. Returns a report of the scan or a status message. Use this for scan_types like 'code' or 'static analysis'.",
        args_schema=ScanInput
        
    ),
    Tool.from_function(
        func=web_scanner,
        name="web_scanner",
        description="Scans the provided website URL for security issues using ZAP. Use this for scan_types like 'web' or 'dynamic analysis'.",
        args_schema=ScanInput,
    )
]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

def run_scan_agent(scan_sources: list, scan_types: list):
    prompt = (
        f"You are a security scan coordinator. Based on the following scan_sources and scan_types, "
        f"decide which tools to use and perform the scans. You may use both the tools if needed based on the sources.\n\n"
        f"Scan Sources: {scan_sources}\n"
        f"Scan Types: {scan_types}\n\n"
        f"Take special care in passing the scan sources to the tools to avoid typos and mistakes. Only pass the actual website/domain to the function.\n"
        f"code_scanner expects an input of type https://github.com/some/path.git"
        f"web_scanner expects an input of type https://some-website.com"
        f"Both the tools return data in json format. Return the same data without modification."
    )

    result = agent.invoke(prompt)
    return result

if __name__ == "__main__":
    # Example usage
    scan_sources = ["https://github.com/hassaan1shakil/Agentic-Cybersecurity-Analyzer.git", "https://www.hassaanshakil.com"]
    scan_types = ["code", "web"]
    final_output = run_scan_agent(scan_sources, scan_types)
    # print(final_output)