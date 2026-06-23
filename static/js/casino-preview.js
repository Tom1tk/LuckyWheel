// Standalone init for casino-preview.html (kept external to satisfy CSP).
window.createCasinoScene(document.getElementById('scene'), {
  lowSpec: new URLSearchParams(location.search).has('lowspec'),
});
