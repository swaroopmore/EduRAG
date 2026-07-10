const API_URL = "http://127.0.0.1:8000/documents";

const token = localStorage.getItem("token");

const uploadBtn = document.getElementById("uploadBtn");
const fileInput = document.getElementById("fileInput");

const params = new URLSearchParams(window.location.search);
const subjectId = params.get("subject_id");

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
        "📄 " + localStorage.getItem("subject_name");

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

                headers: {

                    "Authorization": "Bearer " + token

                }

            }

        );

        if (!response.ok) {

            throw new Error("Unable to load documents.");

        }

        const documents = await response.json();

        renderDocuments(documents);

    }

    catch (error) {

        console.error(error);

        alert("Unable to load documents.");

    }

}

function renderDocuments(documents) {

    const container = document.getElementById("documentsContainer");

    container.innerHTML = "";

    let pdfCount = 0;
    let totalSize = 0;

    documents.forEach(document => {

        if (document.file_type.toLowerCase() === "pdf") {

            pdfCount++;

        }

        totalSize += document.file_size;

        const row = document.createElement("tr");

        row.innerHTML = `

            <td>

                <i class="bi bi-file-earmark-pdf-fill"></i>

                ${document.original_filename}

            </td>

            <td>

                ${document.file_type.toUpperCase()}

            </td>

            <td>

                ${(document.file_size / 1024).toFixed(1)} KB

            </td>

            <td>

                ${new Date(document.created_at).toLocaleDateString()}

            </td>

            <td>

                <button class="primary">

                    Chat

                </button>

            </td>

        `;

        container.appendChild(row);

    });

    document.getElementById("totalDocuments").innerText =
        documents.length;

    document.getElementById("pdfCount").innerText =
        pdfCount;

    document.getElementById("totalSize").innerText =
        (totalSize / (1024 * 1024)).toFixed(2) + " MB";

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

        const response = await fetch(

            `${API_URL}/upload/${subjectId}`,

            {

                method: "POST",

                headers: {

                    "Authorization": "Bearer " + token

                },

                body: formData

            }

        );

        if (!response.ok) {

            throw new Error("Upload failed.");

        }

        alert("✅ Document uploaded successfully!");

        fileInput.value = "";

        await loadDocuments();

    }

    catch (error) {

        console.error(error);

        alert("❌ Upload failed.");

    }

    finally {

        uploadBtn.disabled = false;

        uploadBtn.innerHTML =
            '<i class="bi bi-cloud-upload"></i> Upload Files';

    }

}