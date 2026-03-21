/* MoodBeats AI — Shared app utilities (loaded on every page via base.html) */

// ── Mobile nav toggle ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const menuBtn  = document.getElementById('menu-btn');
  const mobileMenu = document.getElementById('mobile-menu');
  if (menuBtn && mobileMenu) {
    menuBtn.addEventListener('click', () => mobileMenu.classList.toggle('hidden'));
  }
});

// ── Loading overlay ───────────────────────────────────────────────────────────
function showLoading(message) {
  const overlay = document.getElementById('loading-overlay');
  const msg     = document.getElementById('loading-message');
  if (overlay) {
    if (msg) msg.textContent = message || 'Analysing your mood…';
    overlay.classList.remove('hidden');
  }
}

function hideLoading() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) overlay.classList.add('hidden');
}

// ── Toast notifications ───────────────────────────────────────────────────────
function showToast(message, type) {
  // type: 'error' | 'success' | 'info'
  const colors = {
    error:   { bg: '#450a0a', border: '#7f1d1d', text: '#fca5a5' },
    success: { bg: '#052e16', border: '#166534', text: '#86efac' },
    info:    { bg: '#1e1b4b', border: '#3730a3', text: '#a5b4fc' },
  };
  const c = colors[type] || colors.info;

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.style.cssText = `background:${c.bg};border:1px solid ${c.border};color:${c.text}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'mb-slide-in 0.3s ease reverse';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ── Confidence bar — animate width after load ─────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const bar = document.querySelector('.confidence-fill');
  if (bar) {
    const target = bar.dataset.width || '0%';
    // Start at 0, let CSS transition do the animation
    bar.style.width = '0%';
    requestAnimationFrame(() => {
      requestAnimationFrame(() => { bar.style.width = target; });
    });
  }
});

// ── Text example pills ────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.example-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      const textarea = document.getElementById('mood-text');
      if (textarea) {
        textarea.value = pill.dataset.text;
        textarea.focus();
      }
    });
  });
});
