import { showError, toggleLoader } from './utils.js';

// Основные обработчики
export function setupLinkHandlers() {
    // Сокращение ссылок
    setupShortener('guest');
    setupShortener('user');
    
    // Поиск ссылок
    setupSearch('guest');
    setupSearch('user');
    
    // Управление ссылками
    setupManagement();
}

// Настройка сокращения
function setupShortener(type) {
    const btnId = `${type}-shorten-btn`;
    const btn = document.getElementById(btnId);
    
    if (!btn) {
        console.warn(`Кнопка ${btnId} не найдена`);
        return;
    }

    btn.addEventListener('click', async () => {
        const urlInput = document.getElementById(`${type}-original-url`);
        const resultDiv = document.getElementById(`${type}-result`);
        
        if (!urlInput || !resultDiv) return;

        try {
            toggleLoader(btn, true);
            
            // Ваш код запроса...
            
            resultDiv.hidden = false;
        } catch (error) {
            showError(resultDiv, error.message);
        } finally {
            toggleLoader(btn, false);
        }
    });
}

// Настройка поиска
function setupSearch(type) {
    const btnId = `${type}-search-btn`;
    const btn = document.getElementById(btnId);
    
    if (!btn) {
        console.warn(`Кнопка поиска ${btnId} не найдена`);
        return;
    }

    btn.addEventListener('click', async () => {
        const input = document.getElementById(`${type}-search-input`);
        const resultDiv = document.getElementById(`${type}-search-result`);
        
        if (!input || !resultDiv) return;

        try {
            toggleLoader(btn, true);
            
            // Ваш код поиска...
            
            resultDiv.hidden = false;
        } catch (error) {
            showError(resultDiv, error.message);
        } finally {
            toggleLoader(btn, false);
        }
    });
}

// Настройка управления
function setupManagement() {
    // Аналогичная логика для update/delete
}