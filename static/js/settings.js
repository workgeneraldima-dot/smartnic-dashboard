const form = document.getElementById('settings-form');
const statusSpan = document.getElementById('save-status');

async function loadSettings() {
  const response = await fetch('/api/config');
  const configs = await response.json();
  const configMap = Object.fromEntries(configs.map(c => [c.key, c.value]));
  if (configMap.syn_threshold) form.syn_threshold.value = configMap.syn_threshold;
  if (configMap.udp_threshold) form.udp_threshold.value = configMap.udp_threshold;
  form.ml_enabled.checked = configMap.ml_enabled === 'True' || configMap.ml_enabled === true;
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  statusSpan.textContent = '';
  const payload = {
    syn_threshold: form.syn_threshold.value ? Number(form.syn_threshold.value) : null,
    udp_threshold: form.udp_threshold.value ? Number(form.udp_threshold.value) : null,
    ml_enabled: form.ml_enabled.checked,
  };
  await fetch('/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  statusSpan.textContent = 'Saved!';
});

loadSettings();
