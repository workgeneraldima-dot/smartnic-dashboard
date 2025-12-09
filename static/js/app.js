const API_PREFIX = '/api';

async function fetchJSON(url, options = {}) {
    const response = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });
    if (!response.ok) {
        const text = await response.text();
        throw new Error(text || response.statusText);
    }
    return response.json();
}

function formatDate(value) {
    if (!value) return '';
    const date = new Date(value);
    return date.toLocaleString();
}

function decisionBadge(decision) {
    const badgeMap = {
        'BENIGN': 'success',
        'SUSPICIOUS': 'warning',
        'BLOCKED': 'danger'
    };
    const color = badgeMap[decision] || 'secondary';
    return `<span class="badge bg-${color}">${decision}</span>`;
}

window.dashboardPage = async function() {
    try {
        const stats = await fetchJSON(`${API_PREFIX}/events/stats`);
        document.getElementById('stat-total').textContent = stats.total_events;
        document.getElementById('stat-attacks').textContent = stats.attacks_today;
        document.getElementById('stat-blocked').textContent = stats.blocked_count;

        const ctxLine = document.getElementById('chart-line');
        const ctxPie = document.getElementById('chart-pie');

        const lineData = {
            labels: stats.attacks_over_time.map(item => new Date(item.timestamp).toLocaleTimeString()),
            datasets: [{
                label: 'Attacks',
                data: stats.attacks_over_time.map(item => item.count),
                fill: true,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13,110,253,0.2)'
            }]
        };
        new Chart(ctxLine, {
            type: 'line',
            data: lineData,
            options: { scales: { y: { beginAtZero: true } } }
        });

        const labels = Object.keys(stats.attacks_by_type);
        const counts = Object.values(stats.attacks_by_type);
        new Chart(ctxPie, {
            type: 'pie',
            data: {
                labels,
                datasets: [{
                    data: counts,
                    backgroundColor: ['#dc3545', '#0d6efd', '#ffc107', '#198754', '#6610f2']
                }]
            }
        });
    } catch (err) {
        console.error('Failed to load dashboard stats', err);
    }
}

window.eventsPage = function() {
    const tableBody = document.querySelector('#events-table tbody');
    const filter = document.getElementById('filter');

    async function loadEvents() {
        try {
            const events = await fetchJSON(`${API_PREFIX}/events?limit=200`);
            tableBody.innerHTML = '';
            events
                .filter(ev => filter.value === 'ALL' || ev.decision === filter.value)
                .forEach(ev => {
                    const row = document.createElement('tr');
                    row.className = `decision-${ev.decision.toLowerCase()}`;
                    row.innerHTML = `
                        <td>${formatDate(ev.timestamp)}</td>
                        <td>${ev.source_ip}</td>
                        <td>${ev.destination_ip}</td>
                        <td>${ev.attack_type}</td>
                        <td>${decisionBadge(ev.decision)}</td>
                        <td>${ev.packet_count}</td>
                    `;
                    tableBody.appendChild(row);
                });
        } catch (err) {
            console.error('Failed to load events', err);
        }
    }

    filter.addEventListener('change', loadEvents);
    loadEvents();
    setInterval(loadEvents, 4000);
}

window.blockedPage = function() {
    const tableBody = document.querySelector('#blocked-table tbody');

    async function loadBlocked() {
        try {
            const blocked = await fetchJSON(`${API_PREFIX}/blocked_ips`);
            tableBody.innerHTML = '';
            blocked.forEach(ip => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${ip.ip_address}</td>
                    <td>${ip.attack_type}</td>
                    <td>${formatDate(ip.first_seen)}</td>
                    <td>${formatDate(ip.last_seen)}</td>
                    <td>${ip.status}</td>
                    <td><button class="btn btn-sm btn-outline-danger" data-ip="${ip.ip_address}">Unblock</button></td>
                `;
                tableBody.appendChild(row);
            });
        } catch (err) {
            console.error('Failed to load blocked IPs', err);
        }
    }

    tableBody.addEventListener('click', async (event) => {
        const target = event.target;
        if (target.tagName === 'BUTTON') {
            const ip = target.getAttribute('data-ip');
            try {
                await fetchJSON(`${API_PREFIX}/blocked_ips/unblock`, {
                    method: 'POST',
                    body: JSON.stringify({ ip })
                });
                loadBlocked();
            } catch (err) {
                console.error('Failed to unblock IP', err);
            }
        }
    });

    loadBlocked();
    setInterval(loadBlocked, 5000);
}

window.settingsPage = async function() {
    const form = document.getElementById('settings-form');
    const statusEl = document.getElementById('settings-status');

    async function loadConfig() {
        try {
            const config = await fetchJSON(`${API_PREFIX}/config`);
            config.forEach(entry => {
                if (entry.key === 'syn_threshold') {
                    form.syn_threshold.value = entry.value;
                }
                if (entry.key === 'udp_threshold') {
                    form.udp_threshold.value = entry.value;
                }
                if (entry.key === 'enable_ml') {
                    form.enable_ml.checked = entry.value === 'True' || entry.value === true || entry.value === '1';
                }
            });
        } catch (err) {
            console.error('Failed to load config', err);
        }
    }

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const payload = {
            syn_threshold: form.syn_threshold.value ? parseInt(form.syn_threshold.value, 10) : undefined,
            udp_threshold: form.udp_threshold.value ? parseInt(form.udp_threshold.value, 10) : undefined,
            enable_ml: form.enable_ml.checked,
        };
        try {
            await fetchJSON(`${API_PREFIX}/config`, {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            statusEl.textContent = 'Saved';
            setTimeout(() => statusEl.textContent = '', 2000);
        } catch (err) {
            statusEl.textContent = 'Error saving settings';
        }
    });

    loadConfig();
}
