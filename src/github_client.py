"""
github_client.py — async wrapper around the GitHub REST API v3

Auth: personal access token passed as "Authorization: token <ghp_...>".
      Needs read:user and public_repo scopes at minimum.
      Without a token, the API rate limit drops to 60 req/hour — effectively unusable.
"""

import os
from datetime import datetime, timedelta, timezone

import httpx

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
API = "https://api.github.com"


def _headers():
    h = {"Accept": "application/vnd.github.v3+json", "X-GitHub-Api-Version": "2022-11-28"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"token {GITHUB_TOKEN}"
    return h


def _rate_limited(resp):
    """Check whether we've hit the GitHub rate limit and surface a helpful error."""
    if resp.headers.get("X-RateLimit-Remaining") == "0":
        reset = resp.headers.get("X-RateLimit-Reset", "")
        return {"error": f"GitHub rate limit hit. Resets at {reset}"}
    return None


async def get_github_user(username):
    """Verify that a GitHub username exists and return basic profile info."""
    if not GITHUB_TOKEN:
        return {"error": "GITHUB_TOKEN not configured"}

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(f"{API}/users/{username}", headers=_headers())
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}

    if resp.status_code == 404:
        return {"error": f"GitHub user '{username}' not found"}
    if resp.status_code == 401:
        return {"error": "GitHub auth failed — check GITHUB_TOKEN"}
    if err := _rate_limited(resp):
        return err
    if resp.status_code != 200:
        return {"error": f"GitHub returned {resp.status_code}"}

    u = resp.json()
    return {
        "login": u["login"],
        "name": u.get("name", ""),
        "public_repos": u.get("public_repos", 0),
        "url": u.get("html_url", ""),
    }


async def get_github_recent_commits(username, days_back=7):
    """Get commits pushed by a user in the last N days.

    Uses the public events API rather than the search API — it's faster and
    doesn't count against the search rate limit. We filter for PushEvents
    and extract individual commits from each event's payload.
    """
    if not GITHUB_TOKEN:
        return {"error": "GITHUB_TOKEN not configured"}

    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(
                f"{API}/users/{username}/events",
                headers=_headers(),
                params={"per_page": 50},
            )
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}

    if resp.status_code == 404:
        return {"error": f"GitHub user '{username}' not found"}
    if resp.status_code == 401:
        return {"error": "GitHub auth failed — check GITHUB_TOKEN"}
    if err := _rate_limited(resp):
        return err
    if resp.status_code != 200:
        return {"error": f"GitHub returned {resp.status_code}"}

    commits = []
    for event in resp.json():
        if event.get("type") != "PushEvent":
            continue
        created_at = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
        if created_at < cutoff:
            continue
        repo = event.get("repo", {}).get("name", "unknown")
        for c in event.get("payload", {}).get("commits", []):
            commits.append({
                "repo": repo,
                "message": c.get("message", "").split("\n")[0],  # first line only
                "sha": c.get("sha", "")[:7],
                "date": created_at.strftime("%Y-%m-%d"),
                "url": f"https://github.com/{repo}/commit/{c.get('sha', '')}",
            })

    if not commits:
        return {"message": f"No commits found for '{username}' in the last {days_back} days", "commits": []}
    return {"total": len(commits), "days_back": days_back, "commits": commits[:20]}


async def get_github_pull_requests(username):
    """Get open pull requests authored by a user across all public repos."""
    if not GITHUB_TOKEN:
        return {"error": "GITHUB_TOKEN not configured"}

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(
                f"{API}/search/issues",
                headers=_headers(),
                params={"q": f"is:pr author:{username} is:open", "sort": "updated", "per_page": 10},
            )
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}

    if resp.status_code == 401:
        return {"error": "GitHub auth failed — check GITHUB_TOKEN"}
    if err := _rate_limited(resp):
        return err
    if resp.status_code != 200:
        return {"error": f"GitHub returned {resp.status_code}"}

    data = resp.json()
    items = data.get("items", [])
    if not items:
        return {"message": f"No open pull requests found for '{username}'", "pull_requests": []}

    return {
        "total_open": data.get("total_count", len(items)),
        "pull_requests": [
            {
                "title": pr["title"],
                "repo": pr["repository_url"].split("/repos/")[-1],
                "state": pr["state"],
                "updated_at": pr.get("updated_at", "")[:10],
                "url": pr["html_url"],
                "draft": pr.get("draft", False),
            }
            for pr in items
        ],
    }


async def get_github_repos(username):
    """Get the most recently active public repos for a user (sorted by last push)."""
    if not GITHUB_TOKEN:
        return {"error": "GITHUB_TOKEN not configured"}

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(
                f"{API}/users/{username}/repos",
                headers=_headers(),
                params={"sort": "pushed", "per_page": 5},
            )
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}

    if resp.status_code == 404:
        return {"error": f"GitHub user '{username}' not found"}
    if resp.status_code == 401:
        return {"error": "GitHub auth failed — check GITHUB_TOKEN"}
    if err := _rate_limited(resp):
        return err
    if resp.status_code != 200:
        return {"error": f"GitHub returned {resp.status_code}"}

    repos = resp.json()
    if not repos:
        return {"message": f"No repositories found for '{username}'", "repos": []}

    return {
        "repos": [
            {
                "name": r["full_name"],
                "description": r.get("description", ""),
                "language": r.get("language", ""),
                "pushed_at": r.get("pushed_at", "")[:10],
                "url": r["html_url"],
                "stars": r.get("stargazers_count", 0),
            }
            for r in repos
        ]
    }
