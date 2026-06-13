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

function toggleMenu() {
  if (!navBurger || !navMenu) return;
  const open = navMenu.classList.toggle('is-open');
  navBurger.classList.toggle('is-open', open);
  navBurger.setAttribute('aria-expanded', String(open));
  document.body.style.overflow = open ? 'hidden' : '';
}

function closeMenu() {
  if (!navBurger || !navMenu) return;
  navMenu.classList.remove('is-open');
  navBurger.classList.remove('is-open');
  navBurger.setAttribute('aria-expanded', 'false');
  document.body.style.overflow = '';
}

// Mou el menú fora del header per escapar del seu stacking context (z-index:1000)
if (header && navMenu) header.after(navMenu);

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

// ─── PARALLAX ─────────────────────────────────────────────
(function () {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const heroEl      = document.querySelector('.hero');
  const heroContent = document.querySelector('.hero__content');
  const heroCoords  = document.querySelector('.hero__coords');
  const heroScrollEl = document.querySelector('.hero__scroll');
  const droneSec    = document.querySelector('.drone-showcase');
  const droneBg     = document.querySelector('.drone-showcase__bg');

  function raf(fn) { requestAnimationFrame(fn); }

  let ticking = false;
  window.addEventListener('scroll', function () {
    if (!ticking) { raf(updateParallax); ticking = true; }
  }, { passive: true });

  function updateParallax() {
    ticking = false;
    const y = window.scrollY;

    // Hero content: flota cap amunt i es desvaneix
    if (heroContent && heroEl) {
      const h = heroEl.offsetHeight;
      const p = Math.min(y / h, 1);
      heroContent.style.transform = 'translateY(' + (y * 0.18) + 'px)';
      heroContent.style.opacity   = String(Math.max(1 - p * 2.2, 0));
    }
    if (heroCoords)   heroCoords.style.transform  = 'translateY(' + (y * 0.28) + 'px)';
    if (heroScrollEl) heroScrollEl.style.opacity  = String(Math.max(1 - y / 180, 0));

    // Drone showcase: fons es mou a velocitat diferent
    if (droneBg && droneSec) {
      const r = droneSec.getBoundingClientRect();
      if (r.bottom > 0 && r.top < window.innerHeight) {
        droneBg.style.transform = 'translateY(' + ((window.innerHeight - r.top) * 0.12) + 'px)';
      }
    }
  }

  updateParallax();
}());

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
const lightbox       = document.getElementById('lightbox');
const lightboxImg    = document.getElementById('lightbox-img');
const lightboxClose  = document.getElementById('lightbox-close');
const lightboxPrev   = document.getElementById('lightbox-prev');
const lightboxNext   = document.getElementById('lightbox-next');
const lightboxCat    = document.getElementById('lightbox-cat');
const lightboxTitle  = document.getElementById('lightbox-title');
const lightboxCount  = document.getElementById('lightbox-counter');

const galleryItems = Array.from(document.querySelectorAll('.portfolio-item'));
let lbIndex = 0;

function openLightbox(idx) {
  const item = galleryItems[idx];
  if (!lightbox || !lightboxImg || !item) return;
  lbIndex = idx;
  const img = item.querySelector('img');
  lightboxImg.src = img.src;
  lightboxImg.alt = img.alt;
  if (lightboxCat)   lightboxCat.textContent   = item.querySelector('.portfolio-item__cat')?.textContent || '';
  if (lightboxTitle) lightboxTitle.textContent = item.querySelector('h3')?.textContent || '';
  if (lightboxCount) lightboxCount.textContent = (idx + 1) + ' / ' + galleryItems.length;
  lightbox.classList.add('is-open');
  document.body.style.overflow = 'hidden';
}

function closeLightbox() {
  if (!lightbox) return;
  lightbox.classList.remove('is-open');
  document.body.style.overflow = '';
}

function lbNav(dir) {
  openLightbox((lbIndex + dir + galleryItems.length) % galleryItems.length);
}

