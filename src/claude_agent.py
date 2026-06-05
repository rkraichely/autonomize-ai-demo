"""
claude_agent.py — the core of the app.

Instead of a custom query parser + response formatter, Claude acts as the
orchestrator: it reads the user's question, decides which JIRA/GitHub tools
to call, runs them, and writes the final response. This eliminates two entire
modules that a traditional approach would need.
"""

import asyncio
import json
import os

import anthropic

# Swap both API clients for static demo data when USE_MOCK_DATA=true.
# Useful for demos without live JIRA/GitHub credentials.
USE_MOCK = os.getenv("USE_MOCK_DATA", "").lower() in ("1", "true", "yes")

if USE_MOCK:
    from . import mock_client as jira_client
    from . import mock_client as github_client
else:
    from . import jira_client, github_client

client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Configurable via .env — swap to claude-sonnet-4-6 for richer responses
MODEL = os.getenv("MODEL", "claude-haiku-4-5")

# Safety valve: stop the tool-call loop if Claude gets stuck.
# Bump down to 5 if you're seeing runaway iterations during a demo.
MAX_ITERATIONS = 10

# Map JIRA display names to GitHub usernames for people whose handle
# differs from their name. In production this would come from a team
# directory or identity provider (Okta, Workday, etc.).
GITHUB_USERNAMES = {
    "Ryan Kraichely": "rkraichely",
}

# --- System prompt construction ---

# Tell Claude which demo team members exist when running in mock mode
mock_note = ""
if USE_MOCK:
    mock_note = (
        "\n\nNote: running with demo data. Available team members: "
        "Sarah Chen (GitHub: sarahchen-dev), Mike Rodriguez (GitHub: mikerodriguez), "
        "Lisa Park (GitHub: lisapark), John Smith (GitHub: johnsmith99)."
    )

# Inject the name→handle map so Claude doesn't have to guess GitHub usernames
github_username_note = ""
if GITHUB_USERNAMES:
    lines = "\n".join(f"  - {name} → {handle}" for name, handle in GITHUB_USERNAMES.items())
    github_username_note = f"\n\nKnown GitHub usernames (use these instead of guessing from the person's name):\n{lines}"

SYSTEM_PROMPT = f"""You are a team activity assistant with access to JIRA and GitHub.

When someone asks what a team member is working on:
1. Search JIRA for the person by name to get their accountId
2. Fetch their assigned JIRA issues using that accountId
3. Look up their GitHub activity (commits, PRs, repos) — use the known GitHub username if listed below, otherwise make a reasonable guess from their name
4. Combine everything into a clear summary

Include ticket keys, PR titles, and repo names. If someone has no activity in one system just say so briefly.
If you can't find the user at all, say so and suggest they double-check the name.

Response style:
- No emojis of any kind
- No markdown tables
- Always use "- " bullet points for any list of items (JIRA tickets, PRs, commits, repos) — never write list items as bare paragraphs separated by blank lines
- Group JIRA items under a "JIRA:" line and GitHub items under a "GitHub:" line, each followed by bulleted items
- Write like a developer giving a quick Slack update, not a formal report
- Keep it concise and direct{github_username_note}{mock_note}"""

# --- Tool definitions ---
# These are sent to Claude on every request. Claude decides which ones to call
# and in what order — we never route the question through a parser ourselves.
TOOLS = [
    {
        "name": "search_jira_user",
        "description": "Search for a JIRA user by display name or email. Returns their accountId which is needed to fetch issues.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Display name or email to search for"}
            },
            "required": ["name"],
        },
    },
    {
        "name": "get_jira_assigned_issues",
        "description": "Get open JIRA issues assigned to a user. Requires their accountId from search_jira_user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "JIRA accountId from search_jira_user"}
            },
            "required": ["account_id"],
        },
    },
    {
        "name": "get_github_user",
        "description": "Check if a GitHub username exists and get their profile.",
        "input_schema": {
            "type": "object",
            "properties": {
                "username": {"type": "string", "description": "GitHub username to look up"}
            },
            "required": ["username"],
        },
    },
    {
        "name": "get_github_recent_commits",
        "description": "Get recent commits by a GitHub user. Returns commit messages and repos from the past N days.",
        "input_schema": {
            "type": "object",
            "properties": {
                "username": {"type": "string", "description": "GitHub username"},
                "days_back": {"type": "integer", "description": "How many days back to look (default 7)", "default": 7},
            },
            "required": ["username"],
        },
    },
    {
        "name": "get_github_pull_requests",
        "description": "Get open pull requests authored by a GitHub user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "username": {"type": "string", "description": "GitHub username"}
            },
            "required": ["username"],
        },
    },
    {
        "name": "get_github_repos",
        "description": "Get recently active repos for a GitHub user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "username": {"type": "string", "description": "GitHub username"}
            },
            "required": ["username"],
        },
    },
]

