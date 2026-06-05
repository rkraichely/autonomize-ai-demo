"""
Standalone integration test script.
Verifies JIRA and GitHub API connections independently before running the full app.

Usage:
    .venv/bin/python3 test_apis.py
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def test_jira():
    print("\n=== JIRA Integration Test ===")
    from src.jira_client import search_jira_user, get_jira_assigned_issues

    base_url = os.getenv("JIRA_BASE_URL", "")
    email = os.getenv("JIRA_EMAIL", "")
    token = os.getenv("JIRA_API_TOKEN", "")

    if not all([base_url, email, token]) or "..." in [base_url, email, token]:
        print("SKIP — JIRA credentials not configured (set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN)")
        return False

    print(f"  Base URL : {base_url}")
    print(f"  Email    : {email}")
    print(f"  Token    : {'*' * 8}{token[-4:] if len(token) > 4 else '****'}")

    # Test 1: user search
    test_name = input("\n  Enter a JIRA user display name to search: ").strip()
    if not test_name:
        print("  Skipping user search.")
        return True

    print(f"\n  Searching for '{test_name}'...")
    result = await search_jira_user(test_name)

    if "error" in result:
        print(f"  FAIL: {result['error']}")
        return False

    users = result.get("users", [])
    print(f"  PASS: Found {len(users)} user(s)")
    for u in users:
        print(f"    - {u['displayName']} ({u['emailAddress']}) accountId={u['accountId']}")

    if users:
        account_id = users[0]["accountId"]
        print(f"\n  Fetching issues for accountId={account_id}...")
        issues_result = await get_jira_assigned_issues(account_id)

        if "error" in issues_result:
            print(f"  FAIL: {issues_result['error']}")
            return False

        total = issues_result.get("total", 0)
        issues = issues_result.get("issues", [])
        print(f"  PASS: {total} open issue(s)")
        for issue in issues[:3]:
            print(f"    - [{issue['key']}] {issue['summary']} ({issue['status']})")

    return True


async def test_github():
    print("\n=== GitHub Integration Test ===")
    from src.github_client import get_github_user, get_github_recent_commits, get_github_pull_requests

    token = os.getenv("GITHUB_TOKEN", "")
    if not token or "..." in token:
        print("SKIP — GITHUB_TOKEN not configured")
        return False

    print(f"  Token: {'*' * 8}{token[-4:] if len(token) > 4 else '****'}")

    username = input("\n  Enter a GitHub username to test: ").strip()
    if not username:
        print("  Skipping GitHub test.")
        return True

    print(f"\n  Fetching profile for '{username}'...")
    user = await get_github_user(username)
    if "error" in user:
        print(f"  FAIL: {user['error']}")
        return False
    print(f"  PASS: {user['name'] or user['login']} — {user['public_repos']} public repos")

    print(f"\n  Fetching recent commits for '{username}'...")
    commits = await get_github_recent_commits(username, days_back=14)
    if "error" in commits:
        print(f"  FAIL: {commits['error']}")
        return False
    if "message" in commits:
        print(f"  INFO: {commits['message']}")
    else:
        print(f"  PASS: {commits['total']} commit(s) in last 14 days")
        for c in commits.get("commits", [])[:3]:
            print(f"    - [{c['sha']}] {c['message']} ({c['repo']}, {c['date']})")

    print(f"\n  Fetching open PRs for '{username}'...")
    prs = await get_github_pull_requests(username)
    if "error" in prs:
        print(f"  FAIL: {prs['error']}")
        return False
    if "message" in prs:
        print(f"  INFO: {prs['message']}")
    else:
        print(f"  PASS: {prs['total_open']} open PR(s)")
        for pr in prs.get("pull_requests", [])[:3]:
            print(f"    - {pr['title']} ({pr['repo']})")

    return True


async def test_mock():
    print("\n=== Mock Data Test ===")
    os.environ["USE_MOCK_DATA"] = "true"

    # Re-import to pick up mock mode (works if not already imported)
    from src.mock_client import search_jira_user, get_jira_assigned_issues, get_github_recent_commits

    result = await search_jira_user("sarah")
    assert "users" in result, f"Expected users, got: {result}"
    account_id = result["users"][0]["accountId"]

    issues = await get_jira_assigned_issues(account_id)
    assert "issues" in issues, f"Expected issues, got: {issues}"

    commits = await get_github_recent_commits("sarahchen-dev")
    assert "commits" in commits, f"Expected commits, got: {commits}"

    print(f"  PASS: Mock JIRA — {len(issues['issues'])} issues for Sarah Chen")
    print(f"  PASS: Mock GitHub — {commits['total']} commits for sarahchen-dev")
    return True


async def main():
    print("AutonomizeAI — API Integration Tests")
    print("=====================================")

    results = {}
    results["mock"] = await test_mock()

    use_mock = os.getenv("USE_MOCK_DATA", "").lower() in ("1", "true", "yes")
    if not use_mock:
        results["jira"] = await test_jira()
        results["github"] = await test_github()
    else:
        print("\nINFO: USE_MOCK_DATA=true — skipping real API tests")
        print("      Set USE_MOCK_DATA=false in .env to test real JIRA/GitHub connections")

    print("\n=== Results ===")
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {status}  {name}")


if __name__ == "__main__":
    asyncio.run(main())
