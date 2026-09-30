import requests
from typing import Optional

GITHUB_API = "https://api.github.com"


def validate_repo_access(token: str, owner: str, repo: str) -> bool:
    resp = requests.get(
        f"{GITHUB_API}/repos/{owner}/{repo}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        timeout=10,
    )
    return resp.status_code == 200


def create_issue(token: str, owner: str, repo: str, title: str, body: str, labels: Optional[list] = None) -> dict:
    resp = requests.post(
        f"{GITHUB_API}/repos/{owner}/{repo}/issues",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        json={"title": title, "body": body, "labels": labels or []},
        timeout=10,
    )
    if resp.status_code not in (200, 201):
        raise ValueError(f"GitHub API error ({resp.status_code}): {resp.text[:300]}")
    return resp.json()