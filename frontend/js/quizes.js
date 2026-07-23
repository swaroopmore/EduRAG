const API_URL =
    "http://127.0.0.1:8000/quiz";

const token =
    localStorage.getItem("access_token");
    const totalQuestions =
    document.getElementById("totalQuestions");

const currentQuestion =
    document.getElementById("currentQuestion");

const scoreCard =
    document.getElementById("score");

const accuracyCard =
    document.getElementById("accuracy");

const progressFill =
    document.getElementById("progressFill");

const progressText =
    document.getElementById("progressText");

const resultModal =
    document.getElementById("resultModal");

const finalScore =
    document.getElementById("finalScore");

const finalAccuracy =
    document.getElementById("finalAccuracy");

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
    `${subjectName} Quiz`;

let quizzes = [];

let currentIndex = 0;

let answers = {};

async function init() {

    if (!subjectId) {

        alert("Subject not found.");

        return;

    }

    await loadQuiz();

}

init();

async function loadQuiz() {

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
                "Unable to load quiz."
            );

        }

        quizzes = await response.json();

        console.log(
            "Quizzes:",
            quizzes
        );

        if (quizzes.length === 0) {

            document.getElementById(
                "quizCard"
            ).innerHTML = `

                <div class="empty-state">

                    <h2>No Quiz Available</h2>

                    <p>
                        Click Generate Quiz
                        to create AI MCQs.
                    </p>

                </div>

            `;

            return;

        }

        currentIndex = 0;

        renderQuestion();

    }

    catch (error) {

        console.error(error);

        alert(
            "Unable to load quiz."
        );

    }

}

function renderQuestion() {

    const quiz = quizzes[currentIndex];

    const selectedAnswer =
        answers[currentIndex] || "";

document.getElementById("quizCard").innerHTML = `

<div class="question-number">

Question ${currentIndex+1}

</div>

<h2 class="question">

${quiz.question}

</h2>

<div class="options">

<div class="option ${selectedAnswer==="A"?"selected":""}"

onclick="selectAnswer('A')">

<strong>A.</strong>

${quiz.option_a}

</div>

<div class="option ${selectedAnswer==="B"?"selected":""}"

onclick="selectAnswer('B')">

<strong>B.</strong>

${quiz.option_b}

</div>

<div class="option ${selectedAnswer==="C"?"selected":""}"

onclick="selectAnswer('C')">

<strong>C.</strong>

${quiz.option_c}

</div>

<div class="option ${selectedAnswer==="D"?"selected":""}"

onclick="selectAnswer('D')">

<strong>D.</strong>

${quiz.option_d}

</div>

</div>

`;

     updateStatistics();

    document.getElementById(
        "previousBtn"
    ).disabled =
        currentIndex === 0;

    document.getElementById(
        "nextBtn"
    ).disabled =
        currentIndex === quizzes.length - 1;

      

}

function selectAnswer(
    option
) {

    answers[currentIndex] =
        option;

    renderQuestion();

}

document
    .getElementById(
        "previousBtn"
    )
    .addEventListener(
        "click",
        previousQuestion
    );

document
    .getElementById(
        "nextBtn"
    )
    .addEventListener(
        "click",
        nextQuestion
    );

    function previousQuestion() {

    if (
        currentIndex > 0
    ) {

        currentIndex--;

        renderQuestion();

    }

}

function nextQuestion() {

    if (
        currentIndex <
        quizzes.length - 1
    ) {

        currentIndex++;

        renderQuestion();

    }

}

