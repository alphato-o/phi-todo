async function api(path, opts) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch (e) {}
    throw new Error(`${res.status}: ${detail}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

function toast(msg, isError) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast' + (isError ? ' error' : '');
  setTimeout(() => el.classList.add('hidden'), 4000);
}

function taskCard(t) {
  const div = document.createElement('div');
  div.className = 'card' + (t.status === 'completed' ? ' done' : '');
  const due = t.due_date ? `<span class="chip due">due ${t.due_date}</span>` : '';
  const overdue = t.overdue ? '<span class="chip overdue">Overdue</span>' : '';
  const notes = t.notes ? `<div class="notes">${escapeHtml(t.notes)}</div>` : '';
  div.innerHTML = `
    <label class="check">
      <input type="checkbox" ${t.status === 'completed' ? 'checked' : ''} data-id="${t.id}" class="toggle">
    </label>
    <div class="body">
      <div class="title">${escapeHtml(t.title)}</div>
      <div class="meta">
        <span class="chip cat">${t.category}</span>
        <span class="chip pri ${t.priority}">${t.priority}</span>
        ${due} ${overdue}
      </div>
      ${notes}
    </div>
    <div class="actions">
      <button class="btn small breakdown" data-id="${t.id}">&#10024; Break down</button>
      <button class="btn small delete" data-id="${t.id}">&#128465;</button>
    </div>`;
  return div;
}

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

let allTasks = [];
let calCursor = new Date();

async function refresh() {
  const [tasks, stats] = await Promise.all([api('/api/tasks'), api('/api/stats')]);
  allTasks = tasks;
  document.getElementById('stats').textContent =
    `${stats.total} tasks · ${stats.active} active · ${stats.completed} done`;
  const active = document.getElementById('active-list');
  const completed = document.getElementById('completed-list');
  active.innerHTML = '';
  completed.innerHTML = '';
  for (const t of tasks) {
    (t.status === 'completed' ? completed : active).appendChild(taskCard(t));
  }
  renderCalendar();
}

function renderCalendar() {
  const year = calCursor.getFullYear();
  const month = calCursor.getMonth();
  document.getElementById('cal-month').textContent =
    calCursor.toLocaleString('en-US', { month: 'long', year: 'numeric' });
  const cal = document.getElementById('calendar');
  cal.innerHTML = '';
  for (const name of ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']) {
    const h = document.createElement('div');
    h.className = 'cal-dow';
    h.textContent = name;
    cal.appendChild(h);
  }
  const firstDow = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const todayKey = `${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, '0')}-${String(new Date().getDate()).padStart(2, '0')}`;
  for (let i = 0; i < firstDow; i++) {
    const pad = document.createElement('div');
    pad.className = 'cal-cell pad';
    cal.appendChild(pad);
  }
  for (let day = 1; day <= daysInMonth; day++) {
    const cellKey = new Date(year, month, day).toISOString().slice(0, 10);
    const cell = document.createElement('div');
    cell.className = 'cal-cell';
    const localKey = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    if (localKey === todayKey) cell.classList.add('today');
    const num = document.createElement('div');
    num.className = 'cal-day';
    num.textContent = day;
    cell.appendChild(num);
    for (const t of allTasks) {
      if (t.due_date === cellKey && t.status === 'active') {
        const chip = document.createElement('div');
        chip.className = 'cal-task ' + t.priority;
        chip.textContent = t.title;
        chip.title = `${t.title} (due ${t.due_date})`;
        cell.appendChild(chip);
      }
    }
    cal.appendChild(cell);
  }
}

document.getElementById('cal-prev').addEventListener('click', () => {
  calCursor = new Date(calCursor.getFullYear(), calCursor.getMonth() - 1, 1);
  renderCalendar();
});
document.getElementById('cal-next').addEventListener('click', () => {
  calCursor = new Date(calCursor.getFullYear(), calCursor.getMonth() + 1, 1);
  renderCalendar();
});

document.addEventListener('click', async (e) => {
  const btn = e.target.closest('button');
  if (!btn) return;
  try {
    if (btn.classList.contains('delete')) {
      await api(`/api/tasks/${btn.dataset.id}`, { method: 'DELETE' });
      refresh();
    } else if (btn.classList.contains('breakdown')) {
      btn.disabled = true;
      btn.textContent = 'Thinking...';
      const out = await api('/api/assistant/breakdown', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: Number(btn.dataset.id) }),
      });
      showModal('Suggested subtasks',
        '<ul>' + out.subtasks.map(s => `<li>${escapeHtml(s.title)} <em>(${escapeHtml(s.estimate || '')})</em></li>`).join('') + '</ul>');
      btn.disabled = false;
      btn.innerHTML = '&#10024; Break down';
    }
  } catch (err) {
    toast(err.message, true);
    btn.disabled = false;
  }
});

document.addEventListener('change', async (e) => {
  if (!e.target.classList.contains('toggle')) return;
  const status = e.target.checked ? 'completed' : 'active';
  await api(`/api/tasks/${e.target.dataset.id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  refresh();
});

document.getElementById('add-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  await api('/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: document.getElementById('add-title').value,
      category: document.getElementById('add-category').value,
      priority: document.getElementById('add-priority').value,
      due_date: document.getElementById('add-due').value || null,
    }),
  });
  e.target.reset();
  refresh();
});

document.getElementById('btn-prioritize').addEventListener('click', async (e) => {
  const btn = e.target;
  btn.disabled = true;
  btn.textContent = 'Phi is thinking...';
  try {
    const out = await api('/api/assistant/prioritize', { method: 'POST' });
    toast(`Phi re-prioritized ${out.applied} tasks for your week`);
    refresh();
  } catch (err) {
    toast(err.message, true);
  }
  btn.disabled = false;
  btn.innerHTML = '&#10024; Prioritize my week';
});

document.getElementById('btn-cleanup').addEventListener('click', async (e) => {
  const btn = e.target;
  btn.disabled = true;
  btn.textContent = 'Phi is tidying...';
  try {
    const out = await api('/api/assistant/cleanup', { method: 'POST' });
    showModal('List cleaned up',
      `<p>${escapeHtml(out.message)}</p><ul>` +
      out.deleted.map(d => `<li>#${d.id}: ${escapeHtml(d.reason)}</li>`).join('') + '</ul>');
    refresh();
  } catch (err) {
    toast(err.message, true);
  }
  btn.disabled = false;
  btn.innerHTML = '&#129529; Clean up my list';
});

function showModal(title, html) {
  document.getElementById('modal-title').textContent = title;
  document.getElementById('modal-body').innerHTML = html;
  document.getElementById('modal').classList.remove('hidden');
}

refresh();
