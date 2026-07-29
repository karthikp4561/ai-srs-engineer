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


DIAGRAM_PROMPT_TEMPLATE = """You are a software architect. Based on this project analysis, generate three UML diagrams using Mermaid.js syntax.

Project Description:
\"\"\"
{description}
\"\"\"

Functional Requirements:
{requirements}

Target Users:
{users}

Generate valid Mermaid.js syntax for:
1. A Use Case diagram (use "graph TD" or "flowchart TD" style showing actors and their actions as a flowchart, since Mermaid has no native use case diagram type)
2. A Class diagram (use "classDiagram" syntax) showing 3-6 key entities/classes with attributes and relationships based on the requirements
3. An Entity Relationship diagram (use "erDiagram" syntax) showing the likely database entities and their relationships

Return ONLY a valid JSON object (no markdown formatting, no code fences, no explanation) with exactly this structure:

{{
  "use_case_diagram": "mermaid syntax as a single string, using \\n for newlines",
  "class_diagram": "mermaid syntax as a single string, using \\n for newlines",
  "er_diagram": "mermaid syntax as a single string, using \\n for newlines"
}}

Important: the mermaid syntax inside each string must be syntactically valid and self-contained.
Respond with ONLY the JSON object, nothing else."""


def generate_diagrams(description: str, functional_requirements: list, target_users: list) -> dict:
    prompt = DIAGRAM_PROMPT_TEMPLATE.format(
        description=description,
        requirements="\n".join(f"- {r}" for r in functional_requirements),
        users=", ".join(target_users),
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a precise software architect that only outputs valid JSON containing Mermaid.js diagram syntax."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )

    raw_text = response.choices[0].message.content.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.MULTILINE).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI returned invalid JSON: {e}\nRaw response: {raw_text[:500]}")