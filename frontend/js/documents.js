const API_URL = "http://127.0.0.1:8000/documents";

const token = localStorage.getItem("token");

const params = new URLSearchParams(window.location.search);

const subjectId = params.get("subject_id");

console.log("Subject ID:", subjectId);

window.addEventListener("DOMContentLoaded", () => {

    if (!subjectId) {

        alert("No subject selected.");

        return;

    }

    loadDocuments();

});

async function loadDocuments() {

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

            throw new Error("Unable to load documents.");

        }

        const documents = await response.json();

        console.log(documents);

    }

    catch (error) {

        console.error(error);

    }

}