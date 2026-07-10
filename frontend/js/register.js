const API_URL = "http://127.0.0.1:8000/auth/register";

const form = document.getElementById("registerForm");

form.addEventListener("submit", register);

async function register(event) {

    event.preventDefault();

    const full_name = document.getElementById("fullName").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirmPassword").value;

    if (password !== confirmPassword) {
        alert("Passwords do not match.");
        return;
    }

    try {

        const response = await fetch(API_URL, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                full_name,
                email,
                password
            })

        });

        const data = await response.json();

        if (!response.ok) {
            alert(data.detail);
            return;
        }

        alert("Registration Successful!");

        window.location.href = "login.html";

    } catch (error) {

        console.error(error);

        alert("Unable to connect to server.");

    }

}