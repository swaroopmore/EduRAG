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

    const container =
        document.getElementById("documentsContainer");

    container.innerHTML = "";

    let pdfCount = 0;

    let totalSize = 0;

    documents.forEach(doc => {

        if (doc.file_type.toLowerCase() === "pdf") {

            pdfCount++;

        }

        totalSize += doc.file_size;

        const row = document.createElement("tr");

        row.innerHTML = `

            <td>

                <i class="bi bi-file-earmark-pdf-fill"></i>

                ${doc.original_filename}

            </td>

            <td>

                ${doc.file_type.toUpperCase()}

            </td>

            <td>

                ${(doc.file_size / 1024).toFixed(1)} KB

            </td>

            <td>

                ${new Date(doc.created_at).toLocaleDateString()}

            </td>

          <td>

    <button
        class="primary chat-btn"
        data-subject="${subjectId}"
        data-document="${doc.id}"
    >

        AI Chat

    </button>

</td>

        `;

        container.appendChild(row);
        const chatBtn = row.querySelector(".chat-btn");

chatBtn.addEventListener("click", () => {

    localStorage.setItem("subject_id", subjectId);

    localStorage.setItem(
        "document_id",
        doc.id
    );

    localStorage.setItem(
        "document_name",
        doc.original_filename
    );

    window.location.href =
        `chat.html?subject_id=${subjectId}&document_id=${doc.id}`;

});

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