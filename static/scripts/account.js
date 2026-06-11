function applyStatus(dot, status) {
    dot.className = 'vm-status ' + (status || 'stopped');
}

async function refreshAllStatuses() {
    const cards = document.querySelectorAll('[data-vm-id]');
    await Promise.all([...cards].map(async card => {
        const vmId = card.dataset.vmId;
        try {
            const resp = await fetch(`/api/vm/${vmId}/status`);
            if (!resp.ok) return;
            const data = await resp.json();
            const dot = document.getElementById(`vm-status-${vmId}`);
            if (dot) applyStatus(dot, data.status);
        } catch (_) {}
    }));
}

refreshAllStatuses();
setInterval(refreshAllStatuses, 8000);
