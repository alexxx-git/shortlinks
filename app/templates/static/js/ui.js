export function updateUI() {
    const token = localStorage.getItem('token');
    const isAuth = !!token;
    
    // Кнопки авторизации
    document.getElementById('login-button').style.display = isAuth ? 'none' : 'block';
    document.getElementById('register-button').style.display = isAuth ? 'none' : 'block';
    document.getElementById('logout-button').style.display = isAuth ? 'block' : 'none';
    
    // Контейнеры
    document.getElementById('guest-container').style.display = isAuth ? 'none' : 'block';
    document.getElementById('user-container').style.display = isAuth ? 'block' : 'none';
    
    // Приветствие
    const greeting = document.getElementById('user-greeting');
    if (isAuth) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            greeting.innerHTML = `Привет, <strong>${payload.sub}</strong>!`;
        } catch (e) {
            console.error('Ошибка декодирования токена:', e);
            greeting.textContent = 'Привет!';
        }
    } else {
        greeting.textContent = '';
    }
}

// Инициализация копирования
export function setupCopyButtons() {
    document.querySelectorAll('.copy-button').forEach(btn => {
        btn.addEventListener('click', function() {
            const targetId = this.getAttribute('data-copy-target');
            const input = document.getElementById(targetId);
            if (!input) return;
            
            input.select();
            document.execCommand('copy');
            
            // Визуальная обратная связь
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-check"></i> Скопировано!';
            setTimeout(() => {
                this.innerHTML = originalText;
            }, 2000);
        });
    });
}