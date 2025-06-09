from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import json
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    google_api_key=API_KEY,
)


planner_template = PromptTemplate(
    input_variables=["user_prompt"],
    template="""
You are a vulnerability‐report planner for a cybersecurity application. 
Given the following user prompt: "{user_prompt}", decide which sub‐agents to invoke.
Options: ScanAgent, FixAgent, ExplainAgent, ComplianceAgent, ReportAgent, NarrationAgent.

Analyze the user prompt and make the most educated guess about the type depth of the scan required which would define the number of agents used.

Return a JSON array “plan_sequence” listing the agents to run in order.

User “depth” levels:
- “minimal”: only scanning and report
- “cve”: scanning + list CVEs + report
- “fixes”: scanning + CVEs + fixes + explanation + report
- “full”: scanning + CVEs + fixes + explanation + compliance + report + narration

If tthe user prompt is extremely unclear or unrelated to the depth of the report, default to “full”.

Example 1:
user_prompt = “I want a brief report” → 
```json
{{"plan_sequence":["ScanAgent","FixAgent","ExplainAgent","ReportAgent","NarrationAgent"]}}

Example 2:
user_prompt = “I want a very detailed report for the given website/repo” → 
```json
{{"plan_sequence":["ScanAgent","FixAgent","ExplainAgent", "ComplianceAgent", "ReportAgent","NarrationAgent"]}}

Example 3:
user_prompt = “Generate a report only explaining the vulnerabilities in the code for this website/repo” → 
```json
{{"plan_sequence":["ScanAgent","FixAgent","ExplainAgent","ReportAgent","NarrationAgent"]}}
```"""
)

planner_chain = LLMChain(llm=llm, prompt=planner_template)

def get_plan_sequence(user_prompt: str) -> list:
    response = planner_chain.run(user_prompt)
    
    try:
        json_str = response.strip().split("```json")[-1].split("```")[0]
        plan_dict = json.loads(json_str)
        return plan_dict["plan_sequence"]
    except Exception as e:
        print(f"Error parsing plan: {e}")
        return []
    

if __name__ == "__main__":
    prompt = "a quick brown fox jumps over the lazy dog"
    plan = get_plan_sequence(prompt)
    print(f"Plan: ' {plan}")