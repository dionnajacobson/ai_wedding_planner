const SESSION_KEY = "wedding_planner_session_id";
const USER_KEY = "wedding_planner_user";

const VENDOR_PIPELINE = [
  { category: "venue", label: "Venue" },
  { category: "catering", label: "Caterer" },
  { category: "flowers", label: "Florist" },
  { category: "photography", label: "Photographer" },
  { category: "music", label: "DJ" },
];

const VENUE_CARD_THEMES = ["sage", "sky", "rose"];

const onboardingPanelEl = document.getElementById("onboarding-panel");
const chatPanelEl = document.getElementById("chat-panel");
const appEl = document.querySelector(".app");
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
const weddingDashboardEl = document.getElementById("wedding-dashboard");
const weddingJsonEl = document.getElementById("wedding-json");

/** Format a number as USD currency. */
function formatCurrency(value) {
  if (value === null || value === undefined) {
    return null;
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
    return null;
  }
  const parsed = new Date(`${value}T00:00:00`);
  return parsed.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/** Format an ISO date as a short month label. */
function formatMonth(value) {
  if (!value) {
    return null;
  }
  const parsed = new Date(`${value}T00:00:00`);
  return parsed.toLocaleDateString("en-US", { month: "long" });
}

/** Format an enum-like string for display. */
function formatLabel(value) {
  if (!value) {
    return "";
  }
  return value.replaceAll("_", " ");
}

/** Capitalize the first character of a string. */
function capitalize(value) {
  if (!value) {
    return "";
  }
  return value.charAt(0).toUpperCase() + value.slice(1);
}

/** Build a display title from wedding profile fields. */
function buildWeddingTitle(wedding) {
  if (wedding.style.length === 0 && !wedding.location) {
    return "Your wedding";
  }
  const style = wedding.style.length > 0 ? wedding.style.join(" ") : "wedding";
  const location = wedding.location ? ` near ${wedding.location.split(",")[0]}` : "";
  const article = /^[aeiou]/i.test(style) ? "An" : "A";
  const title = `${article} ${style}${location} wedding`;
  return capitalize(title);
}

/** Build the compact summary line shown under the title. */
function buildSummaryLine(wedding) {
  const parts = [];
  if (wedding.style.length > 0) {
    parts.push(`${capitalize(wedding.style.join(" "))} wedding`);
  }
  if (wedding.location) {
    parts.push(wedding.location);
  }
  if (wedding.wedding_date) {
    parts.push(formatMonth(wedding.wedding_date));
  }
  if (wedding.guest_count) {
    parts.push(`${wedding.guest_count} guests`);
  }
  if (wedding.budget_cap) {
    parts.push(`~${formatCurrency(wedding.budget_cap)}`);
  }
  return parts.join(" · ");
}

/** Map vendor status values to dashboard badge styles. */
function vendorStatusMeta(status) {
  const mapping = {
    booked: { className: "status-booked", label: "booked" },
    contacted: { className: "status-negotiating", label: "negotiating" },
    declined: { className: "status-muted", label: "declined" },
    researching: { className: "status-contact", label: "to contact" },
  };
  return mapping[status] || mapping.researching;
}

/** Return vendors filtered by category. */
function vendorsByCategory(wedding, category) {
  return wedding.vendors.filter((vendor) => vendor.category === category);
}

/** Pick the highlighted venue from saved vendors. */
function pickFeaturedVenue(venues) {
  if (venues.length === 0) {
    return null;
  }
  const booked = venues.find((venue) => venue.status === "booked");
  if (booked) {
    return booked;
  }
  const contacted = venues.find((venue) => venue.status === "contacted");
  if (contacted) {
    return contacted;
  }
  return venues[0];
}

/** Count vendors that are not booked or declined. */
function countActiveVendors(wedding) {
  const active = wedding.vendors.filter(
    (vendor) => vendor.status !== "booked" && vendor.status !== "declined"
  );
  return active.length;
}

/** Create a DOM element with optional class and text. */
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) {
    node.className = className;
  }
  if (text !== undefined) {
    node.textContent = text;
  }
  return node;
}

