"""
main.py — FastAPI server

Two endpoints:
  POST /api/chat         — non-streaming, returns full response as JSON
  POST /api/chat/stream  — SSE stream, emits tool events + final response in real time

The static chat UI in public/ is served from the root path.
"""

from pathlib import Path

from dotenv import load_dotenv

# Load .env before importing claude_agent so API keys are set at module level.
# override=True ensures .env values win over any ambient shell variables.
load_dotenv(override=True)

import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .claude_agent import run_agent, run_agent_stream

app = FastAPI(title="AutonomizeAI Team Activity Bot")

# Permissive CORS for local development — tighten for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []  # full conversation history sent by the frontend


class ChatResponse(BaseModel):
    response: str


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Non-streaming chat. Waits for the full agent response before returning."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    try:
        response = await run_agent(req.message.strip(), req.history)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    """Streaming chat via Server-Sent Events.

    The frontend reads this stream and updates the UI as each tool fires,
    showing a live activity feed (spinner → checkmark per step) before the
    final response text appears.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    async def generate():
        try:
            async for chunk in run_agent_stream(req.message.strip(), req.history):
                yield chunk
        except Exception as e:
            # Surface exceptions as an error event rather than a broken stream
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # prevents nginx from buffering SSE chunks
        },
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


# Serve the static chat UI from public/ at the root path.
# This must come last — FastAPI matches routes top-to-bottom and the static
# mount would shadow the API routes if registered first.
public_dir = Path(__file__).parent.parent / "public"
if public_dir.exists():
    app.mount("/", StaticFiles(directory=str(public_dir), html=True), name="static")
