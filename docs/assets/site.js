// Tema claro/escuro, com a mesma chave usada em datafixers.org
(function () {
  var root = document.documentElement;
  try { root.setAttribute('data-theme', localStorage.getItem('df-theme') || 'light'); }
  catch (e) { root.setAttribute('data-theme', 'light'); }
  document.addEventListener('DOMContentLoaded', function () {
    var btn = document.getElementById('themeToggle');
    if (!btn) return;
    btn.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('df-theme', next); } catch (e) {}
    });
  });
})();