async function generateQuiz() {

    try {

        const button =

            document.getElementById(
                "generateBtn"
            );

        button.disabled = true;

        button.innerHTML =

            '<i class="bi bi-arrow-repeat spin"></i> Generating...';

        document.getElementById(
            "quizCard"
        ).innerHTML = `

            <div class="loading-card">

                <h2>Generating Quiz...</h2>

                <p>

                    AI is preparing your quiz.

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
                "Quiz generation failed."
            );

        }

        answers = {};

        await loadQuiz();

    }

    catch (error) {

        console.error(error);

        alert(
            "Unable to generate quiz."
        );

    }

    finally {

        const button =

            document.getElementById(
                "generateBtn"
            );

        button.disabled = false;

        button.innerHTML =

            '<i class="bi bi-stars"></i> Generate Quiz';

    }

}

document
    .getElementById(
        "generateBtn"
    )
    .addEventListener(
        "click",
        generateQuiz
    );

    function submitQuiz() {

    let score = 0;

    quizzes.forEach((quiz, index) => {

        if (answers[index] === quiz.correct_answer) {

            score++;

        }

    });

    const percent = quizzes.length === 0
        ? 0
        : Math.round((score / quizzes.length) * 100);

    scoreCard.innerText = score;

    accuracyCard.innerText = `${percent}%`;

    finalScore.innerText = `${score} / ${quizzes.length}`;

    finalAccuracy.innerText = `Accuracy : ${percent}%`;

    resultModal.classList.remove("hidden");

    document.getElementById("submitBtn").disabled = true;

}


// Restart Quiz Button
document
    .getElementById("restartBtn")
    .addEventListener("click", () => {

        answers = {};

        currentIndex = 0;

        resultModal.classList.add("hidden");

        document.getElementById("submitBtn").disabled = false;

        renderQuestion();

    });


function renderReview() {

    const container =

        document.getElementById(

            "reviewContainer"

        );

    container.innerHTML = "";

    quizzes.forEach(

        (quiz, index) => {

            const userAnswer =

                answers[index] ||

                "Not Answered";

            const correct =

                userAnswer ===

                quiz.correct_answer;

            container.innerHTML += `

                <div class="review-card">

                    <h3>

                        Q${index + 1}. ${quiz.question}

                    </h3>

                    <p>

                        <strong>Your Answer:</strong>

                        <span class="${
                            correct
                                ? "correct"
                                : "wrong"
                        }">

                            ${userAnswer}

                        </span>

                    </p>

                    <p>

                        <strong>Correct Answer:</strong>

                        ${quiz.correct_answer}

                    </p>

                    <p>

                        <strong>Explanation:</strong>

                        ${quiz.explanation}

                    </p>

                </div>

            `;

        }

    );

    document.getElementById(

        "reviewSection"

    ).style.display = "block";

}

function retryQuiz() {

    currentIndex = 0;

    answers = {};

    document.getElementById(

        "quizContainer"

    ).style.display = "block";

    document.getElementById(

        "resultSection"

    ).style.display = "none";

    document.getElementById(
    "reviewSection"
).style.display = "none";

    document.getElementById(

        "submitBtn"

    ).disabled = false;

    renderQuestion();

}

document

    .getElementById(

        "submitBtn"

    )

    .addEventListener(

        "click",

        submitQuiz

    );



    document
    .getElementById("restartBtn")
    .addEventListener(
        "click",
        () => {

            answers = {};

            currentIndex = 0;

            resultModal.classList.add("hidden");

            renderQuestion();

        }
    );

    function updateStatistics(){

    totalQuestions.innerText =
        quizzes.length;

    currentQuestion.innerText =
        quizzes.length===0
        ? "0 / 0"
        : `${currentIndex+1} / ${quizzes.length}`;

    let score=0;

    quizzes.forEach((quiz,index)=>{

        if(
            answers[index]===quiz.correct_answer
        ){

            score++;

        }

    });

    scoreCard.innerText=score;

    const percent=
        quizzes.length===0
        ?0
        :Math.round((score/quizzes.length)*100);

    accuracyCard.innerText=
        percent+"%";

    const progress=
        quizzes.length===0
        ?0
        :Math.round(((currentIndex+1)/quizzes.length)*100);

    progressFill.style.width=
        progress+"%";

    progressText.innerText=
        progress+"%";

}