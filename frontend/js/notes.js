const API_URL =
    "http://127.0.0.1:8000/notes";

const token =
    localStorage.getItem("access_token");

const params =
    new URLSearchParams(
        window.location.search
    );

const subjectId =
    params.get("subject_id");

const subjectName =
    localStorage.getItem(
        "current_subject_name"
    );

document.getElementById(
    "subjectTitle"
).innerText =
    `${subjectName} Notes`;

let notes = [];

async function init() {

    if (!subjectId) {

        alert(
            "Subject not found."
        );

        return;

    }

    await loadNotes();

}

init();

async function loadNotes() {

    try {

        const response = await fetch(

            `${API_URL}/${subjectId}`,

            {

                headers: {

                    Authorization:

                        "Bearer " + token

                }

            }

        );

        if (!response.ok) {

            throw new Error(
                "Unable to load notes."
            );

        }

        notes = await response.json();

        if (notes.length === 0) {

            document.getElementById(

                "notesContainer"

            ).innerHTML = `

                <div class="empty-state">

                    <i class="bi bi-journal-richtext"></i>

                    <h2>No Notes Available</h2>

                    <p>

                        Click <strong>Generate Notes</strong>
                        to create AI study notes.

                    </p>

                </div>

            `;

            document.getElementById(
                "tocContainer"
            ).innerHTML =
                "<p>No sections yet.</p>";

            updateStatistics();

            return;

        }

        renderNotes();

        renderTableOfContents();

        updateStatistics();

    }

    catch (error) {

        console.error(error);

        alert(
            "Unable to load notes."
        );

    }

}

function updateStatistics() {

    document.getElementById("totalNotes").innerText =
        notes.length;

    document.getElementById("sectionCount").innerText =
        notes.length;

    let words = 0;

    notes.forEach(note => {

        words += note.content
            .split(/\s+/)
            .length;

    });

    const minutes =
        Math.max(1, Math.ceil(words / 200));

    document.getElementById("readingTime").innerText =
        `${minutes} min`;

    document.getElementById("keywordCount").innerText =
        words;

}

function renderNotes() {

    const container =

        document.getElementById(

            "notesContainer"

        );

    container.innerHTML = "";

    notes.forEach(

        (note, index) => {

            container.innerHTML += `

                <div
                    class="note-card"
                    id="note-${index}">

                    <div
                        class="note-header"
                        onclick="toggleNote(${index})">

                        <h2>

                            ${note.title}

                        </h2>

                        <i
                            id="icon-${index}"
                            class="bi bi-chevron-down">

                        </i>

                    </div>

                    <div
                        id="content-${index}"
                        class="note-content">

                        <p>

                            ${note.content}

                        </p>

                    </div>

                </div>

            `;

        }

    );

}

function toggleNote(
    index
) {

    const content =

        document.getElementById(

            `content-${index}`

        );

    const icon =

        document.getElementById(

            `icon-${index}`

        );

    if (

        content.style.display === "none"

    ) {

        content.style.display = "block";

        icon.className =

            "bi bi-chevron-up";

    }

    else {

        content.style.display = "none";

        icon.className =

            "bi bi-chevron-down";

    }

}
async function generateNotes() {

    try {

        const button =
            document.getElementById(
                "generateBtn"
            );

        button.disabled = true;

        button.innerHTML =
            '<i class="bi bi-arrow-repeat spin"></i> Generating...';

        document.getElementById(
            "notesContainer"
        ).innerHTML = `

            <div class="loading-card">

                <h2>Generating Notes...</h2>

                <p>

                    AI is preparing your notes.

                </p>

            </div>

        `;

        const response = await fetch(

            `${API_URL}/generate/${subjectId}`,

            {

                method: "POST",

                headers: {

                    Authorization:
                        "Bearer " + token

                }

            }

        );

        if (!response.ok) {

            throw new Error(
                "Failed to generate notes."
            );

        }

        await loadNotes();

    }

    catch (error) {

        console.error(error);

        alert(
            "Unable to generate notes."
        );

    }

    finally {

        const button =
            document.getElementById(
                "generateBtn"
            );

        button.disabled = false;

        button.innerHTML =
            '<i class="bi bi-stars"></i> Generate Notes';

    }

}

function renderTableOfContents() {

    const toc =
        document.getElementById(
            "tocContainer"
        );

    toc.innerHTML = "";

    notes.forEach(

        (note, index) => {

            toc.innerHTML += `

                <a
                    href="#note-${index}"
                    class="toc-item">

                    ${note.title}

                </a>

            `;

        }

    );

}

document

    .getElementById(
        "searchNotes"
    )

    .addEventListener(

        "input",

        function () {

            const keyword =

                this.value
                    .toLowerCase();

            const cards =

                document.querySelectorAll(
                    ".note-card"
                );

            cards.forEach(

                card => {

                    const text =

                        card.innerText
                            .toLowerCase();

                    card.style.display =

                        text.includes(keyword)

                        ? "block"

                        : "none";

                }

            );

        }

    );

    document

    .getElementById(
        "generateBtn"
    )

    .addEventListener(

        "click",

        generateNotes

    );


    document
.getElementById("copyBtn")
.addEventListener("click", () => {

    const text = notes
        .map(note =>
            `${note.title}\n\n${note.content}`)
        .join("\n\n");

    navigator.clipboard.writeText(text);

    alert("Notes copied successfully.");

});

document
.getElementById("regenerateBtn")
.addEventListener(
    "click",
    generateNotes
);

document
.getElementById("regenerateCard")
.addEventListener(
    "click",
    generateNotes
);

document
.getElementById("copyNotesCard")
.addEventListener("click", () => {

    document
        .getElementById("copyBtn")
        .click();

});

document
.getElementById("downloadPdfCard")
.addEventListener("click", () => {

    alert("PDF download coming soon.");

});

    window.addEventListener("scroll", () => {

    const scrollTop =
        window.scrollY;

    const docHeight =
        document.documentElement.scrollHeight -
        window.innerHeight;

    const progress =
        docHeight === 0
        ? 0
        : Math.round((scrollTop / docHeight) * 100);

    document.getElementById("progressFill").style.width =
        progress + "%";

    document.getElementById("progressText").innerText =
        progress + "%";

});