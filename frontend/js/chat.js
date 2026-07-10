const API_URL = "http://127.0.0.1:8000/chat/ask";

const messages = document.querySelector(".messages");
const textarea = document.querySelector("textarea");
const sendBtn = document.querySelector(".send-btn");
const suggestionButtons =
    document.querySelectorAll(".suggestions button");

suggestionButtons.forEach((button) => {

    button.addEventListener("click", () => {

        textarea.value = button.innerText;

        textarea.focus();

    });

});

textarea.addEventListener("keydown", (event) => {

    if (event.key === "Enter" && !event.shiftKey) {

        event.preventDefault();

        sendBtn.click();

    }

});

sendBtn.addEventListener("click", sendMessage);

async function sendMessage() {

    const question = textarea.value.trim();

    if (!question) return;

    addUserMessage(question);

    textarea.value = "";

    const typing = addTypingIndicator();

    try {

        const token =
            localStorage.getItem("token") || "";

        const subjectId =
            localStorage.getItem("subject_id") || "";

        const response = await fetch(API_URL, {

            method: "POST",

            headers: {

                "Content-Type": "application/json",

                "Authorization":
                    "Bearer " + token,

            },

            body: JSON.stringify({

                question: question,

                subject_id: subjectId,

            }),

        });

        removeTypingIndicator(typing);

        if (!response.ok) {

            addAIMessage(
                "Unable to get a response from EduRAG."
            );

            return;

        }

        const data = await response.json();

        addAIMessage(

            data.answer || "No response received."

        );

    } catch (error) {

        console.error(error);

        removeTypingIndicator(typing);

        addAIMessage(
            "Unable to connect to the backend."
        );

    }

}

function addUserMessage(text) {

    messages.insertAdjacentHTML(
        "beforeend",
        `
        <div class="user-message">

            <div class="bubble">

                ${escapeHtml(text)}

            </div>

        </div>
        `
    );

    scrollBottom();

}

function addAIMessage(text) {

    messages.insertAdjacentHTML(
        "beforeend",
        `
        <div class="ai-message">

            <div class="avatar">

                <i class="bi bi-robot"></i>

            </div>

            <div class="bubble">

                ${escapeHtml(text).replace(/\n/g, "<br>")}

            </div>

        </div>
        `
    );

    scrollBottom();

}

function addTypingIndicator() {

    const node = document.createElement("div");

    node.className = "ai-message";

    node.innerHTML = `
        <div class="avatar">

            <i class="bi bi-robot"></i>

        </div>

        <div class="bubble">

            <strong>EduRAG is typing...</strong>

        </div>
    `;

    messages.appendChild(node);

    scrollBottom();

    return node;

}

function removeTypingIndicator(node) {

    if (node) {

        node.remove();

    }

}

function scrollBottom() {

    messages.scrollTop = messages.scrollHeight;

}

function escapeHtml(text) {

    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

}