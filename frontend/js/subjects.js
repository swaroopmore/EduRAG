const API_URL = "http://127.0.0.1:8000/subjects";

const token = localStorage.getItem("access_token");

const container = document.getElementById("subjectsContainer");

const modal = document.getElementById("subjectModal");

const addSubjectBtn = document.getElementById("addSubjectBtn");

const closeModalBtn = document.getElementById("closeModal");

const saveSubjectBtn = document.getElementById("saveSubject");

console.log("Token:", token);

console.log(addSubjectBtn);
console.log(modal);
console.log(closeModalBtn);

window.addEventListener("DOMContentLoaded", () => {

    loadSubjects();

});

async function loadSubjects() {

    try {

        const response = await fetch(API_URL, {

            headers: {

                "Authorization": "Bearer " + token

            }

        });

        if (!response.ok) {

            throw new Error("Unable to load subjects.");

        }

        const subjects = await response.json();

        renderSubjects(subjects);

    }

    catch (error) {

        console.error(error);

        alert("Failed to load subjects.");

    }

}

function renderSubjects(subjects) {

    container.innerHTML = "";

    document.getElementById("totalSubjects").innerText = subjects.length;

    subjects.forEach(subject => {

    const card = document.createElement("div");

    card.className = "subject-card";

   
    card.innerHTML = `
<div class="icon">
    <i class="bi bi-book"></i>
</div>

<h3>${subject.name}</h3>

<p>${subject.description ?? "No description available."}</p>

<small>
Created: ${new Date(subject.created_at).toLocaleDateString()}
</small>

<div class="subject-footer">

    <span>
        <i class="bi bi-file-earmark-text"></i>
        Open Workspace
    </span>

    <i class="bi bi-arrow-right-circle-fill"></i>

</div>
`;

    card.style.cursor = "pointer";

    card.addEventListener("click", () => {

        localStorage.setItem("current_subject_id", subject.id);
        localStorage.setItem("current_subject_name", subject.name);

        window.location.href =
            "documents.html?subject_id=" + subject.id;

    });

    container.appendChild(card);

});

}

addSubjectBtn.addEventListener("click", () => {

    console.log("Button Clicked");

    console.log(modal.className);

    modal.classList.remove("hidden");

    console.log(modal.className);

});

closeModalBtn.addEventListener("click", () => {

    modal.classList.add("hidden");

});

saveSubjectBtn.addEventListener("click", createSubject);

async function createSubject() {

    const name = document
        .getElementById("subjectName")
        .value
        .trim();

    const description = document
        .getElementById("subjectDescription")
        .value
        .trim();

    if (!name) {

        alert("Please enter a subject name.");

        return;

    }

    try {

        const response = await fetch(API_URL, {

            method: "POST",

            headers: {

                "Content-Type": "application/json",

                "Authorization": "Bearer " + token

            },

            body: JSON.stringify({

                name: name,

                description: description

            })

        });

        const data = await response.json();

        if (!response.ok) {

            alert(data.detail || "Unable to create subject.");

            return;

        }

        document.getElementById("subjectName").value = "";

        document.getElementById("subjectDescription").value = "";

        modal.classList.add("hidden");

        await loadSubjects();

    }

    catch (error) {

        console.error(error);

        alert("Unable to connect to the server.");

    }

}

window.addEventListener("click", (event) => {

    if (event.target === modal) {

        modal.classList.add("hidden");

    }

});

console.log