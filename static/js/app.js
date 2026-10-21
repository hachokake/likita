document.addEventListener('alpine:init', () => {
  window.Alpine.data('scannerForm', () => ({
    token: '',
    result: null,
  }));
});

function hideSplash() {
  const splash = document.querySelector('[data-app-splash]');
  if (!splash) return;

  const finish = () => {
    splash.classList.add('is-hidden');
    try { sessionStorage.setItem('likita:splash', '1'); } catch (e) {}
  };

  if (document.documentElement.classList.contains('splash-seen')) {
    finish();
    return;
  }

  // Première visite de la session : on laisse l'intro respirer ~900 ms, sans dépasser 1,6 s même si la page est lente.
  const shownAt = performance.now();
  const minVisible = 900;
  const maxVisible = 1600;
  let done = false;
  const complete = () => {
    if (done) return;
    done = true;
    finish();
  };
  const onLoaded = () => {
    const remaining = Math.max(0, minVisible - (performance.now() - shownAt));
    window.setTimeout(complete, remaining);
  };
  if (document.readyState === 'complete') onLoaded();
  else window.addEventListener('load', onLoaded, { once: true });
  window.setTimeout(complete, maxVisible);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', hideSplash);
} else {
  hideSplash();
}