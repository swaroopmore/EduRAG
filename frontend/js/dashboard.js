/* =====================================================
   EduRAG Dashboard
   Part 1
   Constants • Authentication • Initialization
===================================================== */


/* =====================================================
   API Configuration
===================================================== */

const API_BASE = "http://127.0.0.1:8000";


/* =====================================================
   Authentication
===================================================== */

const token = localStorage.getItem("access_token");

if (!token) {

    window.location.href = "login.html";

}



/* =====================================================
   DOM Elements
===================================================== */

const userName =
    document.getElementById("userName");

const greetingText =
    document.getElementById("greetingText");

const footerYear =
    document.getElementById("footerYear");

const logoutBtn =
    document.getElementById("logoutBtn");

const dashboardSearch =
    document.getElementById("dashboardSearch");



/* =====================================================
   Dashboard Cards
===================================================== */

const subjectsCount =
    document.getElementById("subjectsCount");

const documentsCount =
    document.getElementById("documentsCount");

const flashcardsCount =
    document.getElementById("flashcardsCount");

const quizCount =
    document.getElementById("quizCount");

const notesCount =
    document.getElementById("notesCount");

const plannerCount =
    document.getElementById("plannerCount");

const storageUsed =
    document.getElementById("storageUsed");



/* =====================================================
   Continue Learning
===================================================== */

const continueSubject =
    document.getElementById("continueSubject");

const continueTime =
    document.getElementById("continueTime");

const documentCount =
    document.getElementById("documentCount");

const learningProgress =
    document.getElementById("learningProgress");



/* =====================================================
   Containers
===================================================== */

const subjectGrid =
    document.getElementById("subjectGrid");

const documentsContainer =
    document.getElementById("documentsContainer");

const recentActivity =
    document.getElementById("recentActivity");



/* =====================================================
   Greeting
===================================================== */

function setGreeting() {

    const hour =
        new Date().getHours();

    if (hour < 12) {

        greetingText.textContent =
            "🌅 Good Morning";

    }

    else if (hour < 17) {

        greetingText.textContent =
            "☀️ Good Afternoon";

    }

    else {

        greetingText.textContent =
            "🌙 Good Evening";

    }

}



/* =====================================================
   Footer
===================================================== */

function setFooterYear() {

    footerYear.textContent =
        new Date().getFullYear();

}



/* =====================================================
   Logout
===================================================== */

function logout() {

    localStorage.removeItem(
        "access_token"
    );

    window.location.href =
        "login.html";

}

logoutBtn.addEventListener(

    "click",

    logout

);



/* =====================================================
   API Helper
===================================================== */

async function apiRequest(endpoint) {

    const response = await fetch(

        `${API_BASE}${endpoint}`,

        {

            headers: {

                Authorization:

                    `Bearer ${token}`

            }

        }

    );

    if (!response.ok) {

        throw new Error(

            `API Error : ${response.status}`

        );

    }

    return await response.json();

}



/* =====================================================
   Initialization
===================================================== */

async function init() {

    console.log(

        "EduRAG Dashboard Loaded"

    );

    setGreeting();

    setFooterYear();

    await loadInitialData();

}

document.addEventListener(

    "DOMContentLoaded",

    init

);
/* =====================================================
   Dashboard Data
===================================================== */

let dashboardData = {};

let subjects = [];



/* =====================================================
   Load Logged-in User
===================================================== */

async function loadCurrentUser() {

    try {

        const user = await apiRequest(

            "/auth/me"

        );

        userName.textContent =

            user.full_name ||

            user.name ||

            "Student";

    }

    catch (error) {

        console.error(

            "Unable to load user.",

            error

        );

    }

}



/* =====================================================
   Load Dashboard Statistics
===================================================== */

async function loadDashboard() {

    try {

        dashboardData =

            await apiRequest(

                "/dashboard"

            );



        subjectsCount.textContent =

            dashboardData.subjects;



        documentsCount.textContent =

            dashboardData.documents;



        flashcardsCount.textContent =

            dashboardData.flashcards;



        quizCount.textContent =

            dashboardData.quizzes;



        notesCount.textContent =

            dashboardData.notes;



        plannerCount.textContent =

            dashboardData.study_plans;



        storageUsed.textContent =

            dashboardData.storage_used +

            " MB";



        animateStorageBar();



    }

    catch (error) {

        console.error(

            "Unable to load dashboard.",

            error

        );

    }

}



/* =====================================================
   Storage Progress
===================================================== */

function animateStorageBar() {

    const bar =

        document.getElementById(

            "storageProgress"

        );

    if (!bar) return;



    const storage =

        dashboardData.storage_used || 0;



    const percent =

        Math.min(

            (storage / 1024) * 100,

            100

        );



    bar.style.width =

        percent + "%";

}



