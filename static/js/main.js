// Global JS helpers
document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss flash messages after 4s
  document.querySelectorAll('.alert-dismissible').forEach(el => {
    setTimeout(() => {
      const alert = bootstrap.Alert.getOrCreateInstance(el);
      alert.close();
    }, 4000);
  });

  // Show / hide password buttons
  document.querySelectorAll('[data-toggle-password]').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = document.getElementById(btn.dataset.togglePassword);
      if (!input) return;
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      btn.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
      const icon = btn.querySelector('.bi');
      if (icon) icon.className = show ? 'bi bi-eye-slash' : 'bi bi-eye';
    });
  });

  // Category tabs that filter a product grid in place
  document.querySelectorAll('[data-filter-tabs]').forEach(tabs => {
    const grid = document.querySelector(tabs.dataset.filterTabs);
    if (!grid) return;
    const items = grid.querySelectorAll('[data-category]');
    const buttons = tabs.querySelectorAll('[data-filter]');

    // Hide tabs for categories that have no products on this page
    buttons.forEach(btn => {
      const f = btn.dataset.filter;
      if (f !== 'all' && !grid.querySelector('[data-category="' + f + '"]')) btn.hidden = true;
    });

    buttons.forEach(btn => btn.addEventListener('click', () => {
      const f = btn.dataset.filter;
      buttons.forEach(b => {
        const active = b === btn;
        b.classList.toggle('is-active', active);
        b.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
      items.forEach(el => { el.hidden = !(f === 'all' || el.dataset.category === f); });
    }));
  });

  // Product gallery thumbnails swap the main image
  document.querySelectorAll('[data-gallery]').forEach(box => {
    const main = document.querySelector(box.dataset.gallery);
    const img = main && main.querySelector('img');
    box.querySelectorAll('button[data-src]').forEach(btn => btn.addEventListener('click', () => {
      if (!img) return;
      img.src = btn.dataset.src;
      box.querySelectorAll('button').forEach(b => b.classList.toggle('is-active', b === btn));
    }));
  });
});
