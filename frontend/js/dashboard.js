/* ============================================
   EduRAG Dashboard
============================================ */

const API_BASE =

    "http://127.0.0.1:8000";

const token =

    localStorage.getItem(
        "token"
    );

if (!token) {

    window.location.href =

        "login.html";

}

const userName =

    localStorage.getItem(
        "user_name"
    ) || "Student";

const profileName =

    document.getElementById(
        "profileName"
    );

const dashboardName =

    document.getElementById(
        "userName"
    );

const avatar =

    document.getElementById(
        "profileAvatar"
    );

profileName.innerText =

    userName;

dashboardName.innerText =

    userName;

avatar.innerText =

    userName

        .split(" ")

        .map(

            word =>

                word[0]

        )

        .join("");

const greetingText =

    document.getElementById(
        "greetingText"
    );

const hour =

    new Date().getHours();

if (hour < 12) {

    greetingText.innerHTML =

        "Good Morning 👋";

}

else if (hour < 17) {

    greetingText.innerHTML =

        "Good Afternoon 👋";

}

else {

    greetingText.innerHTML =

        "Good Evening 👋";

}

let subjects = [];

let documents = [];

let activities = [];

init();

async function init() {

    console.log(

        "Dashboard Loaded"

    );
    await loadDashboard();
    await loadSubjects();
      await loadRecentDocuments();
       loadRecentActivity();

}

/* ============================================
   Load Dashboard Statistics
============================================ */

async function loadStatistics() {

    try {

        const response = await fetch(

            `${API_BASE}/subjects`,

            {

                headers: {

                    Authorization:

                        "Bearer " + token

                }

            }

        );

        if (!response.ok) {

            throw new Error(

                "Unable to load subjects."

            );

        }

        subjects =

            await response.json();

        document.getElementById(

            "subjectsCount"

        ).innerText =

            subjects.length;

        document.getElementById(

            "documentsCount"

        ).innerText =

            subjects.reduce(

                (

                    total,

                    subject

                ) =>

                    total +

                    (

                        subject.document_count ||

                        0

                    ),

                0

            );

    }

    catch (error) {

        console.error(

            error

        );

    }

}

/* ============================================
   Dashboard Statistics
============================================ */
async function loadDashboard() {

    try {

        const response = await fetch(

            `${API_BASE}/dashboard`,

            {

                headers: {

                    Authorization:

                        `Bearer ${token}`

                }

            }

        );

        if (!response.ok) {

            throw new Error(

                "Failed to load dashboard."

            );

        }

        const data =

            await response.json();

        document.getElementById(

            "subjectsCount"

        ).innerText =

            data.subjects;

        document.getElementById(

            "documentsCount"

        ).innerText =

            data.documents;

        document.getElementById(

            "flashcardsCount"

        ).innerText =

            data.flashcards;

        document.getElementById(

            "quizCount"

        ).innerText =

            data.quizzes;

        document.getElementById(

            "notesCount"

        ).innerText =

            data.notes;

        document.getElementById(

            "plannerCount"

        ).innerText =

            data.study_plans;

        document.getElementById(

            "storageUsed"

        ).innerText =

            data.storage_used + " MB";

        /* Storage Progress */

        const storagePercent =

            Math.min(

                (data.storage_used / 1024) * 100,

                100

            );

        document.getElementById(

            "storageProgress"

        ).style.width =

            storagePercent + "%";

        /* Placeholder */

        document.getElementById(

            "chatCount"

        ).innerText =

            "0";

    }

    catch (error) {

        console.error(

            "Dashboard Error:",

            error

        );

    }

}


/* ============================================
   Load Subjects
============================================ */

async function loadSubjects() {

    try {

        const response = await fetch(

            `${API_BASE}/subjects`,

            {

                headers: {

                    Authorization:
                        `Bearer ${token}`

                }

            }

        );

        if (!response.ok) {

            throw new Error(

                "Failed to load subjects."

            );

        }

        const subjects =
            await response.json();

        renderSubjects(subjects);
        renderContinueLearning(subjects);

    }

    catch (error) {

        console.error(error);

    }

}

