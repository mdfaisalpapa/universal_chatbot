/**
 * Universal Chatbot Embeddable Web Widget
 * Handles floating chat UI, session persistence across browser refreshes,
 * and bidirectional communication with Frappe backend.
 */
(function () {
  "use strict";

  // Prevent double-initialization
  if (window.UniversalChatbotInitialized) return;
  window.UniversalChatbotInitialized = true;

  // 1. Locate script configuration
  const currentScript =
    document.currentScript ||
    document.querySelector("script[data-deployment-key]");

  const globalConfig = window.UniversalChatbotConfig || {};
  const deploymentKey =
    (currentScript && currentScript.getAttribute("data-deployment-key")) ||
    globalConfig.deployment_key;
  const serverUrl =
    (currentScript && currentScript.getAttribute("data-server-url")) ||
    globalConfig.server_url ||
    window.location.origin;

  if (!deploymentKey) {
    console.error(
      "[Universal Chatbot] Missing data-deployment-key attribute on script tag."
    );
    return;
  }

  // 2. Identity & State Persistence
  function getOrCreateUserId() {
    let uid = localStorage.getItem("ucb_external_user_id");
    if (!uid) {
      uid = "usr_" + Math.random().toString(36).substring(2, 11) + Date.now().toString(36);
      localStorage.setItem("ucb_external_user_id", uid);
    }
    return uid;
  }

  const externalUserId = getOrCreateUserId();
  const storageKeyConv = `ucb_conv_${deploymentKey}`;
  let conversationId = localStorage.getItem(storageKeyConv) || null;

  // 3. UI State
  let isOpen = false;
  let isSending = false;

  // 4. Inject Stylesheet if not already present
  const cssHref = `${serverUrl}/assets/universal_chatbot/widget/chatbot.css`;
  if (!document.querySelector(`link[href="${cssHref}"]`)) {
    const linkEl = document.createElement("link");
    linkEl.rel = "stylesheet";
    linkEl.href = cssHref;
    document.head.appendChild(linkEl);
  }

  // 5. Construct DOM elements
  const container = document.createElement("div");
  container.id = "ucb-widget-container";
  container.innerHTML = `
    <button class="ucb-launcher" id="ucb-launcher" aria-label="Open chat">
      <svg viewBox="0 0 24 24">
        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
      </svg>
    </button>
    <div class="ucb-window" id="ucb-window">
      <div class="ucb-header">
        <div class="ucb-header-info">
          <div class="ucb-avatar" id="ucb-avatar">🤖</div>
          <div class="ucb-title-area">
            <div class="ucb-title" id="ucb-title">Chat Assistant</div>
            <div class="ucb-status">
              <span class="ucb-status-dot"></span>
              <span>Online</span>
            </div>
          </div>
        </div>
        <button class="ucb-close-btn" id="ucb-close-btn" aria-label="Close chat">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
          </svg>
        </button>
      </div>
      <div class="ucb-messages" id="ucb-messages"></div>
      <form class="ucb-input-form" id="ucb-input-form">
        <input type="text" class="ucb-input-field" id="ucb-input-field" placeholder="Type a message..." autocomplete="off"/>
        <button type="submit" class="ucb-send-btn" id="ucb-send-btn" aria-label="Send">
          <svg viewBox="0 0 24 24">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
          </svg>
        </button>
      </form>
    </div>
  `;
  document.body.appendChild(container);

  const launcher = document.getElementById("ucb-launcher");
  const windowEl = document.getElementById("ucb-window");
  const closeBtn = document.getElementById("ucb-close-btn");
  const messagesEl = document.getElementById("ucb-messages");
  const formEl = document.getElementById("ucb-input-form");
  const inputEl = document.getElementById("ucb-input-field");
  const titleEl = document.getElementById("ucb-title");
  const avatarEl = document.getElementById("ucb-avatar");

  // 6. Toggle Chat
  function toggleChat(forceOpen) {
    isOpen = typeof forceOpen === "boolean" ? forceOpen : !isOpen;
    if (isOpen) {
      windowEl.classList.add("ucb-open");
      inputEl.focus();
    } else {
      windowEl.classList.remove("ucb-open");
    }
  }

  launcher.addEventListener("click", () => toggleChat());
  closeBtn.addEventListener("click", () => toggleChat(false));

  // 7. Message Rendering
  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function appendMessage(text, direction, options) {
    const row = document.createElement("div");
    row.className = `ucb-message-row ucb-${direction}`;

    const bubble = document.createElement("div");
    bubble.className = "ucb-bubble";
    bubble.textContent = text;
    row.appendChild(bubble);

    // If message contains multiple-choice or quick reply options
    if (options && options.length > 0 && direction === "bot") {
      const optContainer = document.createElement("div");
      optContainer.className = "ucb-options-container";

      options.forEach((opt) => {
        const btn = document.createElement("button");
        btn.className = "ucb-option-btn";
        btn.textContent = opt.label || opt.value;
        btn.addEventListener("click", () => {
          handleUserSend(opt.value || opt.label);
          optContainer.style.display = "none";
        });
        optContainer.appendChild(btn);
      });
      row.appendChild(optContainer);
    }

    messagesEl.appendChild(row);
    scrollToBottom();
  }

  function showTypingIndicator() {
    const typingRow = document.createElement("div");
    typingRow.id = "ucb-typing-indicator";
    typingRow.className = "ucb-message-row ucb-bot";
    typingRow.innerHTML = `
      <div class="ucb-typing">
        <span class="ucb-dot"></span>
        <span class="ucb-dot"></span>
        <span class="ucb-dot"></span>
      </div>
    `;
    messagesEl.appendChild(typingRow);
    scrollToBottom();
  }

  function removeTypingIndicator() {
    const el = document.getElementById("ucb-typing-indicator");
    if (el) el.remove();
  }

  // 8. API Communication
  async function apiCall(method, params) {
    const url = `${serverUrl}/api/method/universal_chatbot.api.v1.chat.${method}`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(params),
    });

    const data = await response.json();
    if (!response.ok || data.exc) {
      const err = (data._server_messages && JSON.parse(data._server_messages)[0]) || data.message || "Request failed";
      throw new Error(typeof err === "string" ? err : JSON.stringify(err));
    }
    return data.message || data;
  }

  // 9. Initialize Session on Page Load (Preserving State)
  async function initSession() {
    try {
      const res = await apiCall("init_chat", {
        deployment_key: deploymentKey,
        external_user_id: externalUserId,
        conversation_id: conversationId,
      });

      if (res.conversation_id) {
        conversationId = res.conversation_id;
        localStorage.setItem(storageKeyConv, conversationId);
      }

      if (res.bot_title) {
        titleEl.textContent = res.bot_title;
      }

      if (res.bot_avatar) {
        avatarEl.innerHTML = `<img src="${res.bot_avatar}" alt="Avatar"/>`;
      }

      // Render restored history or initial messages
      messagesEl.innerHTML = "";
      if (res.messages && res.messages.length > 0) {
        res.messages.forEach((m) => {
          appendMessage(m.text, m.direction === "inbound" ? "user" : "bot", m.options);
        });
      }
    } catch (err) {
      console.warn("[Universal Chatbot] Init session error:", err.message);
    }
  }

  // 10. Handle User Message Submission
  async function handleUserSend(textToSend) {
    const text = (textToSend || inputEl.value || "").trim();
    if (!text || isSending) return;

    inputEl.value = "";
    isSending = true;

    // Display user message immediately in chat
    appendMessage(text, "user");
    showTypingIndicator();

    try {
      const res = await apiCall("send_message", {
        deployment_key: deploymentKey,
        external_user_id: externalUserId,
        conversation_id: conversationId,
        message: text,
      });

      removeTypingIndicator();

      if (res.messages && res.messages.length > 0) {
        res.messages.forEach((m) => {
          appendMessage(m.text || m.content, "bot", m.options || res.actions);
        });
      } else if (res.response && res.response.text) {
        appendMessage(res.response.text, "bot", res.actions);
      }
    } catch (err) {
      removeTypingIndicator();
      appendMessage("Sorry, I encountered an error connecting to the server.", "bot");
      console.error("[Universal Chatbot] Send message failed:", err);
    } finally {
      isSending = false;
    }
  }

  formEl.addEventListener("submit", (e) => {
    e.preventDefault();
    handleUserSend();
  });

  // Start initialization
  initSession();
})();
