# AutonomizeAI — Team Activity Chatbot

A conversational AI agent that answers **"What is [member] working on?"** by querying JIRA and GitHub in real time, powered by the Anthropic Claude SDK with tool use. Currently running on `claude-haiku-4-5` for fast responses.

## How It Works

User questions are sent to Claude (`claude-sonnet-4-6`). Claude decides which tools to call — JIRA user search, JIRA issue fetch, GitHub commits, PRs, or repos — runs them concurrently, and synthesizes a natural-language response. No custom query parser needed.

## Setup

### 1. Clone & install dependencies

```bash
cd "AutonomizeAI Demo"
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (always required) |
| `USE_MOCK_DATA` | Set `true` to use demo data without real JIRA/GitHub accounts |
| `MODEL` | Claude model to use (default: `claude-haiku-4-5` for speed, swap to `claude-sonnet-4-6` for richer responses) |
| `JIRA_BASE_URL` | Your Atlassian base URL, e.g. `https://yourorg.atlassian.net` |
| `JIRA_EMAIL` | Email address associated with your JIRA API token |
| `JIRA_API_TOKEN` | JIRA API token (generate at id.atlassian.com/manage-profile/security) |
| `GITHUB_TOKEN` | GitHub personal access token (needs `read:user`, `repo` scopes) |

### 2a. Demo mode (no JIRA/GitHub account needed)

Set `USE_MOCK_DATA=true` in `.env` to run with built-in demo data. Only `ANTHROPIC_API_KEY` is required.

Demo team members available:
| Name | JIRA | GitHub |
|---|---|---|
| Sarah Chen | search "Sarah" | sarahchen-dev |
| Mike Rodriguez | search "Mike" | mikerodriguez |
| Lisa Park | search "Lisa" | lisapark |
| John Smith | search "John" | johnsmith99 |

### 3. (Optional) Test API connections independently

```bash
.venv/bin/python3 test_apis.py
```

Verifies JIRA and GitHub credentials before running the full app.

### 4. Run the server

```bash
.venv/bin/uvicorn src.main:app --reload
```

Open **http://localhost:8000** in your browser.

## Example Queries

- `What is Sarah working on?`
- `Show me Mike's recent commits`
- `What has Lisa been up to this week?`
- `What JIRA tickets is John assigned to?`
- `Show me recent pull requests for octocat`

## Project Structure

```
src/
  jira_client.py     — async JIRA REST API wrapper
  github_client.py   — async GitHub REST API wrapper
  claude_agent.py    — tool definitions + Claude agent loop
  main.py            — FastAPI server + /api/chat endpoint
public/
  index.html         — chat UI
  style.css          — styling
  script.js          — frontend logic
```

## API Endpoint

`POST /api/chat`

```json
{
  "message": "What is Sarah working on?",
  "history": []
}
```

Response:
```json
{
  "response": "Here's what Sarah has been working on lately..."
}
```

## Demo Script (10-minute walkthrough)

Suggested query sequence for the live demo:

| # | Query | Demonstrates |
|---|---|---|
| 1 | `"What is Sarah working on?"` | Combined JIRA + GitHub summary |
| 2 | `"What has Mike committed this week?"` | GitHub commits focus |
| 3 | `"Show me Lisa's current JIRA tickets"` | JIRA-only focus |
| 4 | `"What is John working on these days?"` | Full combined flow |
| 5 | `"What is Alex working on?"` | User-not-found error handling |

## Error Cases Handled

- JIRA user not found → Claude suggests checking spelling
- GitHub username not found → Claude notifies clearly
- No open JIRA issues → mentioned in response
- No recent GitHub activity → mentioned in response
- API auth failures → descriptive error surfaced in chat
- GitHub rate limit → surfaced gracefully
