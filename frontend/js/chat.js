// ======================================================
// EduRAG AI Chat
// chat.js (Part 1)
// ======================================================

const API_URL = "http://127.0.0.1:8000/chat/ask";

const token = localStorage.getItem("access_token");

const params = new URLSearchParams(window.location.search);

const subjectId =
    params.get("subject_id");

const subjectName =
    localStorage.getItem("subject_name");

// ======================================================
// Elements
// ======================================================

const chatMessages =
    document.getElementById("chatMessages");

const questionInput =
    document.getElementById("questionInput");

const sendBtn =
    document.getElementById("sendBtn");

const newChatBtn =
    document.getElementById("newChatBtn");

const promptChips =
    document.querySelectorAll(".prompt-chip");

// ======================================================
// Initialization
// ======================================================

window.addEventListener("DOMContentLoaded", () => {

    if (!token) {

        window.location.href = "login.html";

        return;

    }

    if (!subjectId) {

        alert("No subject selected.");

        window.location.href = "subjects.html";

        return;

    }

    document.getElementById("subjectTitle").innerText =
        "🤖 " + subjectName;

    questionInput.focus();

});

// ======================================================
// Events
// ======================================================

sendBtn.addEventListener("click", sendMessage);

questionInput.addEventListener("keydown", (event) => {

    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        sendMessage();

    }

});

// ======================================================
// Prompt Chips
// ======================================================

promptChips.forEach(chip => {

    chip.addEventListener("click", () => {

        questionInput.value =
            chip.innerText;

        questionInput.focus();

    });

});

// ======================================================
// New Chat
// ======================================================

newChatBtn.addEventListener("click", () => {

    chatMessages.innerHTML = `

        <div class="ai-message">

            <div class="chat-avatar">

                🤖

            </div>

            <div class="chat-bubble">

                <h3>

                    New Chat Started

                </h3>

                <p>

                    Ask anything about your uploaded documents.

                </p>

            </div>

        </div>

    `;

    questionInput.value = "";

    questionInput.focus();

});

// ======================================================
// Send Message
// ======================================================

async function sendMessage() {

    const question =
        questionInput.value.trim();

    if (question === "") {

        return;

    }

    addUserMessage(question);

    questionInput.value = "";

    questionInput.focus();

    showThinking();

    disableChat();

    try {

        const response =
            await fetch(API_URL, {

                method: "POST",

                headers: {

                    "Content-Type": "application/json",

                    "Authorization":
                        "Bearer " + token

                },

                body: JSON.stringify({

                    question: question,

                    subject_id: subjectId

                })

            });

        if (!response.ok) {

            const error =
                await response.text();

            throw new Error(error);

        }

        const data =
            await response.json();

        removeThinking();

        addAIMessage(

            data.answer,

            data.citations

        );

    }

    catch (error) {

        console.error(error);

        removeThinking();

        addAIMessage(

            "❌ Unable to contact EduRAG AI."

        );

    }

    finally {

        enableChat();

    }

}

// ======================================================
// User Message
// ======================================================

function addUserMessage(message) {

    const messageDiv = document.createElement("div");

    messageDiv.className = "user-message";

    messageDiv.innerHTML = `

        <div class="chat-avatar">

            👤

        </div>

        <div class="chat-bubble">

            ${message.replace(/\n/g, "<br>")}

        </div>

    `;

    chatMessages.appendChild(messageDiv);

    scrollToBottom();

}

// ======================================================
// Thinking Indicator
// ======================================================

function showThinking() {

    const thinking = document.createElement("div");

    thinking.className = "ai-message";

    thinking.id = "thinking";

    thinking.innerHTML = `

        <div class="chat-avatar">

            🤖

        </div>

        <div class="chat-bubble thinking-bubble">

            <span class="typing-dot"></span>

            <span class="typing-dot"></span>

            <span class="typing-dot"></span>

        </div>

    `;

    chatMessages.appendChild(thinking);

    scrollToBottom();

}

function removeThinking() {

    const thinking =
        document.getElementById("thinking");

    if (thinking) {

        thinking.remove();

    }

}

// ======================================================
// AI Message
// ======================================================

function addAIMessage(answer, citations = []) {

    const messageDiv =
        document.createElement("div");

    messageDiv.className = "ai-message";

    let citationsHTML = "";

    if (citations.length > 0) {

        citationsHTML = `

            <div class="citations">

                <h4>

                    <i class="bi bi-journal-text"></i>

                    Sources

                </h4>

                ${citations.map(citation => `

                    <div class="citation">

                        <strong>

                            ${citation.document}

                        </strong>

                        <p>

                            Page ${citation.page}

                        </p>

                        <small>

                            ${citation.snippet}

                        </small>

                    </div>

                `).join("")}

            </div>

        `;

    }

    messageDiv.innerHTML = `

        <div class="chat-avatar">

            🤖

        </div>

        <div class="chat-bubble">

            <div class="answer">

                ${answer.replace(/\n/g,"<br>")}

            </div>

            ${citationsHTML}

        </div>

    `;

    chatMessages.appendChild(messageDiv);

    scrollToBottom();

}

// ======================================================
// Auto Scroll
// ======================================================

function scrollToBottom() {

    chatMessages.scrollTo({

        top: chatMessages.scrollHeight,

        behavior: "smooth"

    });

}

// ======================================================
// Utility
// ======================================================

function disableChat() {

    sendBtn.disabled = true;

    questionInput.disabled = true;

}

function enableChat() {

    sendBtn.disabled = false;

    questionInput.disabled = false;

    questionInput.focus();

}

// ======================================================
// Logout
// ======================================================

const logoutBtn =
    document.querySelector(".logout-btn");

if (logoutBtn) {

    logoutBtn.addEventListener("click", () => {

        localStorage.removeItem("access_token");

        window.location.href = "login.html";

    });

}