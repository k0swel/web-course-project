let selectedOS = 'Ubuntu';

function selectOS(card, name) {
    document.querySelectorAll('.os-card').forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    selectedOS = name;
    document.getElementById('summary-os').textContent = name;
    document.getElementById('os-input').value = name;
}

function toggleVMPassword(inputId, btn) {
    const input = document.getElementById(inputId);
    const icon = btn.querySelector('i');
    const hidden = input.type === 'password';
    input.type = hidden ? 'text' : 'password';
    icon.className = hidden ? 'bi bi-eye-slash' : 'bi bi-eye';
}

function showFieldError(id, msg) {
    const el = document.getElementById(id);
    el.textContent = msg;
    el.style.display = 'block';
}

function clearFieldError(id) {
    const el = document.getElementById(id);
    el.textContent = '';
    el.style.display = 'none';
}

function pluralCores(n) {
    if (n === 1) return 'ядро';
    if (n >= 2 && n <= 4) return 'ядра';
    return 'ядер';
}

function updateSlider(id) {
    const value = parseInt(document.getElementById(id).value);

    if (id === 'vcpu') {
        document.getElementById('vcpu-display').innerHTML = `${value} <span>${pluralCores(value)}</span>`;
        document.getElementById('summary-vcpu').textContent = `${value} ${pluralCores(value)}`;
        document.getElementById('vcpu-input').value = value;
    } else if (id === 'ram') {
        document.getElementById('ram-display').innerHTML = `${value} <span>GB</span>`;
        document.getElementById('summary-ram').textContent = `${value} GB`;
        document.getElementById('ram-input').value = value;
    } else if (id === 'ssd') {
        document.getElementById('ssd-display').innerHTML = `${value} <span>GB</span>`;
        document.getElementById('summary-ssd').textContent = `${value} GB`;
        document.getElementById('ssd-input').value = value;
    }
}

function validateVM(event) {
    clearFieldError('name-error');
    clearFieldError('password-error');
    clearFieldError('confirm-error');

    const name = document.getElementById('vm-name').value.trim();
    const password = document.getElementById('vm-password').value;
    const confirm = document.getElementById('vm-password-confirm').value;

    let valid = true;

    if (!name) {
        showFieldError('name-error', 'Введите название машины');
        document.getElementById('vm-name').focus();
        valid = false;
    }

    if (password.length < 8) {
        showFieldError('password-error', 'Минимум 8 символов');
        valid = false;
    }

    if (password !== confirm) {
        showFieldError('confirm-error', 'Пароли не совпадают');
        valid = false;
    }

    if (!valid) {
        event.preventDefault();
        return false;
    }

    return true;
}

document.getElementById('vm-name').addEventListener('input', function () {
    clearFieldError('name-error');
});

document.getElementById('vm-password').addEventListener('input', function () {
    clearFieldError('password-error');
    clearFieldError('confirm-error');
});

document.getElementById('vm-password-confirm').addEventListener('input', function () {
    clearFieldError('confirm-error');
});

document.getElementById('vcpu').addEventListener('input', () => updateSlider('vcpu'));
document.getElementById('ram').addEventListener('input', () => updateSlider('ram'));
document.getElementById('ssd').addEventListener('input', () => updateSlider('ssd'));
