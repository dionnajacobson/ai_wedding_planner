const SESSION_KEY = "wedding_planner_session_id";
const USER_KEY = "wedding_planner_user";

const onboardingPanelEl = document.getElementById("onboarding-panel");
const chatPanelEl = document.getElementById("chat-panel");
const onboardingFormEl = document.getElementById("onboarding-form");
const onboardingErrorEl = document.getElementById("onboarding-error");
const startButtonEl = document.getElementById("start-button");
const newSessionButtonEl = document.getElementById("new-session-button");
const welcomeTextEl = document.getElementById("welcome-text");
const firstNameInputEl = document.getElementById("first-name-input");
const lastNameInputEl = document.getElementById("last-name-input");
const emailInputEl = document.getElementById("email-input");
const messagesEl = document.getElementById("messages");
const statusEl = document.getElementById("status");
const statusTextEl = document.getElementById("status-text");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("message-input");
const sendButtonEl = document.getElementById("send-button");

const weddingJsonEl = document.getElementById("wedding-json");
const weddingSummaryEl = document.getElementById("wedding-summary");

/** Format a number as USD currency. */
function formatCurrency(value) {
  if (value === null || value === undefined) {
    return "—";
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

/** Format an ISO date string for display. */
function formatDate(value) {
  if (!value) {
    return "—";
  }
  const parsed = new Date(`${value}T00:00:00`);
  return parsed.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/** Format an enum-like string for display. */
function formatLabel(value) {
  if (!value) {
    return "—";
  }
  return value.replaceAll("_", " ");
}

/** Build a labeled field row for the wedding sidebar. */
function createField(label, value) {
  const row = document.createElement("div");
  row.className = "wedding-field";

  const labelEl = document.createElement("span");
  labelEl.textContent = label;

  const valueEl = document.createElement("span");
  valueEl.textContent = value;

  row.append(labelEl, valueEl);
  return row;
}

/** Build a titled section in the wedding sidebar. */
function createSection(title) {
  const section = document.createElement("section");
  section.className = "wedding-section";

  const heading = document.createElement("h3");
  heading.textContent = title;
  section.appendChild(heading);
  return section;
}

/** Render the wedding profile sidebar from API data. */
function renderWeddingProfile(wedding) {
  weddingSummaryEl.innerHTML = "";
  weddingJsonEl.textContent = JSON.stringify(wedding, null, 2);

  const basics = createSection("Basics");
  basics.append(
    createField("Date", formatDate(wedding.wedding_date)),
    createField("Location", wedding.location || "—"),
    createField("Guests", wedding.guest_count ?? "—"),
    createField("Style", wedding.style.length > 0 ? wedding.style.join(", ") : "—")
  );

  const budget = createSection("Budget");
  budget.append(
    createField("Budget cap", formatCurrency(wedding.budget_cap)),
    createField("Allocated", formatCurrency(wedding.budget.allocated)),
    createField("Remaining", formatCurrency(wedding.budget.remaining))
  );

  if (wedding.budget.items.length > 0) {
    const list = document.createElement("ul");
    list.className = "wedding-list";
    wedding.budget.items.forEach((item) => {
      const entry = document.createElement("li");
      entry.textContent = `${formatLabel(item.category)} · ${item.name} · ${formatCurrency(item.estimated_amount)}`;
      list.appendChild(entry);
    });
    budget.appendChild(list);
  }

  const vendors = createSection("Vendors");
  if (wedding.vendors.length === 0) {
    const empty = document.createElement("p");
    empty.className = "wedding-empty";
    empty.textContent = "No vendors saved yet.";
    vendors.appendChild(empty);
  } else {
    const list = document.createElement("ul");
    list.className = "wedding-list";
    wedding.vendors.forEach((vendor) => {
      const entry = document.createElement("li");
      entry.textContent = `${formatLabel(vendor.category)} · ${vendor.name} · ${formatLabel(vendor.status)}`;
      list.appendChild(entry);
    });
    vendors.appendChild(list);
  }

  const sections = [basics, budget, vendors];
  if (wedding.notes) {
    const notes = createSection("Notes");
    const copy = document.createElement("p");
    copy.className = "wedding-empty";
    copy.textContent = wedding.notes;
    notes.appendChild(copy);
    sections.push(notes);
  }

  weddingSummaryEl.append(...sections);
}

/** Load the wedding profile for the active session. */
async function loadWeddingProfile(sessionId) {
  const response = await api(`/api/chat/${sessionId}/wedding`);
  renderWeddingProfile(response.wedding);
  return response.wedding;
}

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

/** Show the onboarding form and hide chat. */
function showOnboarding(user = null) {
  onboardingPanelEl.hidden = false;
  chatPanelEl.hidden = true;
  messagesEl.innerHTML = "";
  weddingSummaryEl.innerHTML = "";
  weddingJsonEl.textContent = "";
  window.sessionId = null;
  setStatus("", false);
  setComposerEnabled(false);

  firstNameInputEl.value = user?.first_name || "";
  lastNameInputEl.value = user?.last_name || "";
  emailInputEl.value = user?.email || "";
}

/** Show chat and hide the onboarding form. */
function showChat(user) {
  onboardingPanelEl.hidden = true;
  chatPanelEl.hidden = false;
  welcomeTextEl.textContent = `Planning with ${user.first_name} ${user.last_name}`;
}

/** Persist user details in browser storage. */
function saveUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/** Load saved user details from browser storage. */
function loadUser() {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) {
    return null;
  }

  try {
    const user = JSON.parse(raw);
    if (typeof user === "string") {
      return { email: user, first_name: "", last_name: "" };
    }
    return user;
  } catch {
    return { email: raw, first_name: "", last_name: "" };
  }
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

/** Start a session with the provided user details. */
async function startSession(user) {
  const started = await api("/api/chat/start", {
    method: "POST",
    body: JSON.stringify(user),
  });
  localStorage.setItem(SESSION_KEY, started.session_id);
  saveUser(user);
  return started.session_id;
}

/** Restore an existing session from storage. */
async function restoreSession(sessionId) {
  const history = await api(`/api/chat/${sessionId}/messages`);
  history.messages.forEach((message) => {
    appendMessage(message.role, message.content);
  });
  return sessionId;
}

/** Load chat history for a session and enable the composer. */
async function openChat(sessionId, user) {
  showChat(user);
  setComposerEnabled(true);
  inputEl.focus();
  window.sessionId = sessionId;
  await loadWeddingProfile(sessionId);
}

/** Initialize the app from saved session data or show onboarding. */
async function boot() {
  const savedUser = loadUser();
  const existingSession = localStorage.getItem(SESSION_KEY);

  if (existingSession && savedUser?.email) {
    try {
      setStatus("Loading your session…");
      showChat(savedUser);
      await restoreSession(existingSession);
      setStatus("", false);
      await openChat(existingSession, savedUser);
      return;
    } catch {
      localStorage.removeItem(SESSION_KEY);
      showOnboarding(savedUser);
      return;
    }
  }

  showOnboarding(savedUser);
}

/** Send a user message and return the assistant reply payload. */
async function sendMessage(sessionId, message) {
  return api("/api/chat", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, message }),
  });
}

onboardingFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  onboardingErrorEl.hidden = true;
  startButtonEl.disabled = true;
  startButtonEl.textContent = "Starting…";

  const user = {
    first_name: firstNameInputEl.value.trim(),
    last_name: lastNameInputEl.value.trim(),
    email: emailInputEl.value.trim(),
  };

  try {
    const sessionId = await startSession(user);
    await openChat(sessionId, user);
  } catch (error) {
    onboardingErrorEl.textContent =
      "Could not start your session. Check your details and try again.";
    onboardingErrorEl.hidden = false;
    console.error(error);
  } finally {
    startButtonEl.disabled = false;
    startButtonEl.textContent = "Start planning";
  }
});

newSessionButtonEl.addEventListener("click", () => {
  localStorage.removeItem(SESSION_KEY);
  showOnboarding(loadUser());
});

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
    await loadWeddingProfile(window.sessionId);
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
