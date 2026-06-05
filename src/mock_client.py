from datetime import datetime, timedelta, timezone

today = datetime.now(timezone.utc)


# All demo data lives here — one entry per person
# TODO: move this to a config file if we add more team members
TEAM = {
    "sarah": {
        "jira_id": "acct-001",
        "jira_name": "Sarah Chen",
        "jira_email": "sarah.chen@company.com",
        "github": "sarahchen-dev",
        "github_repos": 18,
        "issues": [
            {"key": "PLAT-412", "summary": "Redesign onboarding flow for mobile users", "status": "In Progress", "priority": "High", "type": "Story", "updated": "2026-05-27", "labels": ["mobile", "ux"], "url": "https://company.atlassian.net/browse/PLAT-412"},
            {"key": "PLAT-398", "summary": "Fix session timeout bug on Safari", "status": "In Review", "priority": "High", "type": "Bug", "updated": "2026-05-26", "labels": ["safari", "auth"], "url": "https://company.atlassian.net/browse/PLAT-398"},
            {"key": "PLAT-375", "summary": "Add dark mode toggle to settings page", "status": "In Progress", "priority": "Medium", "type": "Feature", "updated": "2026-05-24", "labels": ["ui", "settings"], "url": "https://company.atlassian.net/browse/PLAT-375"},
        ],
        "commits": [
            {"repo": "company/frontend", "message": "feat: add dark mode toggle component", "sha": "a3f91bc", "date": (today - timedelta(days=1)).strftime("%Y-%m-%d"), "url": "https://github.com/company/frontend/commit/a3f91bc"},
            {"repo": "company/frontend", "message": "fix: Safari session expiry handling", "sha": "b7d42ef", "date": (today - timedelta(days=2)).strftime("%Y-%m-%d"), "url": "https://github.com/company/frontend/commit/b7d42ef"},
            {"repo": "company/frontend", "message": "chore: update onboarding step animations", "sha": "c1e83da", "date": (today - timedelta(days=3)).strftime("%Y-%m-%d"), "url": "https://github.com/company/frontend/commit/c1e83da"},
            {"repo": "company/design-system", "message": "docs: add dark mode usage examples", "sha": "d9a21fb", "date": (today - timedelta(days=4)).strftime("%Y-%m-%d"), "url": "https://github.com/company/design-system/commit/d9a21fb"},
        ],
        "prs": [
            {"title": "feat: mobile onboarding redesign (step 1-3)", "repo": "company/frontend", "state": "open", "updated_at": "2026-05-27", "url": "https://github.com/company/frontend/pull/341", "draft": False},
            {"title": "fix: Safari session timeout — use sessionStorage fallback", "repo": "company/frontend", "state": "open", "updated_at": "2026-05-26", "url": "https://github.com/company/frontend/pull/338", "draft": False},
        ],
        "repos": [
            {"name": "company/frontend", "description": "Main React web app", "language": "TypeScript", "pushed_at": "2026-05-27", "url": "https://github.com/company/frontend", "stars": 14},
            {"name": "company/design-system", "description": "Shared component library", "language": "TypeScript", "pushed_at": "2026-05-24", "url": "https://github.com/company/design-system", "stars": 9},
        ],
    },
    "mike": {
        "jira_id": "acct-002",
        "jira_name": "Mike Rodriguez",
        "jira_email": "mike.rodriguez@company.com",
        "github": "mikerodriguez",
        "github_repos": 31,
        "issues": [
            {"key": "API-210", "summary": "Migrate payments service to new gateway", "status": "In Progress", "priority": "Critical", "type": "Epic", "updated": "2026-05-27", "labels": ["payments", "migration"], "url": "https://company.atlassian.net/browse/API-210"},
            {"key": "API-225", "summary": "Rate limiting middleware for public endpoints", "status": "To Do", "priority": "High", "type": "Story", "updated": "2026-05-25", "labels": ["security", "api"], "url": "https://company.atlassian.net/browse/API-225"},
            {"key": "API-198", "summary": "Write integration tests for checkout flow", "status": "In Progress", "priority": "Medium", "type": "Task", "updated": "2026-05-23", "labels": ["testing"], "url": "https://company.atlassian.net/browse/API-198"},
        ],
        "commits": [
            {"repo": "company/api", "message": "feat: integrate Stripe v3 payment gateway", "sha": "e4c17ad", "date": (today - timedelta(days=1)).strftime("%Y-%m-%d"), "url": "https://github.com/company/api/commit/e4c17ad"},
            {"repo": "company/api", "message": "feat: add rate limiting middleware", "sha": "f2b93ce", "date": (today - timedelta(days=2)).strftime("%Y-%m-%d"), "url": "https://github.com/company/api/commit/f2b93ce"},
            {"repo": "company/api", "message": "test: checkout flow integration tests", "sha": "g8a45df", "date": (today - timedelta(days=2)).strftime("%Y-%m-%d"), "url": "https://github.com/company/api/commit/g8a45df"},
            {"repo": "company/api", "message": "refactor: extract payment service interface", "sha": "h1d72bc", "date": (today - timedelta(days=5)).strftime("%Y-%m-%d"), "url": "https://github.com/company/api/commit/h1d72bc"},
        ],
        "prs": [
            {"title": "feat: Stripe v3 gateway migration", "repo": "company/api", "state": "open", "updated_at": "2026-05-27", "url": "https://github.com/company/api/pull/219", "draft": False},
            {"title": "feat: rate limiting middleware", "repo": "company/api", "state": "open", "updated_at": "2026-05-25", "url": "https://github.com/company/api/pull/215", "draft": True},
        ],
        "repos": [
            {"name": "company/api", "description": "Core backend API service", "language": "Python", "pushed_at": "2026-05-27", "url": "https://github.com/company/api", "stars": 21},
        ],
    },
    "lisa": {
        "jira_id": "acct-003",
        "jira_name": "Lisa Park",
        "jira_email": "lisa.park@company.com",
        "github": "lisapark",
        "github_repos": 12,
        "issues": [
            {"key": "DATA-88", "summary": "Build real-time dashboard for conversion metrics", "status": "In Progress", "priority": "High", "type": "Story", "updated": "2026-05-27", "labels": ["analytics", "dashboard"], "url": "https://company.atlassian.net/browse/DATA-88"},
            {"key": "DATA-91", "summary": "Investigate spike in error rate on data pipeline", "status": "In Review", "priority": "Critical", "type": "Bug", "updated": "2026-05-26", "labels": ["pipeline", "reliability"], "url": "https://company.atlassian.net/browse/DATA-91"},
        ],
        "commits": [
            {"repo": "company/data-pipeline", "message": "fix: resolve null pointer in aggregation step", "sha": "i9f34ea", "date": today.strftime("%Y-%m-%d"), "url": "https://github.com/company/data-pipeline/commit/i9f34ea"},
            {"repo": "company/analytics-dashboard", "message": "feat: real-time conversion funnel widget", "sha": "j3c81db", "date": (today - timedelta(days=1)).strftime("%Y-%m-%d"), "url": "https://github.com/company/analytics-dashboard/commit/j3c81db"},
            {"repo": "company/analytics-dashboard", "message": "feat: add time-range selector to dashboard", "sha": "k7e52fc", "date": (today - timedelta(days=3)).strftime("%Y-%m-%d"), "url": "https://github.com/company/analytics-dashboard/commit/k7e52fc"},
        ],
        "prs": [
            {"title": "feat: real-time conversion funnel dashboard", "repo": "company/analytics-dashboard", "state": "open", "updated_at": "2026-05-27", "url": "https://github.com/company/analytics-dashboard/pull/88", "draft": False},
        ],
        "repos": [
            {"name": "company/analytics-dashboard", "description": "Internal metrics dashboard", "language": "Python", "pushed_at": "2026-05-27", "url": "https://github.com/company/analytics-dashboard", "stars": 5},
            {"name": "company/data-pipeline", "description": "ETL pipeline for analytics", "language": "Python", "pushed_at": "2026-05-27", "url": "https://github.com/company/data-pipeline", "stars": 3},
        ],
    },
    "john": {
        "jira_id": "acct-004",
        "jira_name": "John Smith",
        "jira_email": "john.smith@company.com",
        "github": "johnsmith99",
        "github_repos": 7,
        "issues": [
            {"key": "INFRA-55", "summary": "Set up staging environment for EU region", "status": "To Do", "priority": "High", "type": "Task", "updated": "2026-05-27", "labels": ["infra", "eu"], "url": "https://company.atlassian.net/browse/INFRA-55"},
            {"key": "INFRA-49", "summary": "Upgrade Kubernetes cluster to 1.29", "status": "In Progress", "priority": "Medium", "type": "Task", "updated": "2026-05-22", "labels": ["k8s", "upgrade"], "url": "https://company.atlassian.net/browse/INFRA-49"},
        ],
        "commits": [
            {"repo": "company/infra", "message": "chore: upgrade Kubernetes manifests to 1.29 API", "sha": "l5b29ad", "date": (today - timedelta(days=2)).strftime("%Y-%m-%d"), "url": "https://github.com/company/infra/commit/l5b29ad"},
            {"repo": "company/infra", "message": "feat: add EU region terraform module", "sha": "m2a67ef", "date": (today - timedelta(days=4)).strftime("%Y-%m-%d"), "url": "https://github.com/company/infra/commit/m2a67ef"},
        ],
        "prs": [
            {"title": "chore: k8s 1.29 upgrade + deprecation fixes", "repo": "company/infra", "state": "open", "updated_at": "2026-05-26", "url": "https://github.com/company/infra/pull/72", "draft": False},
        ],
        "repos": [
            {"name": "company/infra", "description": "Infrastructure as code (Terraform + Helm)", "language": "HCL", "pushed_at": "2026-05-26", "url": "https://github.com/company/infra", "stars": 6},
        ],
    },
}

