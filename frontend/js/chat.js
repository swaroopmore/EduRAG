const API_URL = "http://127.0.0.1:8000/chat/ask";

const token = localStorage.getItem("access_token");

const params = new URLSearchParams(window.location.search);

const subjectId =
    params.get("subject_id");

const subjectName =
    localStorage.getItem("subject_name");

const chatMessages =
    document.getElementById("chatMessages");

const questionInput =
    document.getElementById("questionInput");

const sendBtn =
    document.getElementById("sendBtn");

const newChatBtn =
    document.getElementById("newChatBtn");

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

});

sendBtn.addEventListener("click", () => {

    sendMessage();

});

questionInput.addEventListener("keydown", (event) => {

    if (event.key === "Enter" && !event.shiftKey) {

        event.preventDefault();

        sendMessage();

    }

});

function sendMessage() {

    const question = questionInput.value.trim();

    if (question === "") {

        return;

    }

    addUserMessage(question);

    questionInput.value = "";

    questionInput.focus();

    showThinking();

}

function addUserMessage(message) {

    const messageDiv = document.createElement("div");

    messageDiv.className = "user-message";

    messageDiv.innerHTML = `

        <div class="bubble">

            ${message}

        </div>

        <div class="avatar">

            👤

        </div>

    `;

    chatMessages.appendChild(messageDiv);

    scrollToBottom();

}

function showThinking() {

    const thinking = document.createElement("div");

    thinking.className = "ai-message";

    thinking.id = "thinking";

    thinking.innerHTML = `

        <div class="avatar">

            🤖

        </div>

        <div class="bubble">

            Thinking...

        </div>

    `;

    chatMessages.appendChild(thinking);

    scrollToBottom();

}

function removeThinking() {

    const thinking = document.getElementById("thinking");

    if (thinking) {

        thinking.remove();

    }

}

function scrollToBottom() {

    chatMessages.scrollTop = chatMessages.scrollHeight;

}

async function sendMessage() {

    const question = questionInput.value.trim();

    if (question === "") {

        return;

    }

    addUserMessage(question);

    questionInput.value = "";

    questionInput.focus();

    showThinking();

    try {

        const response = await fetch(

            API_URL,

            {

                method: "POST",

                headers: {

                    "Content-Type": "application/json",

                    "Authorization": "Bearer " + token

                },

                body: JSON.stringify({

                    question: question,

                    subject_id: subjectId

                })

            }

        );

        if (!response.ok) {

            const error = await response.text();

            throw new Error(error);

        }

        const data = await response.json();

        removeThinking();

        addAIMessage(data.answer,data.citations);

    }

    catch (error) {

        removeThinking();

        console.error(error);

        addAIMessage(

            "❌ Unable to get response from AI."

        );

    }

}

function addAIMessage(answer, citations = []) {

    const messageDiv = document.createElement("div");

    messageDiv.className = "ai-message";

    let citationsHTML = "";

    if (citations.length > 0) {

        citationsHTML = `

            <div class="citations">

                <h4>Sources</h4>

                ${citations.map(citation => `

                    <div class="citation">

                        <strong>${citation.document}</strong>

                        <br>

                        Page ${citation.page}

                        <br>

                        <small>${citation.snippet}</small>

                    </div>

                `).join("")}

            </div>

        `;

    }

    messageDiv.innerHTML = `

        <div class="avatar">

            🤖

        </div>

        <div class="bubble">

            ${answer.replace(/\n/g, "<br>")}

            ${citationsHTML}

        </div>

    `;

    chatMessages.appendChild(messageDiv);

    scrollToBottom();

}