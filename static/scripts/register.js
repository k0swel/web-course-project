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

function handleRegister(event) {
    event.preventDefault();

    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirm = document.getElementById('confirm-password').value;

    let valid = true;

    clearError('username-error');
    clearError('email-error');
    clearError('password-error');
    clearError('confirm-error');

    if (!username) {
        showError('username-error', 'Введите имя пользователя');
        valid = false;
    } else if (username.length < 3) {
        showError('username-error', 'Минимум 3 символа');
        valid = false;
    }

    if (!email || !email.includes('@')) {
        showError('email-error', 'Введите корректный email');
        valid = false;
    }

    if (password.length < 8) {
        showError('password-error', 'Пароль должен содержать минимум 8 символов');
        valid = false;
    }

    if (password !== confirm) {
        showError('confirm-error', 'Пароли не совпадают');
        valid = false;
    }

    if (valid) {
        event.target.submit();
    }

    return false;
}
