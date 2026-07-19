import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

ANALYSIS_PROMPT_TEMPLATE = """You are a senior software business analyst. Analyze the following software project description and extract structured requirements.

Project Description:
\"\"\"
{description}
\"\"\"

Return ONLY a valid JSON object (no markdown formatting, no code fences, no explanation text) with exactly this structure:

{{
  "objectives": ["list of 3-5 clear project objectives"],
  "scope": "a 2-3 sentence description of what the system will and won't cover",
  "target_users": ["list of user roles/types who will use this system"],
  "functional_requirements": ["list of 6-12 specific functional requirements, each a clear actionable statement"],
  "non_functional_requirements": ["list of 4-8 non-functional requirements covering performance, security, usability, etc."],
  "constraints": ["list of 2-4 likely constraints (technical, time, budget, etc.)"],
  "assumptions": ["list of 2-4 reasonable assumptions"]
}}

Respond with ONLY the JSON object, nothing else."""


def analyze_project_description(description: str) -> dict:
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(description=description)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a precise software business analyst that only outputs valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )

    raw_text = response.choices[0].message.content.strip()

    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.MULTILINE).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI returned invalid JSON: {e}\nRaw response: {raw_text[:500]}")