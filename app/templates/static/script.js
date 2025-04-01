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
            // Для авторизованных пользователей
            document.getElementById("guest-container").style.display = "none";
            document.getElementById("user-container").style.display = "block";
            
            // Очищаем поля поиска при переключении
            document.getElementById("guest-search-original-url").value = "";
            document.getElementById("guest-search-results").innerHTML = "";
            document.getElementById("guest-search-error").style.display = "none";
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
            // Для гостей
            document.getElementById("guest-container").style.display = "block";
            document.getElementById("user-container").style.display = "none";
            
            // Очищаем поля поиска при переключении
            document.getElementById("user-search-original-url").value = "";
            document.getElementById("user-search-results").innerHTML = "";
            document.getElementById("user-search-error").style.display = "none";
            
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

    document.getElementById("delete-button")?.addEventListener("click", async function() {
        const shortCode = document.getElementById("delete-short-code").value.trim();
        const errorElement = document.getElementById("delete-error");
        const successElement = document.getElementById("delete-success");
        
        errorElement.style.display = "none";
        successElement.style.display = "none";

        if (!shortCode) {
            errorElement.textContent = "Введите короткий код";
            errorElement.style.display = "block";
            return;
        }

        try {
            const token = localStorage.getItem("token");
            if (!token) {
                errorElement.textContent = "Требуется авторизация";
                errorElement.style.display = "block";
                return;
            }

            const response = await fetch(`/links/${shortCode}`, {
                method: "DELETE",
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            });

            if (response.ok) {
                successElement.textContent = "Ссылка успешно удалена";
                successElement.style.display = "block";
                document.getElementById("delete-short-code").value = "";
            } else {
                const data = await response.json();
                errorElement.textContent = data.detail || "Ошибка при удалении";
                errorElement.style.display = "block";
            }
        } catch (error) {
            console.error("Ошибка:", error);
            errorElement.textContent = "Ошибка сети";
            errorElement.style.display = "block";
        }
    });
    document.getElementById("update-button")?.addEventListener("click", async function() {
        const shortCode = document.getElementById("update-short-code").value.trim();
        const newUrl = document.getElementById("new-url").value.trim();
        const errorElement = document.getElementById("update-error");
        const successElement = document.getElementById("update-success");
        
        errorElement.style.display = "none";
        successElement.style.display = "none";

        if (!shortCode || !newUrl) {
            errorElement.textContent = "Заполните оба поля";
            errorElement.style.display = "block";
            return;
        }

        try {
            const token = localStorage.getItem("token");
            if (!token) {
                errorElement.textContent = "Требуется авторизация";
                errorElement.style.display = "block";
                return;
            }

            const response = await fetch(`/links/${shortCode}`, {
                method: "PUT",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    new_url: newUrl
                })
            });

            if (response.ok) {
                successElement.textContent = "URL успешно изменён";
                successElement.style.display = "block";
                document.getElementById("update-short-code").value = "";
                document.getElementById("new-url").value = "";
                
                // Обновляем UI если изменяли текущую ссылку
                if (document.getElementById("user-short-link").value === shortCode) {
                    document.getElementById("user-original-link").value = newUrl;
                }
            } else {
                const data = await response.json();
                errorElement.textContent = data.detail || "Ошибка при изменении URL";
                errorElement.style.display = "block";
            }
        } catch (error) {
            console.error("Ошибка:", error);
            errorElement.textContent = "Ошибка сети";
            errorElement.style.display = "block";
        }
    });
   // Обработчик поиска для гостей
document.getElementById("guest-search-button")?.addEventListener("click", async function() {
    await handleSearch(
        "guest-search-original-url",
        "guest-search-results",
        "guest-search-error"
    );
});

// Обработчик поиска для авторизованных пользователей
document.getElementById("user-search-button")?.addEventListener("click", async function() {
    await handleSearch(
        "user-search-original-url",
        "user-search-results",
        "user-search-error"
    );
});

// Общая функция обработки поиска
async function handleSearch(inputId, resultsId, errorId) {
    const originalUrl = document.getElementById(inputId).value.trim();
    const errorElement = document.getElementById(errorId);
    const resultsElement = document.getElementById(resultsId);
    
    errorElement.style.display = "none";
    resultsElement.innerHTML = "";
    
    if (!originalUrl) {
        errorElement.textContent = "Введите URL для поиска";
        errorElement.style.display = "block";
        return;
    }
    
    try {
        const response = await fetch(`/links/search?original_url=${encodeURIComponent(originalUrl)}`);
        const data = await response.json();
        
        if (response.ok) {
            if (data.short_code) {
                const fullShortUrl = `${window.location.origin}/${data.short_code}`;
                resultsElement.innerHTML = `
                    <p>Найдена короткая ссылка:</p>
                    <div style="margin-top: 10px;">
                        <strong>Оригинальный URL:</strong> ${data.original_url}<br>
                        <strong>Короткая ссылка:</strong> <a href="${fullShortUrl}" target="_blank">${fullShortUrl}</a><br>
                        <strong>Код:</strong> ${data.short_code}
                    </div>
                `;
            } else {
                resultsElement.innerHTML = "<p>По вашему запросу ничего не найдено</p>";
            }
        } else {
            errorElement.textContent = data.detail || "Ошибка при поиске";
            errorElement.style.display = "block";
        }
    } catch (error) {
        console.error("Ошибка поиска:", error);
        errorElement.textContent = "Ошибка сети при поиске";
        errorElement.style.display = "block";
    }
}
    }
    
    shortenLink("guest-original-link", null, "guest-short-link", "guest-get-short-link", "guest-error-message");
    shortenLink("user-original-link", "user-custom-alias", "user-short-link", "user-get-short-link", "user-error-message", false);
    updateUI();
});
