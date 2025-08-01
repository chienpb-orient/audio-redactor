from google import genai
from dotenv import load_dotenv
import os
import json
load_dotenv()  

client = genai.Client(api_key=os.getenv("GOOGLE_GENERATIVE_AI_API_KEY"))

PROMPT = """
You are a redaction assistant. Your job is to analyze transcript segments with word-level timestamps and detect **sensitive information commonly shared in workplace conversations** that must be redacted. Your output must be a **JSON array of `[start, end]` timestamp pairs**, with no extra metadata, text, or explanations.

---

### ❗️Redaction Criteria

Mark a word or phrase for redaction if it reveals **confidential, personal, or security-relevant data** in the context of work or meetings. This includes:

#### 📧 Personal Identifiers

* Full names of employees or external contacts
* Email addresses
* Phone numbers
* Home or personal addresses
* Personal ID numbers (e.g. national ID, social security numbers)

#### 🔐 Credentials and Security

* API keys, tokens, passwords
* Login credentials
* Authentication methods or recovery answers
* Internal IP addresses, server hostnames
* Database connection strings or SSH keys

#### 💼 Business Confidentiality

* Internal project code names
* Client or customer names (if not public)
* Contract details or deal amounts
* Salary information
* Proprietary metrics, KPIs, or financial performance
* Unreleased product details
* Legal terms, private negotiations

#### 🧠 Contextual Phrases

Redact also based on **contextual cues** like:

* “My password is…”
* “You can email me at…”
* “His salary is…”
* “The API key is…”
* “Her number is…”

If multiple consecutive words form a sensitive phrase (e.g. “my email is [chien@example.com](mailto:chien@example.com)”), return a **single timestamp range** covering the whole span.

Be cautious: **only redact clear, sensitive content**. Do not over-redact generic discussion.

---

### ✅ Output Format

Return only the redaction spans, formatted as:

[
  [start_time_in_seconds, end_time_in_seconds],
  ...
]

* All values are floats (in seconds)
* No additional keys, metadata, or context
* If no redactions are needed, return an empty array `[]`

---

### 🧾 Input Format

Each input contains:

* A `Segment` with the sentence and full time range
* A list of word-level timestamps in format:
  `[start_time -> end_time] word`

---

### 🔒 Constraints

* Do **not** include words, phrases, or explanations
* Only return valid JSON array of float timestamp ranges
* Maintain **strict minimal output**

---

Let me know if you want a separate variant that also handles **PII in customer service transcripts** or **HIPAA-style health information**.

"""

def detect_sensitive_content(transcript_content):
    """
    Analyze transcript content and return timestamp ranges for sensitive content.
    
    Args:
        transcript_content (str): The transcript content to analyze
        
    Returns:
        list: List of [start, end] timestamp pairs in seconds
    """
    try:
        FINAL_PROMPT = PROMPT + "\n\nHere is the transcript: " + transcript_content
        
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=FINAL_PROMPT
        )
        
        # Parse the JSON response
        response_text = response.text.strip()
        
        # Handle cases where response might have markdown formatting
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "").strip()
            
        # Parse JSON
        timestamp_ranges = json.loads(response_text)
        
        return timestamp_ranges
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Response was: {response.text}")
        return []
    except Exception as e:
        print(f"Error detecting sensitive content: {e}")
        return []

def detect_sensitive_content_from_file(transcript_file_path):
    """
    Analyze transcript file and return timestamp ranges for sensitive content.
    
    Args:
        transcript_file_path (str): Path to the transcript file
        
    Returns:
        list: List of [start, end] timestamp pairs in seconds
    """
    try:
        with open(transcript_file_path, "r", encoding="utf-8") as file:
            transcript = file.read()
        
        return detect_sensitive_content(transcript)
        
    except FileNotFoundError:
        print(f"Error: Transcript file not found: {transcript_file_path}")
        return []
    except Exception as e:
        print(f"Error reading transcript file: {e}")
        return []

# For backwards compatibility - if run as script
if __name__ == "__main__":
    content = input("Enter the path to transcript file: ")
    result = detect_sensitive_content_from_file(content)
    print(json.dumps(result, indent=2))