/** Render venue cards for the dashboard. */
function renderVenueCards(wedding) {
  const section = el("section", "dash-section");
  section.appendChild(el("h3", "dash-section-title", "Venues, price-shopped"));

  const venues = vendorsByCategory(wedding, "venue");
  if (venues.length === 0) {
    const empty = el("p", "dash-empty", "Venue options will appear here as you shortlist locations.");
    section.appendChild(empty);
    return section;
  }

  const featured = pickFeaturedVenue(venues);
  const grid = el("div", "venue-grid");
  venues.forEach((venue, index) => {
    const card = el("article", "venue-card");
    if (venue.id === featured.id) {
      card.classList.add("venue-card--featured");
      card.appendChild(el("span", "venue-badge", "Best fit"));
    }

    const theme = VENUE_CARD_THEMES[index % VENUE_CARD_THEMES.length];
    const icon = el("div", `venue-icon venue-icon--${theme}`);
    icon.textContent = "✦";
    card.appendChild(icon);

    const header = el("div", "venue-card-header");
    header.append(el("strong", "venue-name", venue.name));
    header.append(el("span", "venue-status", formatLabel(venue.status)));
    card.appendChild(header);

    const price = formatCurrency(venue.estimated_cost) || "Quote pending";
    card.appendChild(el("p", "venue-price", price));

    const tags = el("div", "tag-row");
    tags.appendChild(el("span", "tag", formatLabel(venue.category)));
    if (wedding.guest_count) {
      tags.appendChild(el("span", "tag", `${wedding.guest_count} cap`));
    }
    if (venue.notes) {
      tags.appendChild(el("span", "tag", venue.notes));
    }
    card.appendChild(tags);
    grid.appendChild(card);
  });

  section.appendChild(grid);
  return section;
}

/** Render a horizontal quote comparison for venue pricing. */
function renderQuoteComparison(wedding) {
  const section = el("section", "dash-section");
  section.appendChild(el("h3", "dash-section-title", "Quotes, compared"));

  const venues = vendorsByCategory(wedding, "venue");
  if (venues.length === 0) {
    const empty = el("p", "dash-empty", "Price comparisons appear once venue quotes are saved.");
    section.appendChild(empty);
    return section;
  }

  const featured = pickFeaturedVenue(venues);
  const row = el("div", "quote-row");
  venues.forEach((venue) => {
    const chip = el("div", "quote-chip");
    const shortName = venue.name.split(" ")[0];
    const amount = formatCurrency(venue.estimated_cost) || "TBD";
    chip.textContent = `${shortName} ${amount}`;
    if (venue.id === featured.id) {
      chip.classList.add("quote-chip--featured");
    }
    row.appendChild(chip);
  });

  section.appendChild(row);
  section.appendChild(
    el(
      "p",
      "dash-footnote",
      "Ranked by fit from your saved vendors. Illustrative quotes."
    )
  );
  return section;
}

/** Render budget summary with progress bar. */
function renderBudgetSection(wedding) {
  const section = el("section", "dash-section");
  section.appendChild(el("h3", "dash-section-title", "Budget"));

  const stats = el("div", "budget-stats");
  stats.append(
    createStat("Cap", formatCurrency(wedding.budget_cap) || "—"),
    createStat("Allocated", formatCurrency(wedding.budget.allocated) || "$0"),
    createStat("Remaining", formatCurrency(wedding.budget.remaining) || "—")
  );
  section.appendChild(stats);

  if (wedding.budget_cap) {
    const progress = el("div", "budget-progress");
    const fill = el("div", "budget-progress-fill");
    const ratio = Math.min(wedding.budget.allocated / wedding.budget_cap, 1);
    fill.style.width = `${Math.round(ratio * 100)}%`;
    progress.appendChild(fill);
    section.appendChild(progress);
  }

  if (wedding.budget.items.length > 0) {
    const list = el("ul", "dash-list");
    wedding.budget.items.forEach((item) => {
      const row = el("li", "dash-list-item");
      row.append(
        el("span", "dash-list-label", `${formatLabel(item.category)} · ${item.name}`),
        el("span", "dash-list-value", formatCurrency(item.estimated_amount) || "—")
      );
      list.appendChild(row);
    });
    section.appendChild(list);
  }

  return section;
}

