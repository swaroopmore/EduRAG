const API_URL = "http://127.0.0.1:8000/auth/login";

const form = document.getElementById("loginForm");

form.addEventListener("submit", login);

async function login(event) {

    event.preventDefault();

    const email = document.getElementById("email").value.trim();

    const password = document.getElementById("password").value;

    try {

        const response = await fetch(API_URL, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                email,
                password
            })

        });

        const data = await response.json();

        if (!response.ok) {

            alert(data.detail || "Login failed");

            return;

        }

        localStorage.setItem("token", data.access_token);

        window.location.href = "dashboard.html";

    }

    catch (error) {

        console.error(error);

        alert("Unable to connect to server.");

    }

}