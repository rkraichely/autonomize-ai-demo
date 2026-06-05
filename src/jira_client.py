"""
jira_client.py — async wrapper around the JIRA REST API v3

Auth: JIRA Cloud uses Basic auth with base64(email:api_token).
      Generate a personal API token at: id.atlassian.com/manage-profile/security/api-tokens
      Note: organization admin keys (admin.atlassian.com) do NOT work here.
"""

import base64
import os

import httpx

JIRA_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN", "")


def _headers():
    """Build the Authorization header for every JIRA request."""
    token = base64.b64encode(f"{JIRA_EMAIL}:{JIRA_TOKEN}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


async def search_jira_user(name):
    """Find a JIRA user by display name or email.

    Returns a list of matching users with their accountId, which is required
    by get_jira_assigned_issues. JIRA doesn't let you query issues by name
    directly — you always need the accountId first.
    """
    if not JIRA_URL or not JIRA_EMAIL or not JIRA_TOKEN:
        return {"error": "JIRA credentials not configured"}

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(
                f"{JIRA_URL}/rest/api/3/user/search",
                headers=_headers(),
                params={"query": name, "maxResults": 5},
            )
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}

    if resp.status_code == 401:
        return {"error": "JIRA auth failed — check JIRA_EMAIL and JIRA_API_TOKEN"}
    if resp.status_code == 404:
        return {"error": "JIRA endpoint not found — check JIRA_BASE_URL"}
    if resp.status_code != 200:
        return {"error": f"JIRA returned {resp.status_code}"}

    users = resp.json()
    if not users:
        return {"error": f"No JIRA user found matching '{name}'"}

    return {
        "users": [
            {
                "accountId": u["accountId"],
                "displayName": u.get("displayName", ""),
                "emailAddress": u.get("emailAddress", ""),
                "active": u.get("active", True),
            }
            for u in users
        ]
    }


async def get_jira_assigned_issues(account_id):
    """Fetch open issues assigned to a user via JQL.

    Excludes Done issues so we only show active work. Results are sorted by
    last updated so the most recently touched tickets appear first.
    """
    if not JIRA_URL or not JIRA_EMAIL or not JIRA_TOKEN:
        return {"error": "JIRA credentials not configured"}

    jql = f'assignee = "{account_id}" AND statusCategory != Done ORDER BY updated DESC'

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(
                # Note: the old /rest/api/3/search endpoint was removed (returns 410).
                # Use /search/jql instead.
                f"{JIRA_URL}/rest/api/3/search/jql",
                headers=_headers(),
                params={
                    "jql": jql,
                    "maxResults": 15,
                    "fields": "summary,status,priority,issuetype,updated,labels",
                },
            )
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}

    if resp.status_code == 401:
        return {"error": "JIRA auth failed"}
    if resp.status_code != 200:
        return {"error": f"JIRA returned {resp.status_code}: {resp.text[:200]}"}

    data = resp.json()
    issues = data.get("issues", [])
    if not issues:
        return {"message": "No open JIRA issues found for this user", "total": 0}

    return {
        "total": data.get("total", len(issues)),
        "issues": [
            {
                "key": issue["key"],
                "summary": issue["fields"]["summary"],
                "status": issue["fields"]["status"]["name"],
                "priority": issue["fields"].get("priority", {}).get("name", "None"),
                "type": issue["fields"]["issuetype"]["name"],
                "updated": issue["fields"].get("updated", ""),
                "labels": issue["fields"].get("labels", []),
                "url": f"{JIRA_URL}/browse/{issue['key']}",
            }
            for issue in issues
        ],
    }
