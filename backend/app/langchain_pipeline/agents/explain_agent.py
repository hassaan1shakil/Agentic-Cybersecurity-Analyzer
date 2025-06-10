from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
gemini_model = "gemini-2.0-flash"

def enhance_with_gemini(issues):
    enhanced = []
    for issue in issues:
        file = issue.get("path", "Unknown")
        line = issue.get("start", {}).get("line", "Unknown")
        message = issue.get("extra", {}).get("message", "")
        snippet = issue.get("extra", {}).get("lines", "")

        prompt = (
            "You are a cybersecurity analyst. Analyze and explain the vulnerability "
            "in the following source code. Do not use markdown or bullet points. "
            "Only respond in plain text.\n\n"
            f"File: {file}\n"
            f"Line: {line}\n"
            f"Code Snippet:\n{snippet}\n\n"
            f"Message: {message}\n\n"
            "Explain the vulnerability and how to fix it."
        )

        try:
            response = client.models.generate_content(
                model=gemini_model,
                contents=prompt
            )
            explanation = response.model_dump_json(exclude_none=True, indent=4)
            print(explanation)
            
        except Exception as e:
            explanation = "Model failed to analyze this vulnerability."
            print("[!] Model error:", e)

        issue["explanation"] = explanation
        enhanced.append(issue)

    return enhanced
