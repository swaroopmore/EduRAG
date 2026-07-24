const API_URL =
    "http://127.0.0.1:8000/study-plans";

const token =
    localStorage.getItem(
        "token"
    );

const params =
    new URLSearchParams(
        window.location.search
    );

const subjectId =
    params.get(
        "subject_id"
    );

const subjectName =
    localStorage.getItem(
        "current_subject_name"
    );

document.getElementById(
    "subjectTitle"
).innerText =
    `${subjectName} Study Planner`;

document.getElementById(
    "summarySubject"
).innerText =
    subjectName;

let studyPlans = [];

async function init() {

    if (!subjectId) {

        alert(
            "Subject not found."
        );

        return;

    }

    await loadStudyPlan();

}

init();

async function loadStudyPlan() {

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

                "Unable to load study plan."

            );

        }

        studyPlans =

            await response.json();

        if (

            studyPlans.length === 0

        ) {

            document.getElementById(

                "timelineContainer"

            ).innerHTML = `

                <div class="empty-state">

                    <i class="bi bi-calendar-week"></i>

                    <h2>

                        No Study Plan Yet

                    </h2>

                    <p>

                        Click

                        <strong>

                            Generate Study Plan

                        </strong>

                        to create your schedule.

                    </p>

                </div>

            `;

            updateStatistics();

            return;

        }

        renderTimeline();

        updateStatistics();

    }

    catch (error) {

        console.error(error);

        alert(

            "Unable to load study plan."

        );

    }

}

function updateStatistics() {

    document.getElementById(

        "totalDays"

    ).innerText =

        studyPlans.length;

    document.getElementById(

        "summaryDays"

    ).innerText =

        studyPlans.length;

    document.getElementById(

        "totalSessions"

    ).innerText =

        studyPlans.length;

    document.getElementById(

        "summarySessions"

    ).innerText =

        studyPlans.length;

    let totalMinutes = 0;

    studyPlans.forEach(

        plan => {

            const value =

                parseInt(

                    plan.duration

                );

            if (

                !isNaN(value)

            ) {

                totalMinutes += value;

            }

        }

    );

    const hours =

        (totalMinutes / 60)

        .toFixed(1);

    document.getElementById(

        "totalDuration"

    ).innerText =

        `${hours} hrs`;

    document.getElementById(

        "summaryDuration"

    ).innerText =

        `${hours} hrs`;

}

function renderTimeline() {

    const container =
        document.getElementById(
            "timelineContainer"
        );

    container.innerHTML = "";

    studyPlans.forEach(

        (plan, index) => {

            container.innerHTML += `

                <div class="timeline-card">

                    <div class="day">

                        Day ${plan.day}

                    </div>

                    <h2>

                        ${plan.title}

                    </h2>

                    <p>

                        ${plan.description}

                    </p>

                    <div class="badges">

                        <span class="badge">

                            <i class="bi bi-clock"></i>

                            ${plan.time}

                        </span>

                        <span class="badge">

                            <i class="bi bi-hourglass-split"></i>

                            ${plan.duration}

                        </span>

                    </div>

                </div>

            `;

        }

    );

}

async function generateStudyPlan() {

    try {

        const button =
            document.getElementById(
                "generateBtn"
            );

        button.disabled = true;

        button.innerHTML =
            '<i class="bi bi-arrow-repeat spin"></i> Generating...';

        document.getElementById(
            "timelineContainer"
        ).innerHTML = `

            <div class="loading-card">

                <h2>

                    Generating Study Plan...

                </h2>

                <p>

                    AI is creating your personalized study schedule.

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
                "Failed to generate study plan."
            );

        }

        await loadStudyPlan();

    }

    catch (error) {

        console.error(error);

        alert(
            "Unable to generate study plan."
        );

    }

    finally {

        const button =
            document.getElementById(
                "generateBtn"
            );

        button.disabled = false;

        button.innerHTML =
            '<i class="bi bi-stars"></i> Generate Study Plan';

    }

}

document

    .getElementById(
        "generateBtn"
    )

    .addEventListener(

        "click",

        generateStudyPlan

    );