galleryItems.forEach((item, i) => {
  let startY = 0;
  item.addEventListener('touchstart', e => { startY = e.touches[0].clientY; }, { passive: true });
  item.addEventListener('touchend', e => {
    if (Math.abs(e.changedTouches[0].clientY - startY) < 8) {
      e.preventDefault(); openLightbox(i);
    }
  }, { passive: false });
  item.addEventListener('click', () => openLightbox(i));
});

if (lightboxClose) lightboxClose.addEventListener('click', closeLightbox);
if (lightboxPrev)  lightboxPrev.addEventListener('click', () => lbNav(-1));
if (lightboxNext)  lightboxNext.addEventListener('click', () => lbNav(1));
if (lightbox) {
  lightbox.addEventListener('click', e => { if (e.target === lightbox) closeLightbox(); });
  let lbSwipeX = 0;
  lightbox.addEventListener('touchstart', e => { lbSwipeX = e.touches[0].clientX; }, { passive: true });
  lightbox.addEventListener('touchend', e => {
    const dx = e.changedTouches[0].clientX - lbSwipeX;
    if (Math.abs(dx) > 50) lbNav(dx < 0 ? 1 : -1);
  }, { passive: true });
}
document.addEventListener('keydown', e => {
  if (!lightbox?.classList.contains('is-open')) return;
  if (e.key === 'Escape')      closeLightbox();
  if (e.key === 'ArrowLeft')   lbNav(-1);
  if (e.key === 'ArrowRight')  lbNav(1);
});

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

// ─── PARTÍCULES HERO ──────────────────────────────────
(function () {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const canvas = document.getElementById('hero-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let particles = [], w, h;

  function resize() {
    w = canvas.width  = canvas.offsetWidth;
    h = canvas.height = canvas.offsetHeight;
  }

  function mkP() {
    return {
      x:    Math.random() * w,
      y:    Math.random() * h,
      r:    Math.random() * 1.8 + 0.4,
      a:    Math.random() * 0.65 + 0.15,
      dx:   (Math.random() - 0.5) * 0.28,
      dy:   -(Math.random() * 0.3 + 0.08),
      gold: Math.random() > 0.42,
      glow: Math.random() > 0.62
    };
  }

  function init() {
    resize();
    particles = Array.from({ length: 70 }, mkP);
  }

  function frame() {
    ctx.clearRect(0, 0, w, h);
    particles.forEach(p => {
      ctx.save();
      ctx.globalAlpha = p.a;
      if (p.glow) {
        ctx.shadowBlur  = 10;
        ctx.shadowColor = p.gold ? '#e8a020' : 'rgba(240,240,248,0.8)';
      }
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = p.gold ? '#e8a020' : 'rgba(240,240,248,0.85)';
      ctx.fill();
      ctx.restore();

      p.x  += p.dx;
      p.y  += p.dy;
      p.dx += (Math.random() - 0.5) * 0.012;
      p.dy += (Math.random() - 0.5) * 0.006;
      p.dx  = Math.max(-0.38, Math.min(0.38, p.dx));
      p.dy  = Math.max(-0.45, Math.min(-0.06, p.dy));

      if (p.y < -10) { Object.assign(p, mkP()); p.y = h + 10; }
      if (p.x < -10) p.x = w + 10;
      if (p.x > w + 10) p.x = -10;
    });
    requestAnimationFrame(frame);
  }

  window.addEventListener('resize', resize, { passive: true });
  init();
  frame();
}());

// ─── 3D TILT ──────────────────────────────────────────
if (window.matchMedia('(hover: hover)').matches && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  document.querySelectorAll('[data-tilt]').forEach(el => {
    el.style.willChange = 'transform';

    el.addEventListener('mousemove', e => {
      const rect = el.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width  - 0.5;
      const y = (e.clientY - rect.top)  / rect.height - 0.5;
      el.style.transition = 'none';
      el.style.transform  = `perspective(700px) rotateX(${-y * 8}deg) rotateY(${x * 8}deg) translateY(-6px) scale(1.02)`;
    });

    el.addEventListener('mouseleave', () => {
      el.style.transition = 'transform 0.6s cubic-bezier(0.16, 1, 0.3, 1)';
      el.style.transform  = '';
      setTimeout(() => { el.style.transition = ''; }, 650);
    });
  });
}