# --- Activity feed labels ---
# These drive the live "Searching JIRA..." UI shown while Claude works.
# Labels are generated from tool arguments so they're specific (e.g. the actual name searched).
_TOOL_START = {
    "search_jira_user":         lambda a: f'Searching JIRA for "{a["name"]}"',
    "get_jira_assigned_issues": lambda a: "Fetching assigned issues",
    "get_github_user":          lambda a: f'Looking up GitHub user "{a["username"]}"',
    "get_github_recent_commits": lambda a: "Fetching recent commits",
    "get_github_pull_requests": lambda a: "Fetching open pull requests",
    "get_github_repos":         lambda a: "Fetching active repositories",
}


def _done_label(name, result):
    """Translate a tool result into a short completion label for the activity feed."""
    if "error" in result:
        return result["error"][:80]
    if name == "search_jira_user":
        users = result.get("users", [])
        return f'Found {users[0]["displayName"]}' if users else "User not found"
    if name == "get_jira_assigned_issues":
        n = result.get("total", 0)
        return f'{n} open ticket{"s" if n != 1 else ""}' if n else "No open tickets"
    if name == "get_github_user":
        return "Profile found"
    if name == "get_github_recent_commits":
        n = len(result.get("commits", []))
        return f'{n} commit{"s" if n != 1 else ""} found' if n else "No recent commits"
    if name == "get_github_pull_requests":
        n = len(result.get("pull_requests", []))
        return f'{n} open PR{"s" if n != 1 else ""}' if n else "No open PRs"
    if name == "get_github_repos":
        n = len(result.get("repos", []))
        return f'{n} repo{"s" if n != 1 else ""} found'
    return "Done"


async def _call_tool(name, args):
    """Execute a single tool call and return (json_string, is_error).

    Returning is_error=True signals Claude that the tool failed so it can
    explain the problem rather than silently using bad data.
    """
    print(f"[tool] {name}({args})")
    try:
        if name == "search_jira_user":
            result = await jira_client.search_jira_user(args["name"])
        elif name == "get_jira_assigned_issues":
            result = await jira_client.get_jira_assigned_issues(args["account_id"])
        elif name == "get_github_user":
            result = await github_client.get_github_user(args["username"])
        elif name == "get_github_recent_commits":
            result = await github_client.get_github_recent_commits(args["username"], args.get("days_back", 7))
        elif name == "get_github_pull_requests":
            result = await github_client.get_github_pull_requests(args["username"])
        elif name == "get_github_repos":
            result = await github_client.get_github_repos(args["username"])
        else:
            result = {"error": f"unknown tool: {name}"}

        out = json.dumps(result, default=str)
        print(f"[tool] {name} → {out[:150]}")
        return out, "error" in result

    except Exception as e:
        out = json.dumps({"error": str(e)})
        print(f"[tool] {name} error: {e}")
        return out, True


