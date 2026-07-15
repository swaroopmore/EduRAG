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
    await loadStatistics();

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