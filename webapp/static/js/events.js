(function () {
  const tableBody = document.querySelector('#pending-table tbody');
  const emptyMsg = document.querySelector('#pending-empty');
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
  const pendingTakenUrl = (id) => `/intake/${id}/taken`;
  const pendingMissedUrl = (id) => `/intake/${id}/missed`;

  function showToast(text) {
    let toast = document.querySelector('.toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.className = 'toast';
      document.body.appendChild(toast);
    }
    toast.textContent = text;
    toast.classList.add('toast-show');
    setTimeout(() => toast.classList.remove('toast-show'), 4500);
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    }[c]));
  }

  function renderPending(items) {
    if (!tableBody) return;
    if (!items.length) {
      tableBody.innerHTML = '';
      if (emptyMsg) emptyMsg.style.display = '';
      const t = document.querySelector('#pending-table');
      if (t) t.style.display = 'none';
      return;
    }
    if (emptyMsg) emptyMsg.style.display = 'none';
    const t = document.querySelector('#pending-table');
    if (t) t.style.display = '';
    tableBody.innerHTML = items.map((r) => `
      <tr>
        <td>${escapeHtml(r.name)} <span class="muted">${escapeHtml(r.dosage)}</span></td>
        <td>${escapeHtml(r.scheduled_time)}</td>
        <td class="muted">${escapeHtml(r.reminded_at || '')}</td>
        <td class="actions">
          <form method="post" action="${pendingTakenUrl(r.id)}">
            <input type="hidden" name="csrf_token" value="${csrfToken}">
            <button class="btn">Taken</button>
          </form>
          <form method="post" action="${pendingMissedUrl(r.id)}">
            <input type="hidden" name="csrf_token" value="${csrfToken}">
            <button class="btn btn-warn">Missed</button>
          </form>
        </td>
      </tr>
    `).join('');
  }

  async function refreshPending() {
    try {
      const r = await fetch('/api/pending', { credentials: 'same-origin' });
      if (!r.ok) return;
      const data = await r.json();
      renderPending(data.pending || []);
    } catch (e) {
      console.warn('refreshPending failed', e);
    }
  }

  if (!('EventSource' in window)) return;
  const es = new EventSource('/events');

  es.addEventListener('reminder', (e) => {
    let payload = {};
    try { payload = JSON.parse(e.data); } catch (_) {}
    const r = payload.reminder || {};
    showToast(`Time to take ${r.name || 'a medication'} ${r.dosage || ''} (${r.scheduled_time || ''})`);
    refreshPending();
  });

  es.addEventListener('connected', () => {
    refreshPending();
  });

  es.onerror = () => {
    // EventSource auto-reconnects; nothing to do.
  };
})();
