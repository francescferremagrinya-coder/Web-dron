'use strict';

// Activa animacions CSS — sense JS el contingut és sempre visible
document.documentElement.classList.add('js');

// ─── LOADER ────────────────────────────────────────────────
const loader = document.getElementById('loader');

window.addEventListener('load', () => {
  setTimeout(() => {
    if (loader) loader.classList.add('is-done');
    const hero = document.querySelector('.hero');
    if (hero) hero.classList.add('is-loaded');
    document.body.classList.add('is-loaded');
  }, 1600);
});

// ─── SCROLL PROGRESS BAR ──────────────────────────────────
const scrollBar = document.getElementById('scroll-bar');
const backTop   = document.getElementById('back-top');
const header    = document.getElementById('header');

function onScroll() {
  const max      = document.documentElement.scrollHeight - window.innerHeight;
  const progress = max > 0 ? (window.scrollY / max) * 100 : 0;
  if (scrollBar) scrollBar.style.width = progress + '%';
  if (header)    header.classList.toggle('scrolled',   window.scrollY > 50);
  if (backTop)   backTop.classList.toggle('is-visible', window.scrollY > 400);
  setActiveNav();
}
window.addEventListener('scroll', onScroll, { passive: true });
onScroll();

// ─── NAVEGACIÓ ACTIVA ──────────────────────────────────────
const navLinks = document.querySelectorAll('.nav__link:not(.nav__link--cta)');

function setActiveNav() {
  const y = window.scrollY + window.innerHeight / 3;
  let active = null;
  document.querySelectorAll('section[id]').forEach(sec => {
    if (sec.offsetTop <= y) active = sec.id;
  });
  navLinks.forEach(l => {
    l.classList.toggle('is-active', l.getAttribute('href') === '#' + active);
  });
}

// ─── MENÚ MÒBIL ────────────────────────────────────────────
const navBurger = document.getElementById('nav-burger');
const navMenu   = document.getElementById('nav-menu');

function openMenu() {
  if (!navBurger || !navMenu) return;
  navMenu.classList.add('is-open');
  var s = navMenu.style;
  s.display    = 'flex';
  s.position   = 'fixed';
  s.top        = '0';
  s.left       = '0';
  s.width      = '100vw';
  s.height     = '100vh';
  s.flexDirection  = 'column';
  s.justifyContent = 'center';
  s.alignItems     = 'center';
  s.gap        = '36px';
  s.background = 'rgba(5,5,7,0.97)';
  s.zIndex     = '99999';
  s.visibility = 'visible';
  s.opacity    = '1';
  s.pointerEvents = 'auto';
  navBurger.classList.add('is-open');
  navBurger.setAttribute('aria-expanded', 'true');
  document.body.style.overflow = 'hidden';
}

function closeMenu() {
  if (!navBurger || !navMenu) return;
  navMenu.classList.remove('is-open');
  navMenu.style.cssText = '';
  navBurger.classList.remove('is-open');
  navBurger.setAttribute('aria-expanded', 'false');
  document.body.style.overflow = '';
}

function toggleMenu() {
  navMenu && navMenu.classList.contains('is-open') ? closeMenu() : openMenu();
}

if (navBurger) {
  // <button> sempre rep click a iOS/Android — NO afegir touchstart (causaria doble toggle)
  navBurger.addEventListener('click', toggleMenu);
}

if (navMenu) {
  navMenu.querySelectorAll('a').forEach(a => a.addEventListener('click', closeMenu));
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeMenu(); });

// ─── CURSOR PERSONALITZAT ─────────────────────────────────
const ring = document.getElementById('cursor-ring');
const dot  = document.getElementById('cursor-dot');
let   mx = -999, my = -999, rx = -999, ry = -999;

if (ring && dot && window.matchMedia('(hover: hover)').matches) {
  document.addEventListener('mousemove', e => {
    mx = e.clientX; my = e.clientY;
    dot.style.left  = mx + 'px';
    dot.style.top   = my + 'px';
    dot.classList.add('is-visible');
    ring.classList.add('is-visible');
  });

  (function animateCursor() {
    rx += (mx - rx) * 0.14;
    ry += (my - ry) * 0.14;
    ring.style.left = rx + 'px';
    ring.style.top  = ry + 'px';
    requestAnimationFrame(animateCursor);
  })();

  document.addEventListener('mousedown', () => ring.classList.add('is-click'));
  document.addEventListener('mouseup',   () => ring.classList.remove('is-click'));

  document.querySelectorAll('a, button, .portfolio-item, .filter-btn').forEach(el => {
    el.addEventListener('mouseenter', () => ring.classList.add('is-hover'));
    el.addEventListener('mouseleave', () => ring.classList.remove('is-hover'));
  });
}

// ─── BACK TO TOP ──────────────────────────────────────────
if (backTop) {
  backTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
}

// ─── ANIMACIONS EN SCROLL ─────────────────────────────────
// Marca tots com visibles immediatament (fallback segur)
document.querySelectorAll('[data-animate]').forEach(el => el.classList.add('is-visible'));

// Millora progressiva: si IntersectionObserver disponible, anima en entrada
if ('IntersectionObserver' in window) {
  document.querySelectorAll('[data-animate]').forEach(el => el.classList.remove('is-visible'));
  const animObs = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const siblings = Array.from(entry.target.parentElement.children)
        .filter(el => el.hasAttribute('data-animate'));
      const idx = siblings.indexOf(entry.target);
      entry.target.style.transitionDelay = (idx * 80) + 'ms';
      entry.target.classList.add('is-visible');
      animObs.unobserve(entry.target);
    });
  }, { threshold: 0.05 });
  document.querySelectorAll('[data-animate]').forEach(el => animObs.observe(el));
}

