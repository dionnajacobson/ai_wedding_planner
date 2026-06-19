const SESSION_KEY = "wedding_planner_session_id";

const messagesEl = document.getElementById("messages");
const statusEl = document.getElementById("status");
const statusTextEl = document.getElementById("status-text");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("message-input");
const sendButtonEl = document.getElementById("send-button");

/** Update the status line shown below the message list. */
function setStatus(text, visible = true) {
  statusTextEl.textContent = text;
  statusEl.hidden = !visible;
}

/** Enable or disable the message input and send button. */
function setComposerEnabled(enabled) {
  inputEl.disabled = !enabled;
  sendButtonEl.disabled = !enabled;
}

/** Append a user or assistant message bubble to the chat log. */
function appendMessage(role, content) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const label = document.createElement("span");
  label.className = "message-label";
  label.textContent = role === "user" ? "You" : "Planner";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.textContent = content;

  wrapper.append(label, bubble);
  messagesEl.appendChild(wrapper);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

/** Grow the textarea height to fit its content, up to a max height. */
function resizeInput() {
  inputEl.style.height = "auto";
  inputEl.style.height = `${Math.min(inputEl.scrollHeight, 160)}px`;
}

/** Call a JSON API endpoint and return the parsed response body. */
async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed (${response.status})`);
  }

  return response.json();
}

/** Restore an existing session from storage or start a new one. */
async function ensureSession() {
  const existing = localStorage.getItem(SESSION_KEY);
  if (existing) {
    try {
      const history = await api(`/api/chat/${existing}/messages`);
      history.messages.forEach((message) => {
        appendMessage(message.role, message.content);
      });
      return existing;
    } catch {
      localStorage.removeItem(SESSION_KEY);
    }
  }

  const started = await api("/api/chat/start", {
    method: "POST",
    body: JSON.stringify({}),
  });
  localStorage.setItem(SESSION_KEY, started.session_id);
  return started.session_id;
}

/** Send a user message and return the assistant reply payload. */
async function sendMessage(sessionId, message) {
  return api("/api/chat", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, message }),
  });
}

/** Initialize the chat UI and bind the current session id. */
async function boot() {
  setComposerEnabled(false);
  setStatus("Starting your session…");

  try {
    const sessionId = await ensureSession();
    setStatus("", false);
    setComposerEnabled(true);
    inputEl.focus();
    window.sessionId = sessionId;
  } catch (error) {
    setStatus("Could not start a chat session. Is the API running?");
    console.error(error);
  }
}

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();

  const message = inputEl.value.trim();
  if (!message || !window.sessionId) {
    return;
  }

  appendMessage("user", message);
  inputEl.value = "";
  resizeInput();
  setComposerEnabled(false);
  setStatus("Planning your answer…");

  try {
    const result = await sendMessage(window.sessionId, message);
    appendMessage(result.message.role, result.message.content);
    setStatus("", false);
  } catch (error) {
    appendMessage(
      "assistant",
      "Something went wrong sending that message. Please try again."
    );
    setStatus("", false);
    console.error(error);
  } finally {
    setComposerEnabled(true);
    inputEl.focus();
  }
});

inputEl.addEventListener("input", resizeInput);

boot();
