let selectedOS = 'Ubuntu';

function selectOS(card, name) {
    document.querySelectorAll('.os-card').forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    selectedOS = name;
    document.getElementById('summary-os').textContent = name;
    document.getElementById('os-input').value = name;
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
    const nameInput = document.getElementById('vm-name');
    if (!nameInput.value.trim()) {
        nameInput.focus();
        nameInput.style.borderColor = '#ff6b6b';
        event.preventDefault();
        return false;
    }
    return true;
}

document.getElementById('vm-name').addEventListener('input', function () {
    this.style.borderColor = '';
});

document.getElementById('vcpu').addEventListener('input', () => updateSlider('vcpu'));
document.getElementById('ram').addEventListener('input', () => updateSlider('ram'));
document.getElementById('ssd').addEventListener('input', () => updateSlider('ssd'));