/** Render vendor pipeline with status badges. */
function renderVendorPipeline(wedding) {
  const section = el("section", "dash-section dash-section--compact");
  const header = el("div", "dash-section-heading");
  header.appendChild(el("h3", "dash-section-title", "Vendor pipeline"));
  const inFlight = countActiveVendors(wedding);
  header.appendChild(el("span", "dash-section-meta", `${inFlight} in flight`));
  section.appendChild(header);

  const list = el("ul", "pipeline-list");
  VENDOR_PIPELINE.forEach(({ category, label }) => {
    const matches = vendorsByCategory(wedding, category);
    const vendor = matches[0];
    const status = vendor ? vendorStatusMeta(vendor.status) : vendorStatusMeta("researching");

    const row = el("li", "pipeline-item");
    row.append(el("span", "pipeline-label", label));
    const badge = el("span", `pipeline-badge ${status.className}`, status.label);
    row.appendChild(badge);
    list.appendChild(row);
  });

  section.appendChild(list);
  return section;
}

/** Render notes when present. */
function renderNotesSection(wedding) {
  if (!wedding.notes) {
    return null;
  }
  const section = el("section", "dash-section dash-section--compact");
  section.appendChild(el("h3", "dash-section-title", "Notes"));
  section.appendChild(el("p", "dash-notes", wedding.notes));
  return section;
}

/** Build a small stat block for the budget row. */
function createStat(label, value) {
  const block = el("div", "budget-stat");
  block.append(el("span", "budget-stat-label", label), el("strong", "budget-stat-value", value));
  return block;
}

/** Render the full wedding dashboard from API data. */
function renderWeddingProfile(wedding) {
  weddingDashboardEl.innerHTML = "";
  weddingJsonEl.textContent = JSON.stringify(wedding, null, 2);

  const dashboard = el("div", "wedding-dashboard-inner");
  dashboard.classList.add("wedding-dashboard-inner--refresh");

  const metaBar = el("div", "dash-meta-bar");
  metaBar.textContent = buildSummaryLine(wedding) || "Share details in chat to build your wedding profile.";
  dashboard.appendChild(metaBar);

  const hero = el("header", "dash-hero");
  hero.appendChild(el("h2", "dash-title", buildWeddingTitle(wedding)));

  const subtitleParts = [];
  const formattedDate = formatDate(wedding.wedding_date);
  if (formattedDate) {
    subtitleParts.push(formattedDate);
  }
  if (wedding.vendors.length > 0) {
    subtitleParts.push(`${wedding.vendors.length} vendors tracked`);
  }
  if (wedding.budget.items.length > 0) {
    subtitleParts.push(`${wedding.budget.items.length} budget lines`);
  }
  if (wedding.style.length > 0) {
    subtitleParts.push(wedding.style.join(", "));
  }
  hero.appendChild(el("p", "dash-subtitle", subtitleParts.join(" · ") || "Planning in progress"));

  const tagRow = el("div", "dash-tag-row");
  if (wedding.location) {
    tagRow.appendChild(el("span", "dash-tag", wedding.location));
  }
  if (wedding.guest_count) {
    tagRow.appendChild(el("span", "dash-tag", `${wedding.guest_count} guests`));
  }
  if (wedding.budget_cap) {
    tagRow.appendChild(el("span", "dash-tag", formatCurrency(wedding.budget_cap)));
  }
  if (tagRow.childElementCount > 0) {
    hero.appendChild(tagRow);
  }
  dashboard.appendChild(hero);

  dashboard.appendChild(renderVenueCards(wedding));
  dashboard.appendChild(renderQuoteComparison(wedding));
  dashboard.appendChild(renderBudgetSection(wedding));

  const bottomGrid = el("div", "dash-bottom-grid");
  const pipeline = renderVendorPipeline(wedding);
  bottomGrid.appendChild(pipeline);

  const notes = renderNotesSection(wedding);
  if (notes) {
    bottomGrid.appendChild(notes);
  } else {
    const placeholder = el("section", "dash-section dash-section--compact");
    placeholder.appendChild(el("h3", "dash-section-title", "The day"));
    placeholder.appendChild(
      el("p", "dash-empty", "Your timeline will appear here once you start planning the schedule.")
    );
    bottomGrid.appendChild(placeholder);
  }
  dashboard.appendChild(bottomGrid);

  weddingDashboardEl.appendChild(dashboard);
  requestAnimationFrame(() => {
    dashboard.classList.remove("wedding-dashboard-inner--refresh");
  });
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
  appEl.classList.remove("app--chat");
  onboardingPanelEl.hidden = false;
  chatPanelEl.hidden = true;
  messagesEl.innerHTML = "";
  weddingDashboardEl.innerHTML = "";
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
  appEl.classList.add("app--chat");
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

/** Escape HTML special characters so markdown source can't inject markup. */
function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

/** Apply inline markdown formatting (bold, italic, code, links) to escaped text. */
function renderInlineMarkdown(text) {
  let html = escapeHtml(text);
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, "<em>$1</em>");
  html = html.replace(
    /!\[([^\]]*)\]\((https?:\/\/[^\s)]+)\)/g,
    '<img src="$2" alt="$1" loading="lazy">'
  );
  html = html.replace(
    /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
  );
  return html;
}

