document.addEventListener('alpine:init', () => {
  window.Alpine.data('scannerForm', () => ({
    token: '',
    result: null,
  }));
});

function hideSplashAfterDelay() {
  const splash = document.querySelector('[data-app-splash]');

  window.setTimeout(() => {
    document.body.classList.remove('app-loading');
    splash?.classList.add('is-hidden');
  }, 1500);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', hideSplashAfterDelay);
} else {
  hideSplashAfterDelay();
}