function renderSubjects(subjects) {

    const container =

        document.getElementById(

            "subjectsContainer"

        );

    container.innerHTML = "";

    if (subjects.length === 0) {

        container.innerHTML = `

            <div class="empty-state">

                <i class="bi bi-book"></i>

                <h3>

                    No Subjects Yet

                </h3>

                <p>

                    Create your first subject to start learning.

                </p>

            </div>

        `;

        return;

    }

    subjects.forEach(subject => {

        const card =

            document.createElement("div");

        card.className =

            "subject-card";

        card.innerHTML = `

            <div class="subject-top">

                <div class="subject-icon">

                    <i class="bi bi-book"></i>

                </div>

            </div>

            <h3>

                ${subject.name}

            </h3>

            <p>

                ${subject.description ?? "No description"}

            </p>

            <button

                class="subject-btn"

                onclick="openSubject('${subject.id}')">

                Open

            </button>

        `;

        container.appendChild(card);

    });

}

function openSubject(subjectId) {

    window.location.href =

        `documents.html?subject_id=${subjectId}`;

}

/* ============================================
   Recent Documents
============================================ */

async function loadRecentDocuments() {

    try {

        const response = await fetch(

            `${API_BASE}/documents`,

            {

                headers: {

                    Authorization:

                        `Bearer ${token}`

                }

            }

        );

        if (!response.ok) {

            throw new Error(

                "Unable to load documents."

            );

        }

        const documents =

            await response.json();

        renderRecentDocuments(documents);

    }

    catch (error) {

        console.error(error);

    }

}

function renderRecentDocuments(documents) {

    const container =

        document.getElementById(

            "recentDocuments"

        );

    container.innerHTML = "";

    if (documents.length === 0) {

        container.innerHTML = `

            <div class="empty-state">

                <i class="bi bi-file-earmark"></i>

                <h3>

                    No Documents Uploaded

                </h3>

                <p>

                    Upload your first PDF to begin learning.

                </p>

            </div>

        `;

        return;

    }

    documents

        .sort(

            (a, b) =>

                new Date(b.created_at)

                -

                new Date(a.created_at)

        )

        .slice(0, 5)

        .forEach(doc => {

            const item =

                document.createElement("div");

            item.className =

                "recent-document";

            item.innerHTML = `

                <div class="doc-left">

                    <i class="bi bi-file-earmark-pdf-fill"></i>

                    <div>

                        <h4>

                            ${doc.original_filename}

                        </h4>

                        <span>

                            ${(doc.file_size / 1024).toFixed(1)} KB

                        </span>

                    </div>

                </div>

                <div class="doc-right">

                    ${new Date(

                        doc.created_at

                    ).toLocaleDateString()}

                </div>

            `;

            container.appendChild(item);

        });

}

/* ============================================
   Continue Learning
============================================ */

function renderContinueLearning(subjects) {

    if (!subjects || subjects.length === 0) {

        document.getElementById(

            "continueSubject"

        ).innerText =

            "No Subject Available";

        document.getElementById(

            "continueTime"

        ).innerText =

            "Create your first subject to begin learning.";

        document.getElementById(

            "documentCount"

        ).innerText =

            "0 Documents";

        document.getElementById(

            "learningProgress"

        ).style.width =

            "0%";

        return;

    }

    const latest = subjects[0];

    document.getElementById(

        "continueSubject"

    ).innerText =

        latest.name;

    document.getElementById(

        "continueTime"

    ).innerText =

        latest.description ||

        "Continue learning this subject with AI.";

    document.getElementById(

        "documentCount"

    ).innerText =

        "Ready to Study";

    document.getElementById(

        "continueBtn"

    ).dataset.subjectId =

        latest.id;

    setTimeout(

        () => {

            document.getElementById(

                "learningProgress"

            ).style.width =

                "20%";

        },

        300

    );

}

