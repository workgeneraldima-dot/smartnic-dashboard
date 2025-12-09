const blockedBody = document.querySelector('#blocked-table tbody');

async function loadBlocked() {
  const response = await fetch('/api/blocked_ips');
  const blocked = await response.json();
  blockedBody.innerHTML = '';

  blocked.forEach(entry => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${entry.ip_address}</td>
      <td>${entry.attack_type || ''}</td>
      <td>${new Date(entry.first_seen).toLocaleString()}</td>
      <td>${new Date(entry.last_seen).toLocaleString()}</td>
      <td><span class="badge bg-danger">${entry.status}</span></td>
      <td><button class="btn btn-sm btn-outline-secondary" data-ip="${entry.ip_address}">Unblock</button></td>
    `;
    blockedBody.appendChild(row);
  });
}

blockedBody.addEventListener('click', async (e) => {
  if (e.target.tagName === 'BUTTON') {
    const ip = e.target.getAttribute('data-ip');
    await fetch('/api/blocked_ips/unblock', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip })
    });
    loadBlocked();
  }
});

loadBlocked();
setInterval(loadBlocked, 5000);
