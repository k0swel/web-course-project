const vmId = document.body.dataset.vmId;
let currentStatus = document.body.dataset.vmStatus || 'stopped';

function updateStatusUI(status) {
    const dot    = document.getElementById('status-dot');
    const badge  = document.getElementById('status-badge');
    const btnStart = document.getElementById('btn-start');
    const btnStop  = document.getElementById('btn-stop');

    const isRunning  = status === 'running';
    const isBuilding = status === 'building';

    dot.className = `vm-status-dot ${status}`;

    if (isRunning) {
        badge.className = 'status-badge running';
        badge.textContent = 'Работает';
    } else if (isBuilding) {
        badge.className = 'status-badge building';
        badge.textContent = 'Создаётся';
    } else if (status === 'error') {
        badge.className = 'status-badge stopped';
        badge.textContent = 'Ошибка';
    } else {
        badge.className = 'status-badge stopped';
        badge.textContent = 'Выключена';
    }

    btnStart.disabled = isRunning || isBuilding;
    btnStop.disabled  = !isRunning;
}

async function refreshStatus() {
    try {
        const resp = await fetch(`/api/vm/${vmId}/status`);
        if (!resp.ok) return;
        const data = await resp.json();
        if (data.status && data.status !== currentStatus) {
            currentStatus = data.status;
            updateStatusUI(currentStatus);
        }
        const ipEl = document.getElementById('vm-ip');
        if (ipEl && data.ip) ipEl.textContent = data.ip;
    } catch (_) {}
}

async function vmAction(action) {
    if (action === 'start') {
        fetch(document.getElementById('btn-start').dataset.url, { method: 'POST' });
    } else if (action === 'stop') {
        fetch(document.getElementById('btn-stop').dataset.url, { method: 'POST' });
    } else if (action === 'console') {
        const btn = document.getElementById('btn-console');
        btn.disabled = true;
        try {
            const resp = await fetch(btn.dataset.url, { method: 'POST' });
            const data = await resp.json();
            if (data.url) {
                window.open(data.url, '_blank');
            }
        } finally {
            btn.disabled = false;
        }
    }
}

function showDeleteModal() {
    document.getElementById('delete-modal').classList.add('visible');
}

function hideDeleteModal() {
    document.getElementById('delete-modal').classList.remove('visible');
}

document.getElementById('delete-modal').addEventListener('click', function (e) {
    if (e.target === this) hideDeleteModal();
});

updateStatusUI(currentStatus);
refreshStatus();
setInterval(refreshStatus, 8000);
