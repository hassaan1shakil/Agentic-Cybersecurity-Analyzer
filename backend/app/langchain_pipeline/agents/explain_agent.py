import os
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain.agents import initialize_agent, Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents.agent_types import AgentType
from langchain.chat_models.base import BaseChatModel

from langchain_pipeline.tools.code_explainer import code_explainer_handler as code_explainer
from langchain_pipeline.tools.web_explainer import web_explainer_handler as web_explainer

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

llm: BaseChatModel = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    google_api_key=GOOGLE_API_KEY 
)

class ExplainInput(BaseModel):
    file_path: str

tools = [
    Tool.from_function(
        func=code_explainer,
        name="code_explainer",
        description="Scans the provided public GitHub repository URL for security issues using Semgrep. Returns a report of the scan or a status message. Use this for scan_types like 'code' or 'static analysis'.",
        args_schema=ExplainInput
        
    ),
    Tool.from_function(
        func=web_explainer,
        name="web_explainer",
        description="Scans the provided website URL for security issues using ZAP. Use this for scan_types like 'web' or 'dynamic analysis'.",
        args_schema=ExplainInput,
    )
]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)
    

def run_explain_agent(scan_results: dict):
    prompt = (
        f"You are responsible for the documnetation of a cybersecurity scan using the tools available to you. Based on the following data received that may contain data from a static code analysis or a website scan or both, your job is to use the relevant tools and format the received data.\n"
        f"The incoming data is in JSON format contianing the file paths to the saved reports for the respective scan. If the file path is empty, it means that the scan assosciated with that was not performed and it should not be explained any further. The file paths should be passed exactly as received including any folder or directories in the path\n"
        
        f"Input Data: {scan_results}\n\n"
        
        f"Available Tools:\n"
        f"1) code_explainer: takes the code_scan_file as input and returns filename where the formatted results are saved .\n"
        f"1) web_explainer: takes the web_scan_file as input and returns filename where the formatted results are saved .\n"
        
        f"Decide which tools to use based on the incoming data.\n\n"
        
        f"Collect the JSON output from all generated tool calls. Return a single JSON dictionary structured as follows:\n"
        "{'code_explain_file': name of the file where code scan explanations are saved, 'web_explain_file': name of the file where web scan explanations are saved}\n\n"
        "If no calls were made for a specific explanation tool in case of empty file path name for that scan, the corresponding key's value should be empty (``). Include the filename received from the tools exactly as received and make sure it is complete and not modified.\n\n"
       
        "Example output: {'code_explain_file': 'code_explain_results_487384684.py', 'web_explain_file': 'web_explain_results_487384684'}\n"
        "Example output: {'code_explain_file': 'code_explain_results_487384684.py', 'web_explain_file': ''}\n\n"
    )

    result = agent.invoke(prompt)
    return result

if __name__ == "__main__":
    
    data = {'code_explain_file': 'scan_reports/code_scan_results_1749639302.json', 'web_explain_file': 'scan_reports/web_scan_results_1749639803.json'}
    final_output = run_explain_agent(data)
    # scan_reports/code_scan_results_1749639302.json
    # scan_reports/web_scan_results_1749639803.json
    # print(final_output)