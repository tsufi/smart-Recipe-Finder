// static/js/admin.js

document.addEventListener('DOMContentLoaded', () => {
  const modalElement = document.getElementById('confirmActionModal');
  const form = document.getElementById('adminActionForm');
  const message = document.getElementById('modalMessage');
  const passwordInput = document.getElementById('adminPassword');

  window.openAdminModal = function (actionUrl, actionText, username) {
    form.action = actionUrl;
    message.textContent = `${actionText} "${username}". Please confirm with your admin password.`;
    passwordInput.value = '';
    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
    modal.show();
  };
});
