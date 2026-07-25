const form = document.getElementById("loginForm");

form.addEventListener("submit", login);

async function login(event) {
    event.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    try {
        const response = await fetch(`${BASE_URL}/auth/login`, {
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

        // Store JWT Token
        localStorage.setItem("access_token", data.access_token);

        // Redirect to Dashboard
        window.location.href = "dashboard.html";

    } catch (error) {
        console.error("Login Error:", error);
        alert("Unable to connect to server.");
    }
}