/* =====================================================
   Continue Learning
===================================================== */

function renderContinueLearning() {

    if (

        subjects.length === 0

    ) {

        continueSubject.textContent =

            "No Subjects Yet";



        continueTime.textContent =

            "Create your first subject to begin learning.";



        documentCount.textContent =

            "0 Documents";



        learningProgress.style.width =

            "0%";



        return;

    }



    const latest =

        subjects[0];



    continueSubject.textContent =

        latest.name;



    continueTime.textContent =

        latest.description ||

        "Continue learning this subject.";



    documentCount.textContent =

        "Ready to Study";



    learningProgress.style.width =

        "25%";

}



/* =====================================================
   Load Dashboard
===================================================== */

async function loadInitialData() {

    await Promise.all([

        loadCurrentUser(),

        loadDashboard(),
         loadSubjects(),
         loadRecentDocuments()

    ]);

}

/* =====================================================
   Load Subjects
===================================================== */

async function loadSubjects() {

    try {

        subjects = await apiRequest(

            "/subjects"

        );

        renderSubjects();

        renderContinueLearning();

    }

    catch (error) {

        console.error(

            "Unable to load subjects.",

            error

        );

    }

}



/* =====================================================
   Render Subject Cards
===================================================== */

function renderSubjects() {

    if (!subjectGrid) return;

    subjectGrid.innerHTML = "";



    if (subjects.length === 0) {

        subjectGrid.innerHTML = `

            <div class="empty-state">

                <i class="bi bi-book"></i>

                <h3>No Subjects Found</h3>

                <p>

                    Create your first subject to start learning.

                </p>

            </div>

        `;

        return;

    }



    subjects.forEach(subject => {

        const card = document.createElement(

            "div"

        );



        card.className =

            "subject-card";



        card.innerHTML = `

            <h3>

                ${subject.name}

            </h3>

            <p>

                ${subject.description || "No description available."}

            </p>

            <button

                class="primary-btn open-subject"

                data-id="${subject.id}"

            >

                Open Subject

            </button>

        `;



        subjectGrid.appendChild(

            card

        );

    });



    attachSubjectEvents();

}



/* =====================================================
   Subject Events
===================================================== */

function attachSubjectEvents() {

    document

        .querySelectorAll(

            ".open-subject"

        )

        .forEach(button => {

            button.addEventListener(

                "click",

                function () {

                    const subjectId =

                        this.dataset.id;



                    localStorage.setItem(

                        "current_subject",

                        subjectId

                    );



                    window.location.href =

                        "documents.html";

                }

            );

        });

}



/* =====================================================
   Subject Search
===================================================== */

if (dashboardSearch) {

    dashboardSearch.addEventListener(

        "input",

        function () {

            const keyword =

                this.value

                .trim()

                .toLowerCase();



            const cards =

                document.querySelectorAll(

                    ".subject-card"

                );



            cards.forEach(card => {

                const title =

                    card.querySelector("h3")

                        .textContent

                        .toLowerCase();



                if (

                    title.includes(keyword)

                ) {

                    card.style.display =

                        "block";

                }

                else {

                    card.style.display =

                        "none";

                }

            });

        }

    );

}



/* =====================================================
   Continue Learning Button
===================================================== */

const continueBtn =

    document.getElementById(

        "continueBtn"

    );



if (continueBtn) {

    continueBtn.addEventListener(

        "click",

        () => {

            if (

                subjects.length === 0

            ) {

                window.location.href =

                    "subjects.html";

                return;

            }



            localStorage.setItem(

                "current_subject",

                subjects[0].id

            );



            window.location.href =

                "documents.html";

        }

    );

}

/* =====================================================
   Load Recent Documents
===================================================== */

async function loadRecentDocuments() {

    try {

        const documents = await apiRequest(

            "/documents"

        );

        renderRecentDocuments(

            documents

        );

        renderRecentActivity(

            documents

        );

    }

    catch (error) {

        console.error(

            "Unable to load documents.",

            error

        );

    }

}



/* =====================================================
   Render Documents
===================================================== */