/* ============================================
   Recent Activity
============================================ */

function loadRecentActivity() {

    const container =

        document.getElementById(

            "activityContainer"

        );

    container.innerHTML =

        "";

    const activities = [

        {

            icon:

                "bi-book",

            title:

                "Subject Created",

            text:

                "Created a new learning subject."

        },

        {

            icon:

                "bi-file-earmark-pdf",

            title:

                "Document Uploaded",

            text:

                "Uploaded a new PDF."

        },

        {

            icon:

                "bi-stars",

            title:

                "AI Ready",

            text:

                "Start chatting with your documents."

        }

    ];

    activities.forEach(activity => {

        const item =

            document.createElement(

                "div"

            );

        item.className =

            "activity-item";

        item.innerHTML = `

            <div class="activity-icon">

                <i class="bi ${activity.icon}"></i>

            </div>

            <div class="activity-info">

                <h4>

                    ${activity.title}

                </h4>

                <p>

                    ${activity.text}

                </p>

            </div>

        `;

        container.appendChild(

            item

        );

    });

}

/* ============================================
   Navigation Buttons
============================================ */

document

    .getElementById(

        "newSubjectBtn"

    )

    .addEventListener(

        "click",

        () => {

            window.location.href =

                "subjects.html";

        }

    );


document

    .getElementById(

        "uploadBtn"

    )

    .addEventListener(

        "click",

        () => {

            window.location.href =

                "documents.html";

        }

    );


document

    .getElementById(

        "chatBtn"

    )

    .addEventListener(

        "click",

        () => {

            window.location.href =

                "chat.html";

        }

    );


document

    .getElementById(

        "continueBtn"

    )

    .addEventListener(

        "click",

        () => {

            window.location.href =

                "documents.html";

        }

    );

    /* ============================================
   Quick Access
============================================ */

document

    .getElementById(

        "quickChat"

    )

    .onclick = () =>

        window.location.href =

            "chat.html";


document

    .getElementById(

        "quickFlashcards"

    )

    .onclick = () =>

        window.location.href =

            "flashcards.html";


document

    .getElementById(

        "quickQuiz"

    )

    .onclick = () =>

        window.location.href =

            "quizes.html";


document

    .getElementById(

        "quickNotes"

    )

    .onclick = () =>

        window.location.href =

            "notes.html";


document

    .getElementById(

        "quickPlanner"

    )

    .onclick = () =>

        window.location.href =

            "studyplanner.html";

            /* ============================================
   Logout
============================================ */

document

    .getElementById(

        "logoutBtn"

    )

    .addEventListener(

        "click",

        () => {

            localStorage.removeItem(

                "token"

            );

            localStorage.removeItem(

                "user_name"

            );

            window.location.href =

                "login.html";

        }

    );

    /* ============================================
   Daily Motivation
============================================ */

const quotes = [

    "Success is the sum of small efforts repeated every day.",

    "Consistency beats motivation.",

    "Learn something today your future self will thank you for.",

    "Small progress every day adds up to big results.",

    "Discipline creates opportunities."

];

document

    .getElementById(

        "dailyQuote"

    )

    .innerText =

        quotes[

            Math.floor(

                Math.random()

                * quotes.length

            )

        ];

        /* ============================================
   Theme Toggle
============================================ */

const themeToggle =

    document.getElementById(

        "themeToggle"

    );

const themeIcon =

    document.getElementById(

        "themeIcon"

    );

themeToggle.addEventListener(

    "click",

    () => {

        document.body.classList.toggle(

            "dark"

        );

        if (

            document.body.classList.contains(

                "dark"

            )

        ) {

            themeIcon.className =

                "bi bi-sun";

        }

        else {

            themeIcon.className =

                "bi bi-moon";

        }

    }

);