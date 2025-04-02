// Убедитесь, что это ES модуль
const initApp = async () => {
  try {
    // Динамический импорт всех модулей
    const { setupAuthHandlers } = await import('./auth.js');
    const { setupLinkHandlers } = await import('./links.js');
    const { setupStatsHandlers } = await import('./stats.js');
    const { updateUI } = await import('./ui.js');

    // Инициализация
    setupAuthHandlers();
    setupLinkHandlers();
    setupStatsHandlers();
    updateUI();
    
    // Показываем контент после загрузки
    document.body.style.visibility = 'visible';
    
  } catch (error) {
    console.error('Ошибка инициализации:', error);
  }
};

export { initApp };