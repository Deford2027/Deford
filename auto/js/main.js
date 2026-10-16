// Мобильное меню
const burger = document.querySelector('.burger');
const nav = document.getElementById('nav');

burger.addEventListener('click', () => {
  const open = burger.getAttribute('aria-expanded') !== 'true';
  burger.setAttribute('aria-expanded', String(open));
  nav.classList.toggle('is-open', open);
});

nav.addEventListener('click', (e) => {
  if (e.target.closest('a')) {
    burger.setAttribute('aria-expanded', 'false');
    nav.classList.remove('is-open');
  }
});

// Выпадающий список телефонов
const phonesToggle = document.querySelector('.phones__toggle');
const phonesList = document.getElementById('phones-list');

phonesToggle.addEventListener('click', (e) => {
  e.stopPropagation();
  const open = phonesList.hidden;
  phonesList.hidden = !open;
  phonesToggle.setAttribute('aria-expanded', String(open));
});

document.addEventListener('click', (e) => {
  if (!phonesList.hidden && !e.target.closest('.phones')) {
    phonesList.hidden = true;
    phonesToggle.setAttribute('aria-expanded', 'false');
  }
});
