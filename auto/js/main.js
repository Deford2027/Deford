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

// Квиз из четырёх шагов
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

  const show = (i) => {
    current = i;
    steps.forEach((s, n) => s.classList.toggle('is-active', n === i));
    bar.style.width = `${((i + 1) / steps.length) * 100}%`;
    label.textContent = `Шаг ${i + 1} из ${steps.length}`;
    prev.hidden = i === 0;
    next.hidden = i === steps.length - 1;
    submit.hidden = i !== steps.length - 1;
    note.textContent = '';
  };

  next.addEventListener('click', () => {
    if (!steps[current].querySelector('input:checked')) {
      note.textContent = 'Выберите один из вариантов.';
      return;
    }
    show(current + 1);
  });
  prev.addEventListener('click', () => show(current - 1));

  // Выбор варианта сразу ведёт к следующему вопросу
  steps.slice(0, -1).forEach((step, i) => {
    step.addEventListener('change', () => setTimeout(() => show(i + 1), 250));
  });

  quiz.addEventListener('submit', (e) => {
    e.preventDefault();
    fakeSubmit(steps[steps.length - 1], note);
  });
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

// Партнёры: «Показать ещё»
const more = document.getElementById('partners-more');
if (more) {
  more.addEventListener('click', () => {
    document.querySelectorAll('#partners .partner[hidden]').forEach((p) => { p.hidden = false; });
    more.hidden = true;
  });
}

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