# common name variations
ALIASES = {
    "sarah chen": "sarah",
    "mike rodriguez": "mike",
    "michael": "mike",
    "lisa park": "lisa",
    "john smith": "john",
}


def _find(name):
    key = name.lower().strip()
    key = ALIASES.get(key, key)
    return TEAM.get(key)


def _find_by_github(username):
    for person in TEAM.values():
        if person["github"].lower() == username.lower():
            return person
    return None


async def search_jira_user(name):
    person = _find(name)
    if not person:
        return {"error": f"No JIRA user found matching '{name}'. Try: Sarah, Mike, Lisa, or John."}
    return {"users": [{"accountId": person["jira_id"], "displayName": person["jira_name"], "emailAddress": person["jira_email"], "active": True}]}


async def get_jira_assigned_issues(account_id):
    for person in TEAM.values():
        if person["jira_id"] == account_id:
            return {"total": len(person["issues"]), "issues": person["issues"]}
    return {"message": "No open JIRA issues found for this user", "total": 0}


async def get_github_user(username):
    person = _find_by_github(username)
    if not person:
        return {"error": f"GitHub user '{username}' not found. Try: sarahchen-dev, mikerodriguez, lisapark, or johnsmith99."}
    return {"login": person["github"], "name": person["jira_name"], "public_repos": person["github_repos"], "url": f"https://github.com/{person['github']}"}


async def get_github_recent_commits(username, days_back=7):
    person = _find_by_github(username)
    if not person:
        return {"error": f"GitHub user '{username}' not found"}
    commits = person["commits"]
    if not commits:
        return {"message": f"No commits found for '{username}' in the last {days_back} days", "commits": []}
    return {"total": len(commits), "days_back": days_back, "commits": commits}


async def get_github_pull_requests(username):
    person = _find_by_github(username)
    if not person:
        return {"error": f"GitHub user '{username}' not found"}
    prs = person["prs"]
    if not prs:
        return {"message": f"No open pull requests found for '{username}'", "pull_requests": []}
    return {"total_open": len(prs), "pull_requests": prs}


async def get_github_repos(username):
    person = _find_by_github(username)
    if not person:
        return {"error": f"GitHub user '{username}' not found"}
    return {"repos": person["repos"]}
