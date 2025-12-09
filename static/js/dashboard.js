const attackCtx = document.getElementById('attackTypeChart');
const decisionCtx = document.getElementById('decisionChart');
let attackChart; let decisionChart;

async function loadStats() {
  const response = await fetch('/api/events/stats');
  const data = await response.json();

  const totalEvents = Object.values(data.decision_counts).reduce((a, b) => a + b, 0);
  document.getElementById('events-count').textContent = totalEvents;
  document.getElementById('blocked-count').textContent = data.blocked_total;

  const benign = data.decision_counts['BENIGN'] || 0;
  const threats = totalEvents - benign;
  document.getElementById('decision-summary').textContent = `${benign} benign / ${threats} threats`;

  const attackLabels = Object.keys(data.attacks_by_type);
  const attackValues = Object.values(data.attacks_by_type);

  if (attackChart) attackChart.destroy();
  attackChart = new Chart(attackCtx, {
    type: 'bar',
    data: {
      labels: attackLabels,
      datasets: [{
        label: 'Count',
        data: attackValues,
        backgroundColor: 'rgba(54, 162, 235, 0.6)'
      }]
    }
  });

  const decisionLabels = Object.keys(data.decision_counts);
  const decisionValues = Object.values(data.decision_counts);

  if (decisionChart) decisionChart.destroy();
  decisionChart = new Chart(decisionCtx, {
    type: 'doughnut',
    data: {
      labels: decisionLabels,
      datasets: [{
        data: decisionValues,
        backgroundColor: ['#198754', '#ffc107', '#dc3545']
      }]
    }
  });
}

loadStats();
setInterval(loadStats, 5000);
