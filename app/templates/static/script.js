document.addEventListener("DOMContentLoaded", function () {
    const loginModal = document.getElementById("login-modal");
    const registerModal = document.getElementById("register-modal");
    const loginButton = document.getElementById("login-button");
    const registerButton = document.getElementById("register-button");
    const logoutButton = document.getElementById("logout-button");
    const userGreeting = document.getElementById("user-greeting");
    const guestContainer = document.getElementById("guest-container");
    const userContainer = document.getElementById("user-container");
    const userOriginalLink = document.getElementById("user-original-link");
    const userCustomAlias = document.getElementById("user-custom-alias");
    const userShortLink = document.getElementById("user-short-link");
    const userErrorMessage = document.getElementById("user-error-message");

    function updateUI() {
        const token = localStorage.getItem("token");
        if (token) {
            loginButton.style.display = "none";
            registerButton.style.display = "none";
            logoutButton.style.display = "inline-block";
            userGreeting.textContent = `Привет, ${JSON.parse(atob(token.split('.')[1])).sub}!`;
            guestContainer.style.display = "none";
            userContainer.style.display = "block";
    
            // Сбросить состояние полей и кнопки
            userOriginalLink.value = "";
            userCustomAlias.value = "";
            userShortLink.value = "";
            userShortLink.style.display = "none";
            userErrorMessage.style.display = "none";
    
            // Сбросить текст кнопки на "Создать короткую ссылку"
            const button = document.getElementById("user-get-short-link");
            if (button) {
                button.textContent = "Создать короткую ссылку";
            }
        } else {
            loginButton.style.display = "inline-block";
            registerButton.style.display = "inline-block";
            logoutButton.style.display = "none";
            userGreeting.textContent = "";
            guestContainer.style.display = "block";
            userContainer.style.display = "none";
    
            // Сбросить текст кнопки при разлогинивании
            const button = document.getElementById("user-get-short-link");
            if (button) {
                button.textContent = "Создать короткую ссылку";
            }
        }
    }

    loginButton.addEventListener("click", () => loginModal.style.display = "block");
    registerButton.addEventListener("click", () => registerModal.style.display = "block");
    logoutButton.addEventListener("click", () => {
        localStorage.removeItem("token");
        updateUI();
    });

    document.querySelectorAll(".close-modal").forEach(btn => {
        btn.addEventListener("click", () => {
            loginModal.style.display = "none";
            registerModal.style.display = "none";
        });
    });

    document.getElementById("login-form").addEventListener("submit", async function (event) {
        event.preventDefault();
        const formData = new FormData(this);
        const response = await fetch("/token", { method: "POST", body: formData });
        const data = await response.json();
        if (response.ok) {
            localStorage.setItem("token", data.access_token);
            updateUI();
            loginModal.style.display = "none";
        } else {
            document.getElementById("login-error").innerText = data.detail;
        }
    });

    document.getElementById("register-form").addEventListener("submit", async function (event) {
        event.preventDefault();
        const formData = new FormData(this);
        const response = await fetch("/register", { method: "POST", body: formData });
        const data = await response.json();
        if (response.ok) {
            document.getElementById("register-modal").style.display = "none";
            const loginData = new URLSearchParams();
            loginData.append("username", formData.get("username"));
            loginData.append("password", formData.get("password"));
            const loginResponse = await fetch("/token", {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: loginData
            });
            const loginResult = await loginResponse.json();
            if (loginResponse.ok) {
                localStorage.setItem("token", loginResult.access_token);
                updateUI();
            }
        } else {
            document.getElementById("register-error").innerText = data.detail;
        }
    });

    async function shortenLink(inputId, aliasId, resultId, buttonId, errorId, isGuest = true) {
        const input = document.getElementById(inputId);
        const aliasInput = aliasId ? document.getElementById(aliasId) : null;
        const resultInput = document.getElementById(resultId);
        const button = document.getElementById(buttonId);
        const errorMessage = document.getElementById(errorId);
    
        button.addEventListener("click", async function () {
            if (button.textContent === "Хочу ещё раз") {
                input.value = '';
                if (aliasInput) aliasInput.value = '';
                resultInput.style.display = "none";
                button.textContent = isGuest ? "Создать короткую ссылку" : "Создать ещё одну ссылку";
                return;
            }
    
            const originalUrl = input.value.trim();
            if (!originalUrl) return;
    
            const customAlias = aliasInput ? aliasInput.value.trim() : undefined;
    
            const requestBody = { original_url: originalUrl };
            if (customAlias) requestBody.custom_alias = customAlias;
    
            try {
                const token = localStorage.getItem("token");
                const headers = { "Content-Type": "application/json" };
                if (token && !isGuest) headers["Authorization"] = `Bearer ${token}`;
    
                const response = await fetch(`/links/shorten`, {
                    method: "POST",
                    headers,
                    body: JSON.stringify(requestBody),
                });
    
                const data = await response.json();
    
                if (response.ok) {
                    resultInput.value = data.short_url;
                    resultInput.style.display = "block";
                    if (aliasInput) aliasInput.value = data.custom_alias || '';
                    input.value = data.original_url;
                    button.textContent = "Хочу ещё раз";
                    errorMessage.style.display = "none";
                } else {
                    if (response.status === 400 || response.status === 422) {
                        if (data.detail && Array.isArray(data.detail)) {
                            errorMessage.textContent = data.detail.map(err => err.msg).join("\n");
                        } else if (data.detail) {
                            errorMessage.textContent = data.detail;
                        } else {
                            errorMessage.textContent = "Ошибка запроса, попробуйте позже.";
                        }
                    } else {
                        errorMessage.textContent = "Ошибка сервера, попробуйте позже.";
                    }
    
                    errorMessage.style.display = "block";
                }
            } catch (error) {
                console.error("Ошибка запроса:", error);
                errorMessage.textContent = "Ошибка сети, попробуйте позже.";
                errorMessage.style.display = "block";
            }
        });
    }
    
    shortenLink("guest-original-link", null, "guest-short-link", "guest-get-short-link", "guest-error-message");
    shortenLink("user-original-link", "user-custom-alias", "user-short-link", "user-get-short-link", "user-error-message", false);
    updateUI();
});
