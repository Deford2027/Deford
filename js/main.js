(function () {
  // Мобильное меню
  var burger = document.querySelector('.header__burger');
  var nav = document.querySelector('.header__nav');

  function setMenu(open) {
    burger.setAttribute('aria-expanded', String(open));
    burger.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
    nav.classList.toggle('is-open', open);
  }

  burger.addEventListener('click', function () {
    setMenu(burger.getAttribute('aria-expanded') !== 'true');
  });

  nav.addEventListener('click', function (e) {
    if (e.target.closest('a')) setMenu(false);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') setMenu(false);
  });

  // Портфолио: фильтр по технике
  var chips = document.querySelectorAll('.chip');
  var items = document.querySelectorAll('.gallery__item');
  var track = document.querySelector('.gallery__track');
  var empty = document.querySelector('.gallery__empty');

  function applyFilter(filter) {
    var visible = 0;
    items.forEach(function (item) {
      var show = filter === 'all' || item.dataset.cat === filter;
      item.hidden = !show;
      if (show) visible++;
    });
    empty.hidden = visible > 0;
    track.scrollLeft = 0;
    updateNav();
  }

  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      chips.forEach(function (c) {
        c.classList.toggle('is-active', c === chip);
        c.setAttribute('aria-pressed', String(c === chip));
      });
      applyFilter(chip.dataset.filter);
    });
  });

  // Портфолио: стрелки слайдера
  var navButtons = document.querySelectorAll('.slider-nav__btn');

  function updateNav() {
    var max = track.scrollWidth - track.clientWidth;
    // Если все работы помещаются, стрелки остаются в обычном виде, как в макете
    if (max <= 1) {
      navButtons.forEach(function (b) { b.disabled = false; });
      return;
    }
    navButtons[0].disabled = track.scrollLeft <= 1;
    navButtons[1].disabled = track.scrollLeft >= max - 1;
  }

  navButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var item = track.querySelector('.gallery__item:not([hidden])');
      var step = item ? item.getBoundingClientRect().width + 19 : track.clientWidth;
      track.scrollBy({ left: step * Number(btn.dataset.dir), behavior: 'smooth' });
    });
  });

  track.addEventListener('scroll', updateNav, { passive: true });
  window.addEventListener('resize', updateNav);

  var active = document.querySelector('.chip.is-active');
  applyFilter(active ? active.dataset.filter : 'all');
})();