/** Convert a small subset of markdown (headers, lists, emphasis, links, paragraphs) to safe HTML. */
function renderMarkdown(source) {
  const lines = source.replace(/\r\n/g, "\n").split("\n");
  const htmlParts = [];
  let listTag = null;
  let listItems = [];
  let paragraphLines = [];

  function flushParagraph() {
    if (paragraphLines.length === 0) {
      return;
    }
    htmlParts.push(`<p>${paragraphLines.map(renderInlineMarkdown).join("<br>")}</p>`);
    paragraphLines = [];
  }

  function flushList() {
    if (listItems.length === 0) {
      return;
    }
    const items = listItems.map((item) => `<li>${renderInlineMarkdown(item)}</li>`).join("");
    htmlParts.push(`<${listTag}>${items}</${listTag}>`);
    listItems = [];
    listTag = null;
  }

  for (const rawLine of lines) {
    const line = rawLine.trim();

    if (line === "") {
      flushParagraph();
      flushList();
      continue;
    }

    const headerMatch = line.match(/^(#{1,3})\s+(.*)$/);
    if (headerMatch) {
      flushParagraph();
      flushList();
      const level = headerMatch[1].length + 3;
      htmlParts.push(`<h${level}>${renderInlineMarkdown(headerMatch[2])}</h${level}>`);
      continue;
    }

    const bulletMatch = line.match(/^[-*]\s+(.*)$/);
    if (bulletMatch) {
      flushParagraph();
      if (listTag && listTag !== "ul") {
        flushList();
      }
      listTag = "ul";
      listItems.push(bulletMatch[1]);
      continue;
    }

    const numberedMatch = line.match(/^\d+\.\s+(.*)$/);
    if (numberedMatch) {
      flushParagraph();
      if (listTag && listTag !== "ol") {
        flushList();
      }
      listTag = "ol";
      listItems.push(numberedMatch[1]);
      continue;
    }

    flushList();
    paragraphLines.push(line);
  }

  flushParagraph();
  flushList();

  return htmlParts.join("");
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
  if (role === "user") {
    bubble.textContent = content;
  } else {
    bubble.innerHTML = renderMarkdown(content);
  }

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