function renderRecentDocuments(

    documents

) {

    if (!documentsContainer) return;

    documentsContainer.innerHTML = "";



    if (documents.length === 0) {

        documentsContainer.innerHTML = `

            <tr>

                <td colspan="5">

                    No documents uploaded.

                </td>

            </tr>

        `;

        return;

    }



    documents

        .slice(0,5)

        .forEach(document => {

            const row =

                document.createElement("tr");



            row.innerHTML = `

                <td>

                    <i class="bi bi-file-earmark-pdf-fill"></i>

                    ${document.original_filename}

                </td>

                <td>

                    ${document.file_type}

                </td>

                <td>

                    ${formatFileSize(

                        document.file_size

                    )}

                </td>

                <td>

                    ${formatDate(

                        document.created_at

                    )}

                </td>

                <td>

                    <button

                        class="secondary"

                    >

                        View

                    </button>

                </td>

            `;



            documentsContainer.appendChild(

                row

            );

        });

}



/* =====================================================
   Recent Activity
===================================================== */

function renderRecentActivity(

    documents

) {

    if (!recentActivity) return;

    recentActivity.innerHTML = "";



    if (documents.length === 0) {

        recentActivity.innerHTML = `

            <p>

                No recent activity.

            </p>

        `;

        return;

    }



    documents

        .slice(0,5)

        .forEach(document => {

            const item =

                document.createElement(

                    "div"

                );



            item.className =

                "activity-item";



            item.innerHTML = `

                <div class="activity-icon">

                    <i class="bi bi-upload"></i>

                </div>

                <div class="activity-content">

                    <h4>

                        Uploaded

                        ${document.original_filename}

                    </h4>

                    <p>

                        ${formatDate(

                            document.created_at

                        )}

                    </p>

                </div>

            `;



            recentActivity.appendChild(

                item

            );

        });

}



/* =====================================================
   Helpers
===================================================== */

function formatFileSize(

    bytes

) {

    if (bytes < 1024)

        return bytes + " B";



    if (bytes < 1024 * 1024)

        return (

            (bytes / 1024)

            .toFixed(1)

            + " KB"

        );



    return (

        (bytes /

        (1024 * 1024))

        .toFixed(2)

        + " MB"

    );

}



function formatDate(

    date

) {

    return new Date(

        date

    ).toLocaleDateString(

        "en-IN",

        {

            day:"numeric",

            month:"short",

            year:"numeric"

        }

    );

}

/* =====================================================
   Quick Actions
===================================================== */

const quickChat =
    document.getElementById("quickChat");

const quickFlashcards =
    document.getElementById("quickFlashcards");

const quickQuiz =
    document.getElementById("quickQuiz");

const quickNotes =
    document.getElementById("quickNotes");

const quickPlanner =
    document.getElementById("quickPlanner");

const uploadBtn =
    document.getElementById("uploadBtn");

const newSubjectBtn =
    document.getElementById("newSubjectBtn");

const chatBtn =
    document.getElementById("chatBtn");



/* =====================================================
   Navigation Helpers
===================================================== */

function navigate(page) {

    window.location.href = page;

}



/* =====================================================
   Register Events
===================================================== */

function registerEvents() {

    if (quickChat)

        quickChat.addEventListener(

            "click",

            () => navigate("chat.html")

        );



    if (chatBtn)

        chatBtn.addEventListener(

            "click",

            () => navigate("chat.html")

        );



    if (quickFlashcards)

        quickFlashcards.addEventListener(

            "click",

            () => navigate("flashcards.html")

        );



    if (quickQuiz)

        quickQuiz.addEventListener(

            "click",

            () => navigate("quizzes.html")

        );



    if (quickNotes)

        quickNotes.addEventListener(

            "click",

            () => navigate("notes.html")

        );



    if (quickPlanner)

        quickPlanner.addEventListener(

            "click",

            () => navigate("studyplanner.html")

        );



    if (uploadBtn)

        uploadBtn.addEventListener(

            "click",

            () => navigate("documents.html")

        );



    if (newSubjectBtn)

        newSubjectBtn.addEventListener(

            "click",

            () => navigate("subjects.html")

        );

}



/* =====================================================
   Notification Placeholder
===================================================== */

function loadNotifications() {

    console.log(

        "Notification module ready."

    );

}



/* =====================================================
   Loading
===================================================== */

function showLoading() {

    document.body.style.cursor =

        "wait";

}



function hideLoading() {

    document.body.style.cursor =

        "default";

}



/* =====================================================
   Global Error Handler
===================================================== */

function handleError(

    error

) {

    console.error(

        error

    );

}



/* =====================================================
   Dashboard Initialization
===================================================== */

async function init() {

    try {

        showLoading();

        console.log(

            "EduRAG Dashboard Initialized"

        );



        setGreeting();

        setFooterYear();



        await loadInitialData();



        loadNotifications();



        registerEvents();



    }

    catch (error) {

        handleError(

            error

        );

    }

    finally {

        hideLoading();

    }

}



/* =====================================================
   Start Dashboard
===================================================== */

document.addEventListener(

    "DOMContentLoaded",

    init

);