async def run_agent(message, history):
    """Non-streaming agent loop. Returns the final response as a plain string.

    Used by the /api/chat endpoint (kept for backwards compatibility).
    """
    # Cap history to avoid token costs growing across long conversations
    msgs = history[-6:] + [{"role": "user", "content": message}]

    # cache_control: ephemeral pins the system prompt in Anthropic's prompt cache.
    # On repeated calls the cached portion is reused, which cuts latency and cost.
    system = [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}]

    for _ in range(MAX_ITERATIONS):
        resp = await client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system,
            tools=TOOLS,
            messages=msgs,
        )

        # Claude finished — return whatever text it produced
        if resp.stop_reason == "end_turn":
            for block in resp.content:
                if hasattr(block, "text"):
                    return block.text
            return "Couldn't generate a response."

        # Claude wants to call one or more tools — execute them and loop back
        if resp.stop_reason == "tool_use":
            tool_blocks = [b for b in resp.content if b.type == "tool_use"]
            msgs.append({"role": "assistant", "content": resp.content})

            # Run all requested tool calls concurrently to minimise wait time
            results = await asyncio.gather(*[_call_tool(b.name, b.input) for b in tool_blocks])

            msgs.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": b.id,
                        "content": out,
                        "is_error": is_err,
                    }
                    for b, (out, is_err) in zip(tool_blocks, results)
                ],
            })
        else:
            return f"Unexpected stop reason: {resp.stop_reason}"

    return "Hit the max number of steps — try rephrasing your question."


def _extract_links(tool_name, result):
    """Pull JIRA ticket and GitHub PR URLs out of a tool result.

    These are sent to the frontend as a 'links' SSE event so the UI can
    render clickable source buttons — separate from the prose response so
    they're always accurate regardless of how Claude phrases the answer.
    """
    links = []
    if tool_name == "get_jira_assigned_issues":
        for issue in result.get("issues", []):
            if issue.get("url") and issue.get("key"):
                links.append({"label": issue["key"], "url": issue["url"], "kind": "jira"})
    elif tool_name == "get_github_pull_requests":
        for pr in result.get("pull_requests", []):
            if pr.get("url"):
                # Extract the PR number from the URL tail (e.g. .../pull/42 → "PR #42")
                num = pr["url"].rstrip("/").split("/")[-1]
                links.append({"label": f"PR #{num}", "url": pr["url"], "kind": "github"})
    return links


async def run_agent_stream(message, history):
    """Streaming agent loop — yields SSE-formatted strings.

    Event types emitted:
      tool_start  — a tool call is about to run (shows spinner in UI)
      tool_done   — tool call finished (spinner → checkmark)
      links       — clickable JIRA/GitHub URLs collected from tool results
      response    — the final prose answer from Claude
      error       — something went wrong
    """

    def event(data):
        # SSE format: each event is "data: <json>\n\n"
        return f"data: {json.dumps(data)}\n\n"

    msgs = history[-6:] + [{"role": "user", "content": message}]
    system = [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}]
    collected_links = []  # accumulate across all tool rounds

    for _ in range(MAX_ITERATIONS):
        resp = await client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system,
            tools=TOOLS,
            messages=msgs,
        )

        if resp.stop_reason == "end_turn":
            text = next((b.text for b in resp.content if hasattr(b, "text")), "Couldn't generate a response.")
            # Send links before the response so the frontend can attach them to the bubble
            if collected_links:
                yield event({"type": "links", "items": collected_links})
            yield event({"type": "response", "text": text})
            return

        if resp.stop_reason == "tool_use":
            tool_blocks = [b for b in resp.content if b.type == "tool_use"]
            msgs.append({"role": "assistant", "content": resp.content})

            # Emit start events for all tools about to fire — they may run concurrently
            for b in tool_blocks:
                label = _TOOL_START.get(b.name, lambda a: b.name)(b.input)
                yield event({"type": "tool_start", "id": b.id, "label": label})

            # Run all tool calls at the same time rather than sequentially
            results = await asyncio.gather(*[_call_tool(b.name, b.input) for b in tool_blocks])

            tool_results = []
            for b, (out, is_err) in zip(tool_blocks, results):
                result_dict = json.loads(out)
                done = _done_label(b.name, result_dict)
                yield event({"type": "tool_done", "id": b.id, "label": done, "is_error": is_err})
                collected_links.extend(_extract_links(b.name, result_dict))
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": b.id,
                    "content": out,
                    "is_error": is_err,
                })

            msgs.append({"role": "user", "content": tool_results})
        else:
            yield event({"type": "error", "text": f"Unexpected stop reason: {resp.stop_reason}"})
            return

    yield event({"type": "error", "text": "Hit the max number of steps — try rephrasing your question."})
