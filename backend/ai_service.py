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
        model="openai/gpt-oss-120b",
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
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You are a precise software architect that only outputs valid JSON containing Mermaid.js diagram syntax."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )

    raw_text = response.choices[0].message.content.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.MULTILINE).strip()
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI returned invalid JSON: {e}\nRaw response: {raw_text[:500]}")

    def fix_unlabeled_nodes(code: str) -> str:
        counter = {"n": 0}
        def repl(m):
            counter["n"] += 1
            return f"{m.group(1)}AutoNode{counter['n']}("
        return re.sub(r'(-->\s*)\(', repl, code)

    for key in ("use_case_diagram", "class_diagram", "er_diagram"):
        if key in result:
            result[key] = re.sub(r'\|>', '|', result[key])

    if "use_case_diagram" in result:
        result["use_case_diagram"] = fix_unlabeled_nodes(result["use_case_diagram"])

    return result

API_SPEC_PROMPT_TEMPLATE = """You are a backend API architect. Based on this project's functional requirements, design a REST API specification.

Project Description:
\"\"\"
{description}
\"\"\"

Functional Requirements:
{requirements}

Generate a REST API specification with 5-10 endpoints covering the core functionality. For each endpoint include the HTTP method, path, a short description, an example request body (if applicable), and an example response body.

Return ONLY a valid JSON object (no markdown, no code fences, no explanation) with exactly this structure:

{{
  "endpoints": [
    {{
      "method": "POST",
      "path": "/api/resource",
      "description": "short description of what this endpoint does",
      "request_body": {{"example": "field"}},
      "response_body": {{"example": "field"}}
    }}
  ]
}}

request_body should be null (not an object) for GET and DELETE endpoints without a body.
Respond with ONLY the JSON object, nothing else."""


def generate_api_spec(description: str, functional_requirements: list) -> dict:
    prompt = API_SPEC_PROMPT_TEMPLATE.format(
        description=description,
        requirements="\n".join(f"- {r}" for r in functional_requirements),
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You are a precise backend API architect that only outputs valid JSON."},
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

TECH_STACK_PROMPT_TEMPLATE = """You are a senior software architect. Based on this project, recommend a suitable technology stack.

Project Description:
\"\"\"
{description}
\"\"\"

Non-Functional Requirements:
{nfr}

Recommend technologies across these categories: frontend, backend, database, cloud_deployment, third_party_integrations.
For each recommendation, give the technology name and a brief reason it fits this specific project.

Return ONLY a valid JSON object (no markdown, no code fences, no explanation) with exactly this structure:

{{
  "frontend": {{"technology": "name", "reason": "why it fits"}},
  "backend": {{"technology": "name", "reason": "why it fits"}},
  "database": {{"technology": "name", "reason": "why it fits"}},
  "cloud_deployment": {{"technology": "name", "reason": "why it fits"}},
  "third_party_integrations": [
    {{"technology": "name", "reason": "why it fits"}}
  ]
}}

third_party_integrations should have 2-4 items. Respond with ONLY the JSON object, nothing else."""


def generate_tech_stack(description: str, non_functional_requirements: list) -> dict:
    prompt = TECH_STACK_PROMPT_TEMPLATE.format(
        description=description,
        nfr="\n".join(f"- {r}" for r in non_functional_requirements),
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You are a precise software architect that only outputs valid JSON."},
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

PLANNING_PROMPT_TEMPLATE = """You are a senior project manager. Based on this project, create a development plan.

Project Description:
\"\"\"
{description}
\"\"\"

Functional Requirements:
{requirements}

Constraints:
{constraints}

Create a realistic project plan including:
1. An overall estimated timeline (in weeks) broken into phases
2. 3-5 sprints, each with a name, duration in weeks, and a list of goals for that sprint
3. 3-5 key milestones with a short description
4. 3-5 project risks, each with the risk, its likely impact, and a mitigation strategy

Return ONLY a valid JSON object (no markdown, no code fences, no explanation) with exactly this structure:

{{
  "estimated_duration_weeks": 12,
  "phases": [
    {{"name": "phase name", "duration_weeks": 2, "description": "what happens in this phase"}}
  ],
  "sprints": [
    {{"name": "Sprint 1", "duration_weeks": 2, "goals": ["goal 1", "goal 2"]}}
  ],
  "milestones": [
    {{"name": "milestone name", "description": "what this milestone represents"}}
  ],
  "risks": [
    {{"risk": "description of risk", "impact": "High/Medium/Low", "mitigation": "how to mitigate it"}}
  ]
}}

Respond with ONLY the JSON object, nothing else."""


def generate_project_plan(description: str, functional_requirements: list, constraints: list) -> dict:
    prompt = PLANNING_PROMPT_TEMPLATE.format(
        description=description,
        requirements="\n".join(f"- {r}" for r in functional_requirements),
        constraints="\n".join(f"- {c}" for c in constraints),
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You are a precise project manager that only outputs valid JSON."},
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

    