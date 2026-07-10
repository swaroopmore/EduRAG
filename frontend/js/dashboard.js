const API_URL = "http://127.0.0.1:8000/dashboard";

window.onload = loadDashboard;

async function loadDashboard() {

    const token = localStorage.getItem("token");

    if (!token) {
        window.location.href = "login.html";
        return;
    }

    try {

        const response = await fetch(API_URL, {
            method: "GET",
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        if (!response.ok) {
            throw new Error("Unauthorized");
        }

        const data = await response.json();

        document.getElementById("welcomeName").innerText =
            data.full_name;

        document.getElementById("subjectsCount").innerText =
            data.subjects;

        document.getElementById("documentsCount").innerText =
            data.documents;

        document.getElementById("chatCount").innerText =
            data.ai_chats;

        document.getElementById("flashcardCount").innerText =
            data.flashcards;

        document.getElementById("quizCount").innerText =
            data.quizzes;

    } catch (error) {

        console.error(error);

        localStorage.removeItem("token");

        window.location.href = "login.html";

    }

}