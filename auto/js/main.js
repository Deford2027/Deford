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

// Простая проверка формы: имя, телефон и согласие
function validate(form) {
  let ok = true;
  form.querySelectorAll('input[required]').forEach((input) => {
    const bad = input.type === 'checkbox'
      ? !input.checked
      : input.type === 'tel'
        ? input.value.replace(/\D/g, '').length < 10
        : !input.value.trim();
    const target = input.type === 'checkbox' ? input.closest('.consent') : input;
    target.classList.toggle('is-invalid', bad);
    if (bad) ok = false;
  });
  return ok;
}

// Отправка заявок не подключена: показываем сообщение вместо запроса на сервер
function fakeSubmit(form, note) {
  note.textContent = validate(form)
    ? 'Спасибо! Форма заполнена. Отправку заявок нужно подключить к вашему CRM или почте.'
    : 'Заполните имя, телефон и отметьте согласие.';
}

document.querySelectorAll('.lead-form, .service-form').forEach((form) => {
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    fakeSubmit(form, form.querySelector('.form-note'));
  });
});

// Квиз из четырёх шагов, как на plutosauto.ru
const quiz = document.getElementById('quiz-form');
if (quiz) {
  const steps = [...quiz.querySelectorAll('.quiz__step')];
  const bar = document.getElementById('quiz-bar');
  const label = document.getElementById('quiz-label');
  const prev = document.getElementById('quiz-prev');
  const next = document.getElementById('quiz-next');
  const submit = document.getElementById('quiz-submit');
  const note = document.getElementById('quiz-note');
  let current = 0;

  // Годы выпуска 2000–2026
  quiz.querySelectorAll('select[data-years]').forEach((select) => {
    for (let year = 2000; year <= 2026; year += 1) select.add(new Option(year, year));
  });

  const show = (i) => {
    current = i;
    steps.forEach((s, n) => s.classList.toggle('is-active', n === i));
    const progress = steps[i].dataset.progress;
    bar.style.width = `${progress}%`;
    label.textContent = `${progress} % пройдено`;
    prev.hidden = i === 0;
    next.hidden = i === steps.length - 1;
    submit.hidden = i !== steps.length - 1;
    note.textContent = '';
  };

  next.addEventListener('click', () => {
    if (!validate(steps[current])) {
      note.textContent = 'Заполните обязательные поля.';
      return;
    }
    show(current + 1);
  });
  prev.addEventListener('click', () => show(current - 1));

  quiz.addEventListener('submit', (e) => {
    e.preventDefault();
    fakeSubmit(steps[steps.length - 1], note);
  });

  show(0);
}

// Слайдер кейсов
const slider = document.getElementById('cases-slider');
if (slider) {
  const slides = [...slider.querySelectorAll('.slide')];
  const count = document.getElementById('cases-count');
  let index = 0;
  slider.querySelectorAll('.arrow').forEach((btn) => {
    btn.addEventListener('click', () => {
      index = (index + Number(btn.dataset.dir) + slides.length) % slides.length;
      slides.forEach((s, n) => s.classList.toggle('is-active', n === index));
      count.textContent = `${index + 1} / ${slides.length}`;
    });
  });
}

// Галереи кейсов: миниатюры переключают большое фото
document.querySelectorAll('.gallery').forEach((gallery) => {
  const main = gallery.querySelector('.gallery__main');
  const thumbs = [...gallery.querySelectorAll('.gallery__thumbs button')];
  thumbs.forEach((btn) => {
    btn.addEventListener('click', () => {
      main.src = btn.querySelector('img').src;
      thumbs.forEach((b) => b.classList.toggle('is-active', b === btn));
    });
  });
});

// «Показать ещё» для партнёров и вопросов
document.querySelectorAll('[data-more]').forEach((more) => {
  more.addEventListener('click', () => {
    document.querySelectorAll(`${more.dataset.more}[hidden]`).forEach((item) => { item.hidden = false; });
    more.hidden = true;
  });
});

// Кнопка «Наверх»
const toTop = document.querySelector('.to-top');
if (toTop) {
  const onScroll = () => toTop.classList.toggle('is-visible', window.scrollY > window.innerHeight);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  toTop.addEventListener('click', (e) => {
    e.preventDefault();
    window.scrollTo({ top: 0 });
  });
}
