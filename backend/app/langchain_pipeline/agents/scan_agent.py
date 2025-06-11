import os
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain.agents import initialize_agent, Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents.agent_types import AgentType
from langchain.chat_models.base import BaseChatModel

from langchain_pipeline.tools.code_scanner import code_scanner_handler as code_scanner
from langchain_pipeline.tools.web_scanner import web_scanner_handler as web_scanner

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
        description="Scans the provided public GitHub repository URL for security issues using Semgrep. Returns the filename where the scan results are saved and a status message. Use this for scan_types like 'code' or 'static analysis'.",
        args_schema=ScanInput
        
    ),
    Tool.from_function(
        func=web_scanner,
        name="web_scanner",
        description="Scans the provided website URL for security issues using ZAP. Returns the filename where the scan results are saved and a status message. Use this for scan_types like 'web' or 'dynamic analysis'.",
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
        f"You are a security scan coordinator. Given the `scan_sources` and `scan_types`, determine which sources require scanning by `code_scanner` or `web_scanner`, generate the necessary function calls, and structure the results.\n\n"
        f"Scan Sources: {scan_sources}\n"
        f"Scan Types: {scan_types}\n\n"
        
        f"Tool Definitions and Input Requirements:\n"
        f"- `code_scanner(url)`: Requires a full Git repository URL (e.g., `https://github.com/org/repo.git`). Used if 'code' is in `scan_types` and a source is a Git repo URL.\n"
        f"- `web_scanner(url)`: Requires a full web URL (e.g., `https://example.com` or `https://example.com/path`). Used if 'web' is in `scan_types` and a source is a web URL.\n\n"
        
        f"Process each source. If its format matches the requirement of a tool and that tool's type is in `scan_types`, generate the function call for that source. Ensure that only the URL alone is passed to the function. Do not pass the url like url=\"http://example.com\"\n\n"
        
        f"In case of failure, make at least 3 retries. Check for failure using the status message recieved from the tool's output."
        
        f"Collect the JSON output from all generated tool calls. Return a single JSON dictionary structured as follows:\n"
        "{'code_scan_file': name of the file where code scan results are saved, 'web_scan_file': name of the file where web scan results are saved}\n\n"
        "If no calls were made for a specific scan type (either not requested or no matching sources), the corresponding key's value should be empty (``). Include the filename received from the tools exactly as received and make sure it is complete and not modified.\n\n"
       
        "Example output: {'code_scan_file': 'code_scan_results_487384684.py', 'web_scan_file': 'web_scan_results_487384684'}\n"
        "Example output: {'code_scan_file': 'code_scan_results_487384684.py', 'web_scan_file': ''}\n\n"
    )

    result = agent.invoke(prompt)
    return result

if __name__ == "__main__":
    # Example usage
    scan_sources = ["https://github.com/hassaan1shakil/Agentic-Cybersecurity-Analyzer.git", "https://www.hassaanshakil.com"]
    scan_types = ["code", "web"]
    final_output = run_scan_agent(scan_sources, scan_types)
    # print(final_output)