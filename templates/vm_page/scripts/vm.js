let isRunning = document.body.dataset.vmStatus === 'running';

function updateStatusUI() {
    const dot = document.getElementById('status-dot');
    const badge = document.getElementById('status-badge');
    const btnStart = document.getElementById('btn-start');
    const btnStop = document.getElementById('btn-stop');

    if (isRunning) {
        dot.className = 'vm-status-dot running';
        badge.className = 'status-badge running';
        badge.textContent = 'Работает';
        btnStart.disabled = true;
        btnStop.disabled = false;
    } else {
        dot.className = 'vm-status-dot stopped';
        badge.className = 'status-badge stopped';
        badge.textContent = 'Выключена';
        btnStart.disabled = false;
        btnStop.disabled = true;
    }
}

function vmAction(action) {
    if (action === 'start') {
        const url = document.getElementById('btn-start').dataset.url;
        fetch(url, { method: 'POST' });
        isRunning = true;
        updateStatusUI();
    } else if (action === 'stop') {
        const url = document.getElementById('btn-stop').dataset.url;
        fetch(url, { method: 'POST' });
        isRunning = false;
        updateStatusUI();
    } else if (action === 'console') {
        // TODO: открыть веб-консоль (WebSocket / noVNC)
        console.log('Открыть консоль');
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

updateStatusUI();