// ─── BARRES D'HABILITATS ──────────────────────────────────
const skillsEl = document.querySelector('.sobre__skills');
if (skillsEl) {
  new IntersectionObserver(([e], obs) => {
    if (!e.isIntersecting) return;
    skillsEl.classList.add('skills-animated');
    obs.disconnect();
  }, { threshold: 0.3 }).observe(skillsEl);
}

// ─── COMPTADORS ANIMATS ────────────────────────────────────
(function () {
  var counters = document.querySelectorAll('.stat__n[data-count]');
  if (!counters.length) return;
  var done = false;

  function animateCounter(el) {
    var target = +el.dataset.count;
    var step = 0, steps = 50;
    var iv = setInterval(function () {
      step++;
      var p = step / steps;
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(eased * target);
      if (step >= steps) { el.textContent = target; clearInterval(iv); }
    }, 30);
  }

  function run() {
    if (done) return;
    done = true;
    counters.forEach(animateCounter);
  }

  // Trigger 1: quan l'usuari fa scroll fins als comptadors
  window.addEventListener('scroll', function () {
    counters.forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.top < window.innerHeight && r.bottom > 0) run();
    });
  }, { passive: true });

  // Trigger 2: check quan la pàgina acaba de carregar
  window.addEventListener('load', checkScroll);

  // Trigger 3: IntersectionObserver per màxima compatibilitat
  if ('IntersectionObserver' in window) {
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { run(); obs.disconnect(); } });
    }, { threshold: 0.05, rootMargin: '0px 0px -50px 0px' });
    counters.forEach(function (el) { obs.observe(el); });
  }
}());

// ─── FILTRE PORTFOLIO ──────────────────────────────────────
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('is-active'));
    btn.classList.add('is-active');
    const f = btn.dataset.filter;
    document.querySelectorAll('.portfolio-item').forEach(item => {
      const show = f === 'all' || item.dataset.category === f;
      item.style.opacity        = show ? '1' : '0.12';
      item.style.pointerEvents  = show ? '' : 'none';
      item.style.transition     = 'opacity .35s ease';
    });
  });
});

// ─── LIGHTBOX ──────────────────────────────────────────────
const lightbox      = document.getElementById('lightbox');
const lightboxImg   = document.getElementById('lightbox-img');
const lightboxClose = document.getElementById('lightbox-close');

function openLightbox(imgEl) {
  if (!lightbox || !lightboxImg || !imgEl) return;
  lightboxImg.src = imgEl.src;
  lightboxImg.alt = imgEl.alt;
  lightbox.classList.add('is-open');
  document.body.style.overflow = 'hidden';
}

function closeLightbox() {
  if (!lightbox) return;
  lightbox.classList.remove('is-open');
  document.body.style.overflow = '';
}

document.querySelectorAll('.portfolio-item').forEach(item => {
  let touchStartY = 0;

  // Guardem posició Y inicial per distingir tap de scroll
  item.addEventListener('touchstart', e => {
    touchStartY = e.touches[0].clientY;
  }, { passive: true });

  // touchend: obre lightbox si no és scroll (delta < 8px)
  // preventDefault evita el click sintètic posterior (evita doble disparada)
  item.addEventListener('touchend', function (e) {
    const delta = Math.abs(e.changedTouches[0].clientY - touchStartY);
    if (delta < 8) {
      e.preventDefault();
      openLightbox(item.querySelector('img'));
    }
  }, { passive: false });

  // click: desktop (el touchend ja fa preventDefault en tap mòbil)
  item.addEventListener('click', () => {
    openLightbox(item.querySelector('img'));
  });
});

if (lightboxClose) lightboxClose.addEventListener('click', closeLightbox);
if (lightbox) {
  lightbox.addEventListener('click', e => { if (e.target === lightbox) closeLightbox(); });
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeLightbox(); });

// ─── FORMULARI ────────────────────────────────────────────
const form = document.getElementById('contact-form');
if (form) {
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const btnText   = form.querySelector('.btn-text');
    const submitBtn = form.querySelector('[type="submit"]');
    if (!btnText || !submitBtn) return;
    const original  = btnText.textContent;

    let valid = true;
    form.querySelectorAll('[required]').forEach(field => {
      const err = !field.value.trim();
      field.style.borderColor = err ? '#e83232' : '';
      field.style.boxShadow   = err ? '0 0 0 3px rgba(232,50,50,0.12)' : '';
      if (err) {
        valid = false;
        field.addEventListener('input', () => {
          field.style.borderColor = '';
          field.style.boxShadow   = '';
        }, { once: true });
      }
    });
    if (!valid) return;

    btnText.textContent = 'Enviant...';
    submitBtn.disabled  = true;

    try {
      const res = await fetch('https://api.web3forms.com/submit', {
        method: 'POST',
        headers: { 'Accept': 'application/json' },
        body: new FormData(form)
      });
      const data = await res.json();
      if (data.success) {
        btnText.textContent = '✓ Missatge enviat!';
        form.reset();
        setTimeout(() => { btnText.textContent = original; submitBtn.disabled = false; }, 3500);
      } else {
        throw new Error(data.message || 'Error');
      }
    } catch {
      btnText.textContent = '✗ Error. Torna a intentar-ho.';
      submitBtn.disabled = false;
      setTimeout(() => { btnText.textContent = original; }, 4000);
    }
  });
}
