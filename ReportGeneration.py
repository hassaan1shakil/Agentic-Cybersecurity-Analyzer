# Directory: report_agent/
# File: report_agent.py

import json
from pathlib import Path
from gtts import gTTS
from fpdf import FPDF
from googletrans import Translator


class ReportAgent:
    def __init__(self, input_json_path, output_dir):
        self.input_path = Path(input_json_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.translator = Translator()
        self.report_data = self._load_input()

    def _load_input(self):
        with self.input_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _format_issues(self, issues):
        formatted = []
        for issue in issues:
            formatted.append(
                {
                    "title": issue.get("title", ""),
                    "description": issue.get("description", ""),
                    "severity": issue.get("severity", ""),
                    "location": issue.get("location", ""),
                    "remediation": issue.get("remediation", ""),
                }
            )
        return formatted

    def _translate_to_urdu(self, text):
        try:
            return self.translator.translate(text, dest="ur").text
        except Exception as e:
            print(f"Translation failed: {e}")
            return text  # fallback to original

    def _generate_text_report(self, issues, is_urdu=False):
        lines = []
        for i, issue in enumerate(issues, 1):
            lines.append(f"⚠️ Vulnerability #{i}")
            for key, value in issue.items():
                label = key.capitalize()
                if is_urdu:
                    label = self._translate_to_urdu(label)
                    value = self._translate_to_urdu(value)
                lines.append(f"{label}: {value}")
            lines.append("\n")
        return "\n".join(lines)

    def _generate_pdf(self, text, filename):
        pdf = FPDF()
        pdf.add_page()
        pdf.add_font(
            "ArialUnicode",
            "",
            fname="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            uni=True,
        )
        pdf.set_font("ArialUnicode", size=12)
        for line in text.split("\n"):
            pdf.multi_cell(0, 10, txt=line)
        pdf.output(str(self.output_dir / filename))

    def _generate_tts(self, text, lang, filename):
        tts = gTTS(text=text, lang=lang)
        tts.save(str(self.output_dir / filename))

    def _save_json_summary(self, issues, filename="stage_summary.json"):
        summary_path = self.output_dir / filename
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(issues, f, indent=2, ensure_ascii=False)

    def run(self):
        issues = self._format_issues(self.report_data.get("vulnerabilities", []))

        # English Report
        english_text = self._generate_text_report(issues, is_urdu=False)
        self._generate_pdf(english_text, "report_en.pdf")
        self._generate_tts(english_text, "en", "report_en.mp3")

        # Urdu Report
        urdu_text = self._generate_text_report(issues, is_urdu=True)
        self._generate_pdf(urdu_text, "report_ur.pdf")
        self._generate_tts(urdu_text, "ur", "report_ur.mp3")

        # JSON Summary
        self._save_json_summary(issues)

        print("✔️ Report generation complete!")


# Example usage
if __name__ == "__main__":
    agent = ReportAgent(input_json_path="input/scan_result.json", output_dir="output")
    agent.run()
