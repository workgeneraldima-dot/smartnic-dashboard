const tableBody = document.querySelector('#events-table tbody');
const filter = document.getElementById('decision-filter');

function decisionClass(decision) {
  if (decision === 'BLOCKED') return 'table-danger';
  if (decision === 'SUSPICIOUS') return 'table-warning';
  return '';
}

async function loadEvents() {
  const response = await fetch('/api/events?limit=100');
  const events = await response.json();
  tableBody.innerHTML = '';

  events
    .filter(evt => !filter.value || evt.decision === filter.value)
    .forEach(evt => {
      const row = document.createElement('tr');
      row.className = decisionClass(evt.decision);
      row.innerHTML = `
        <td>${new Date(evt.timestamp).toLocaleString()}</td>
        <td>${evt.source_ip}</td>
        <td>${evt.destination_ip}</td>
        <td>${evt.attack_type}</td>
        <td>${evt.decision}</td>
        <td>${evt.packet_count}</td>
      `;
      tableBody.appendChild(row);
    });
}

filter.addEventListener('change', loadEvents);
loadEvents();
setInterval(loadEvents, 3000);
