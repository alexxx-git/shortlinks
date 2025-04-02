import { showError, hideError, toggleLoader } from './utils.js';

export const setupAuthHandlers = () => {
  const loginForm = document.getElementById('login-form');
  if (!loginForm) return;

  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    // Ваша логика авторизации
  });
};import { showError, hideError, toggleLoader } from './utils.js';

export const setupAuthHandlers = () => {
  const loginForm = document.getElementById('login-form');
  if (!loginForm) return;

  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    // Ваша логика авторизации
  });
};