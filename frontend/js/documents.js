const API_URL = "http://127.0.0.1:8000/documents";

const token = localStorage.getItem("access_token")

const uploadBtn = document.getElementById("uploadBtn");
const fileInput = document.getElementById("fileInput");

const params = new URLSearchParams(window.location.search);

const subjectId =
    params.get("subject_id") ||
    localStorage.getItem("current_subject_id");

console.log("Subject ID:", subjectId);

window.addEventListener("DOMContentLoaded", () => {

    if (!token) {

        window.location.href = "login.html";
        return;

    }

    if (!subjectId) {

        alert("No subject selected.");
        return;

    }

    document.getElementById("subjectTitle").innerText =
        "📄 " + localStorage.getItem("current_subject_name");

    loadDocuments();

});

uploadBtn.addEventListener("click", () => {

    fileInput.click();

});

fileInput.addEventListener("change", uploadDocument);

async function loadDocuments() {

    try {

        const response = await fetch(

            `${API_URL}/${subjectId}`,

            {

                method: "GET",

                headers: {

                    "Authorization": "Bearer " + token

                }

            }

        );

        if (!response.ok) {

            const error = await response.text();

            console.error(error);

            throw new Error(error);

        }

        const documents = await response.json();

        console.log("Documents:", documents);

        renderDocuments(documents);

    }

    catch (error) {

        console.error(error);

        alert(error.message);

    }

}


function renderDocuments(documents) {

    const container = document.getElementById("documentsContainer");

    container.innerHTML = "";

    let pdfCount = 0;
    let totalSize = 0;

    if (documents.length === 0) {

        container.innerHTML = `

            <div class="empty-state">

                <i class="bi bi-folder2-open"></i>

                <h2>No Documents Found</h2>

                <p>Upload your first PDF to start learning with AI.</p>

            </div>

        `;

    }

    documents.forEach(doc => {

        if (doc.file_type.toLowerCase() === "pdf") {

            pdfCount++;

        }

        totalSize += doc.file_size;

        const card = document.createElement("div");

        card.className = "document-card";

        card.innerHTML = `

            <div class="document-icon">

                <i class="bi bi-file-earmark-pdf-fill"></i>

            </div>

            <h3>${doc.original_filename}</h3>

            <div class="document-meta">

                <p><strong>Type:</strong> ${doc.file_type.toUpperCase()}</p>

                <p><strong>Size:</strong> ${(doc.file_size / 1024).toFixed(1)} KB</p>

                <p><strong>Uploaded:</strong> ${new Date(doc.created_at).toLocaleDateString()}</p>

            </div>

            <div class="document-actions">

                <button onclick="openChat()">
                    AI Chat
                </button>

                <button onclick="openFlashcards()">
                    Flashcards
                </button>

                <button onclick="openQuiz()">
                    Quiz
                </button>

                <button onclick="openNotes()">
                    Notes
                </button>

                <button onclick="openStudyPlanner()">
                    Planner
                </button>

            </div>

        `;

        container.appendChild(card);

    });

    document.getElementById("documentCount").innerText =
        documents.length;

}

async function uploadDocument() {

    if (fileInput.files.length === 0) {

        return;

    }

    const file = fileInput.files[0];

    const formData = new FormData();

    formData.append("file", file);

    try {

        uploadBtn.disabled = true;

        uploadBtn.innerHTML =
            '<i class="bi bi-arrow-repeat"></i> Uploading...';

        console.log("Uploading:", file.name);

        const response = await fetch(

            `${API_URL}/upload/${subjectId}`,

            {

                method: "POST",

                headers: {

                    Authorization: `Bearer ${token}`

                },

                body: formData

            }

        );

        console.log("Status Code:", response.status);

        const responseText = await response.text();

        console.log("Response:", responseText);

        if (!response.ok) {

            throw new Error(responseText);

        }

        alert("✅ Document uploaded successfully!");

        fileInput.value = "";

        await loadDocuments();

    }

    catch (error) {

        console.error("Upload Error:", error);

        alert(error.message);

    }

    finally {

        uploadBtn.disabled = false;

        uploadBtn.innerHTML =
            '<i class="bi bi-cloud-upload"></i> Upload Files';

    }

}

function openChat() {

    window.location.href =

        `chat.html?subject_id=${subjectId}`;

}

function openFlashcards() {

    window.location.href =

        `flashcards.html?subject_id=${subjectId}`;

}

function openQuiz() {

    window.location.href =
        `quizes.html?subject_id=${subjectId}`;

}

function openNotes() {

    window.location.href =
        `notes.html?subject_id=${subjectId}`;

}

function openStudyPlanner() {

    window.location.href =
        `studyplanner.html?subject_id=${subjectId}`;

}