// Убедитесь, что экспорты правильные
export const hideError = (elementId) => {
  const element = document.getElementById(elementId);
  if (element) element.style.display = 'none';
};

export const showError = (elementId, message) => {
  const element = document.getElementById(elementId);
  if (element) {
    element.textContent = message;
    element.style.display = 'block';
  }
};

export const toggleLoader = (button, isLoading) => {
  if (button) {
    button.disabled = isLoading;
    button.innerHTML = isLoading 
      ? '<i class="fas fa-spinner fa-spin"></i>' 
      : button.dataset.originalText;
  }
};