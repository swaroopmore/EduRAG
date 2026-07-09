const API_URL = "http://127.0.0.1:8000";

const form = document.getElementById("registerForm");

const password = document.getElementById("password");
const confirmPassword = document.getElementById("confirmPassword");

const togglePassword = document.getElementById("togglePassword");

togglePassword.addEventListener("click", () => {

    if (password.type === "password") {

        password.type = "text";

        togglePassword.innerHTML =
            '<i class="bi bi-eye-slash"></i>';

    } else {

        password.type = "password";

        togglePassword.innerHTML =
            '<i class="bi bi-eye"></i>';
    }

});

form.addEventListener("submit", async (e) => {

    e.preventDefault();

    const fullName =
        document.getElementById("fullName").value.trim();

    const email =
        document.getElementById("email").value.trim();

    const passwordValue =
        password.value.trim();

    const confirmValue =
        confirmPassword.value.trim();

    if (
        fullName === "" ||
        email === "" ||
        passwordValue === "" ||
        confirmValue === ""
    ) {

        alert("Please fill all fields.");

        return;
    }

    if (passwordValue !== confirmValue) {

        alert("Passwords do not match.");

        return;
    }

    try {

        const response = await fetch(
            API_URL + "/auth/register",
            {

                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                },

                body: JSON.stringify({

                    full_name: fullName,

                    email: email,

                    password: passwordValue,

                }),

            }
        );

        const data = await response.json();

        if (response.ok) {

            alert("Registration Successful!");

            window.location.href = "../../index.html";

        } else {

            alert(
                data.detail || "Registration Failed."
            );

        }

    } catch (error) {

        console.error(error);

        alert("Unable to connect to backend.");

    }

});