document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.info-wrap').forEach(function (wrap) {
    var icon = wrap.querySelector('.info-icon');
    if (!icon) return;

    icon.addEventListener('click', function (e) {
      e.stopPropagation();
      var isOpen = wrap.classList.contains('open');
      document.querySelectorAll('.info-wrap.open').forEach(function (w) {
        w.classList.remove('open');
      });
      if (!isOpen) wrap.classList.add('open');
    });

    icon.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        icon.click();
      }
      if (e.key === 'Escape') wrap.classList.remove('open');
    });

    icon.setAttribute('tabindex', '0');
    icon.setAttribute('role', 'button');
  });

  document.addEventListener('click', function () {
    document.querySelectorAll('.info-wrap.open').forEach(function (w) {
      w.classList.remove('open');
    });
  });
});

function makeInfo(text) {
  return '<span class="info-wrap">' +
    '<span class="info-icon" aria-label="More information">i</span>' +
    '<span class="info-tooltip">' + text + '</span>' +
    '</span>';
}
