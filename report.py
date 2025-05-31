import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

FILE_PATH = "input/scan_result.json"
MODIFIED_FILE_PATH = "output/modified.json"
OVERVALL_REPORT_PATH = "output/completeOverviewReport.txt"
GEMINI_MODEL = "gemini-2.0-flash"

#
# def load_json_data(data):
#     with open(data, 'r') as file:
#         data = json.load(file)
#     return json.dumps(data, indent=4)
#


def simplify_instances(json_input_path, json_output_path):
    """
    Takes a JSON file (list of vulnerability dictionaries), replaces each "instances" list
    with a count of instances, and writes the result to a new JSON file.
    """

    with open(json_input_path, "r", encoding="utf-8") as infile:
        # This is a list, not a dict with "reports" key
        data = json.load(infile)

    for vulnerability in data:
        if "instances" in vulnerability:
            count = len(vulnerability["instances"])
            vulnerability["instances"] = f"{count} instance(s) affected"

    with open(json_output_path, "w", encoding="utf-8") as outfile:
        json.dump(data, outfile, indent=4, ensure_ascii=False)
    return data


load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

# Step 2: Configure Gemini
genai.configure(api_key=api_key)

# Step 3: Load your JSON prompt from file
# resdata = load_json_data(FILE_PATH)
modified_data = simplify_instances(FILE_PATH, MODIFIED_FILE_PATH)
# # Step 4: Create a clear and simple prompt
prompt = f"""
You are a cybersecurity analyst specializing in summarizing structured scan data for voice-based reporting.

Your task is to convert a list of vulnerabilities, provided in JSON format, into clear, concise paragraphs. These paragraphs must be easy to transcribe with a text-to-speech engine and free from technical clutter or unnecessary storytelling.

**Guidelines:**
- Use complete sentences.
- Each vulnerability must be summarized in a single paragraph.
- Begin with the vulnerability's name and risk level.
- Briefly explain the issue using the "description".
- If a solution exists, include it clearly.
- Summarize relevant tags, like CWE or OWASP IDs, as part of the explanation.
- Mention how many instances were affected using the instance count.
- Adapt to missing fields gracefully — some sources may lack certain tags or structure.
- Do not output markdown, code blocks, quotes, symbols, or lists — output should be plain readable text only.

**Here is the vulnerability data to summarize:**

{json.dumps(modified_data, indent=2, ensure_ascii=False)}
"""
# # Step 5: Send to Gemini API
model = genai.GenerativeModel(GEMINI_MODEL)
response = model.generate_content(prompt)
#
# # Step 6: Print or save the result
with open(OVERVALL_REPORT_PATH, "w") as f:
    f.write(response.text)
