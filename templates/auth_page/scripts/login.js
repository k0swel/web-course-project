function togglePassword(inputId, btn) {
    const input = document.getElementById(inputId);
    const icon = btn.querySelector('i');
    const isHidden = input.type === 'password';
    input.type = isHidden ? 'text' : 'password';
    icon.className = isHidden ? 'bi bi-eye-slash' : 'bi bi-eye';
}

function showError(id, message) {
    const el = document.getElementById(id);
    el.textContent = message;
    el.style.display = 'block';
}

function clearError(id) {
    const el = document.getElementById(id);
    el.textContent = '';
    el.style.display = 'none';
}

function handleLogin(event) {
    event.preventDefault();

    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    let valid = true;

    clearError('email-error');
    clearError('password-error');

    if (!email || !email.includes('@')) {
        showError('email-error', 'Введите корректный email');
        valid = false;
    }

    if (!password) {
        showError('password-error', 'Введите пароль');
        valid = false;
    }

    if (valid) {
        // что сделать потом: отправить данные на сервер
        console.log('Вход:', { email });
    }

    return false;
}
