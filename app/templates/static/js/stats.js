import { showError, hideError, toggleLoader, checkAuth, formatDate } from './utils.js';

export function setupStatsHandlers() {
    document.getElementById('stats-button')?.addEventListener('click', fetchStats);
}

async function fetchStats() {
    const button = document.getElementById('stats-button');
    const shortCode = document.getElementById('stats-short-code').value.trim();
    const errorElement = document.getElementById('stats-error');
    const resultElement = document.getElementById('stats-result');
    
    toggleLoader(button, true);
    hideError('stats-error');
    resultElement.style.display = 'none';
    
    try {
        if (!shortCode) throw new Error('Введите короткий код');
        
        const response = await fetch(`/links/${shortCode}/stats`, {
            headers: {
                'Authorization': `Bearer ${checkAuth()}`
            }
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Ошибка при получении статистики');
        }
        
        const stats = await response.json();
        document.getElementById('stats-original-url').textContent = stats.original_url;
        document.getElementById('stats-created-at').textContent = formatDate(stats.created_at);
        document.getElementById('stats-visit-count').textContent = stats.visit_count;
        document.getElementById('stats-last-access').textContent = formatDate(stats.last_access_at);
        
        resultElement.style.display = 'block';
    } catch (error) {
        showError('stats-error', error.message);
    } finally {
        toggleLoader(button, false, '<i class="fas fa-chart-line"></i> Показать статистику');
    }
}