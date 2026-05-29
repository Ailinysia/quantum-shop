/* ── Time spinners ────────────────────────────────────────────────────────── */
document.querySelectorAll('.spinner-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const targetId = btn.dataset.target;
    const input = document.getElementById(targetId);
    if (!input) return;

    const dir   = parseInt(btn.dataset.dir, 10);
    const step  = parseInt(btn.dataset.step  || '1', 10);
    const min   = parseInt(btn.dataset.min,  10);
    const max   = parseInt(btn.dataset.max,  10);

    let val = parseInt(input.value, 10) + dir * step;
    if (val < min) val = max;
    if (val > max) val = min;

    input.value = String(val).padStart(2, '0');
  });
});

/* ── Shop filter ──────────────────────────────────────────────────────────── */
const filterBtns = document.querySelectorAll('.filter-btn');
if (filterBtns.length) {
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const filter = btn.dataset.filter;
      const boysSec  = document.getElementById('section-boys');
      const girlsSec = document.getElementById('section-girls');

      if (!boysSec || !girlsSec) return;

      if (filter === 'all') {
        boysSec.style.display  = '';
        girlsSec.style.display = '';
      } else if (filter === 'boys') {
        boysSec.style.display  = '';
        girlsSec.style.display = 'none';
      } else {
        boysSec.style.display  = 'none';
        girlsSec.style.display = '';
      }
    });
  });
}
