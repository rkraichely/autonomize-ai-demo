// script.js — chat UI logic
//
// Connects to POST /api/chat/stream (SSE) so tool activity appears in real
// time: spinners while tools are running, checkmarks when they finish, then
// the prose response fades in. Conversation history is kept in memory and
// sent with each request so Claude has context for follow-ups.

const messagesEl = document.getElementById('messages');
const form = document.getElementById('input-form');
const input = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

// Full conversation history — each entry is {role, content}.
// Sent to the backend on every message so Claude can handle follow-ups.
let history = [];

function scrollToBottom() {
  messagesEl.parentElement.scrollTop = messagesEl.parentElement.scrollHeight;
}

function setInputEnabled(enabled) {
  input.disabled = !enabled;
  sendBtn.disabled = !enabled;
  if (enabled) input.focus();
}

// --- Text formatting ---

function escapeHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// Inline formatting: bold and code spans only
function inline(s) {
  return escapeHtml(s)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>');
}

// Line-by-line formatter that groups consecutive bullet lines into a <ul>
// and wraps plain text runs in <p> tags. Blank lines act as block separators.
function formatText(text) {
  const out = [];
  let listItems = [];
  let paraLines = [];

  const flushList = () => {
    if (listItems.length) {
      out.push('<ul>' + listItems.map(li => `<li>${inline(li)}</li>`).join('') + '</ul>');
      listItems = [];
    }
  };
  const flushPara = () => {
    if (paraLines.length) {
      out.push('<p>' + paraLines.map(inline).join('<br>') + '</p>');
      paraLines = [];
    }
  };

  for (const raw of text.split('\n')) {
    const line = raw.trim();
    if (!line) { flushList(); flushPara(); continue; }

    const item   = line.match(/^(?:[-*]|\d+\.)\s+(.+)$/);
    const header = line.match(/^#{1,3}\s+(.+)$/);

    if (item) {
      flushPara();
      listItems.push(item[1]);
    } else if (header) {
      flushList(); flushPara();
      out.push(`<p><strong>${inline(header[1])}</strong></p>`);
    } else {
      flushList();
      paraLines.push(line);
    }
  }
  flushList();
  flushPara();
  return out.join('');
}

// --- Activity feed helpers ---
// The assistant bubble starts as an activity feed (spinners) and transitions
// to the prose response once Claude finishes.

function createAssistantMessage() {
  const msg = document.createElement('div');
  msg.className = 'message assistant';

  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.textContent = 'AI';

  const bubble = document.createElement('div');
  bubble.className = 'bubble activity-bubble';
  bubble.innerHTML = '<div class="activity-feed"></div>';

  msg.appendChild(avatar);
  msg.appendChild(bubble);
  messagesEl.appendChild(msg);
  scrollToBottom();
  return bubble;
}

// Adds a new spinning step to the activity feed when a tool starts
function addActivityStep(bubble, id, label) {
  const feed = bubble.querySelector('.activity-feed');
  const step = document.createElement('div');
  step.className = 'activity-step';
  step.dataset.id = id;  // used to find the step again when the tool completes
  step.innerHTML = `<span class="step-spinner"></span><span class="step-label">${escapeHtml(label)}...</span>`;
  feed.appendChild(step);
  scrollToBottom();
}

// Replaces the spinner with a checkmark (or ✗ on error) when a tool finishes
function completeActivityStep(bubble, id, label, isError) {
  const step = bubble.querySelector(`[data-id="${id}"]`);
  if (!step) return;
  const spinner = step.querySelector('.step-spinner');
  const icon = document.createElement('span');
  icon.className = isError ? 'step-icon step-icon--error' : 'step-icon step-icon--done';
  icon.textContent = isError ? '✗' : '✓';
  spinner.replaceWith(icon);
  step.querySelector('.step-label').textContent = label;
}

// Renders JIRA ticket and GitHub PR links as clickable pills
function renderLinks(links) {
  if (!links.length) return '';
  const pills = links.map(l => {
    const cls = l.kind === 'jira' ? 'source-link--jira' : 'source-link--github';
    return `<a href="${l.url}" target="_blank" rel="noopener" class="source-link ${cls}">${escapeHtml(l.label)} ↗</a>`;
  }).join('');
  return `<div class="source-links">${pills}</div>`;
}

// Transitions the activity bubble to the final response text.
// Brief delay lets the user see the last checkmarks before the text appears.
function resolveActivityBubble(bubble, text, links = []) {
  setTimeout(() => {
    bubble.className = 'bubble';
    bubble.innerHTML = formatText(text) + renderLinks(links);
    scrollToBottom();
  }, 300);
}

function showErrorInBubble(bubble, text) {
  bubble.className = 'bubble error';
  bubble.textContent = text;
  scrollToBottom();
}

// --- Message send ---

function addUserMessage(text) {
  const msg = document.createElement('div');
  msg.className = 'message user';

  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.textContent = 'You';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;

  msg.appendChild(avatar);
  msg.appendChild(bubble);
  messagesEl.appendChild(msg);
  scrollToBottom();
}

async function sendMessage(text) {
  if (!text.trim()) return;

  addUserMessage(text);
  history.push({ role: 'user', content: text });
  setInputEnabled(false);

  // Create the activity bubble immediately so the user sees something right away
  const bubble = createAssistantMessage();

  try {
    const res = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      // Send history minus the current message — the backend appends it
      body: JSON.stringify({ message: text, history: history.slice(0, -1) }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
      showErrorInBubble(bubble, `Error: ${err.detail || res.statusText}`);
      history.pop();
      return;
    }

    // Read the SSE stream manually using fetch + ReadableStream.
    // EventSource only supports GET, so we use fetch for POST streams.
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let pendingLinks = [];  // links event arrives before response event

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // Split on newlines and process any complete "data: ..." lines.
      // Keep any partial line in the buffer for the next chunk.
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        let evt;
        try { evt = JSON.parse(line.slice(6)); } catch { continue; }

        if (evt.type === 'tool_start') {
          addActivityStep(bubble, evt.id, evt.label);
        } else if (evt.type === 'tool_done') {
          completeActivityStep(bubble, evt.id, evt.label, evt.is_error);
        } else if (evt.type === 'links') {
          // Hold onto links until the response arrives so we can attach them
          pendingLinks = evt.items;
        } else if (evt.type === 'response') {
          resolveActivityBubble(bubble, evt.text, pendingLinks);
          history.push({ role: 'assistant', content: evt.text });
        } else if (evt.type === 'error') {
          showErrorInBubble(bubble, evt.text);
          history.pop();
        }
      }
    }
  } catch (e) {
    showErrorInBubble(bubble, `Network error: ${e.message}`);
    history.pop();
  } finally {
    setInputEnabled(true);
  }
}

form.addEventListener('submit', e => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  sendMessage(text);
});
