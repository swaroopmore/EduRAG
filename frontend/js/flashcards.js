const API_URL = "http://127.0.0.1:8000/flashcards";

const token = localStorage.getItem("access_token");

const params = new URLSearchParams(window.location.search);

const subjectId = params.get("subject_id");

const subjectName = localStorage.getItem("current_subject_name");
const totalCards = document.getElementById("totalCards");
const currentCard = document.getElementById("currentCard");
const masteredCards = document.getElementById("masteredCards");
const progressPercent = document.getElementById("progressPercent");

const progressFill = document.getElementById("progressFill");
const progressText = document.getElementById("progressText");

console.log(subjectId);
console.log(window.location.href);

let flashcards = [];

let currentIndex = 0;

let showingAnswer = false;
let mastered = new Set();



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
        "🧠 " + subjectName;

    loadFlashcards();

});

async function loadFlashcards() {

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

            throw new Error("Unable to load flashcards.");

        }

        flashcards = await response.json();
        console.log("FlashCards Receieved :",flashcards);
        console.log("Count",flashcards.length);

   if (flashcards.length === 0) {

    document.getElementById("flashcard").innerHTML = `

        <div class="empty-state">

            <i class="bi bi-journal-richtext"></i>

            <h2>No Flashcards Yet</h2>

            <p>

                Generate AI-powered flashcards
                from your uploaded documents.

            </p>

        </div>

    `;

    updateStatistics();

    return;

}

        currentIndex = 0;

        renderFlashcard();

    }

    catch (error) {

        console.error(error);

        alert("Unable to load flashcards.");

    }

}

function renderFlashcard() {

    const flashcard = flashcards[currentIndex];

    showingAnswer = false;

    document.getElementById("flashcard").innerHTML = `

        <div class="card-face question">

    <span class="card-label">

        Question

    </span>

    <h2>

        ${flashcard.question}

    </h2>

    <small>

        Click anywhere to reveal answer

    </small>

</div>

    `;


    document.getElementById("previousBtn").disabled =

        currentIndex === 0;

    document.getElementById("nextBtn").disabled =

        currentIndex === flashcards.length - 1;

        updateStatistics();

}

function flipFlashcard() {

    if (flashcards.length === 0) {

        return;

    }

    const flashcard = flashcards[currentIndex];

    if (showingAnswer) {

        document.getElementById("flashcard").innerHTML = `

            <div class="card-face question">

                <h3>Question</h3>

                <p>${flashcard.question}</p>

            </div>

        `;

        showingAnswer = false;

    }

    else {

        document.getElementById("flashcard").innerHTML = `

           <div class="card-face answer">

    <span class="card-label">

        Answer

    </span>

    <h2>

        ${flashcard.answer}

    </h2>

</div>

        `;

        showingAnswer = true;

    }

}

document
    .getElementById("flipBtn")
    .addEventListener(
        "click",
        flipFlashcard
    );


    function nextFlashcard() {

    if (flashcards.length === 0) {

        return;

    }

    if (currentIndex < flashcards.length - 1) {

        mastered.add(currentIndex);

        currentIndex++;

        renderFlashcard();

    }

}

function previousFlashcard() {

    if (flashcards.length === 0) {

        return;

    }

    if (currentIndex > 0) {

        currentIndex--;

        renderFlashcard();

    }

}

document
    .getElementById("nextBtn")
    .addEventListener(
        "click",
        nextFlashcard
    );

document
    .getElementById("previousBtn")
    .addEventListener(
        "click",
        previousFlashcard
    );

    async function generateFlashcards() {

    try {

        const button =

            document.getElementById("generateBtn");

        button.disabled = true;

        button.innerHTML =

            '<i class="bi bi-arrow-repeat spin"></i> Generating...';

        document.getElementById("flashcard").innerHTML = `

            <div class="loading-card">

                <h3>Generating Flashcards...</h3>

                <p>This may take a few seconds.</p>

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

            throw new Error();

        }

        await loadFlashcards();

    }

    catch (error) {

        console.error(error);

        alert("Failed to generate flashcards.");

    }

    finally {

        const button =

            document.getElementById("generateBtn");

        button.disabled = false;

        button.innerHTML =

            '<i class="bi bi-stars"></i> Generate Flashcards';

    }

}

document
    .getElementById("generateBtn")
    .addEventListener(
        "click",
        generateFlashcards
    );

    function shuffleFlashcards() {

    if (flashcards.length <= 1) {

        return;

    }

    for (

        let i = flashcards.length - 1;

        i > 0;

        i--

    ) {

        const j = Math.floor(

            Math.random() * (i + 1)

        );

        [

            flashcards[i],

            flashcards[j]

        ] = [

            flashcards[j],

            flashcards[i]

        ];

    }

    currentIndex = 0;

    renderFlashcard();
    updateStatistics();

}

document
    .getElementById("shuffleBtn")
    .addEventListener(
        "click",
        shuffleFlashcards
    );

    document.addEventListener(

    "keydown",

    (event) => {

        switch (event.key) {

            case "ArrowRight":

                nextFlashcard();

                break;

            case "ArrowLeft":

                previousFlashcard();

                break;

            case " ":

                event.preventDefault();

                flipFlashcard();

                break;

        }

    }

);

document
    .getElementById("flashcard")
    .addEventListener(
        "click",
        flipFlashcard
    );

function updateStatistics() {

    totalCards.textContent = flashcards.length;

    currentCard.textContent =
        flashcards.length === 0
        ? "0 / 0"
        : `${currentIndex + 1} / ${flashcards.length}`;

    masteredCards.textContent =
        mastered.size;

    const percent =
        flashcards.length === 0
        ? 0
        : Math.round(((currentIndex + 1) / flashcards.length) * 100);

    progressPercent.textContent =
        percent + "%";

    progressFill.style.width =
        percent + "%";

    progressText.textContent =
        percent + "%";

}