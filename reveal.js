/* Scroll reveal: 400ms fade plus 12px rise, 60ms stagger.
   design_system.md MOTION. Reduced motion resolves instantly via CSS. */
(function () {
  var items = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window)) {
    items.forEach(function (el) { el.classList.add('is-in'); });
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    var n = 0;
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      var el = entry.target;
      el.style.transitionDelay = (n * 60) + 'ms';
      n += 1;
      el.classList.add('is-in');
      io.unobserve(el);
    });
  }, { rootMargin: '0px 0px -10% 0px', threshold: 0.05 });

  items.forEach(function (el) { io.observe(el); });
})();
