'use strict';

// ============================================================
// NAVEGACIÓ
// ============================================================
const header    = document.getElementById('header');
const navBurger = document.getElementById('nav-burger');
const navMenu   = document.getElementById('nav-menu');
const navLinks  = document.querySelectorAll('.nav__link:not(.nav__link--cta)');
const backTop   = document.getElementById('back-top');

function onScroll() {
  header.classList.toggle('scrolled', window.scrollY > 40);
  backTop.classList.toggle('is-visible', window.scrollY > 400);
  setActiveNav();
}
window.addEventListener('scroll', onScroll, { passive: true });
onScroll();

function setActiveNav() {
  const sections = document.querySelectorAll('section[id]');
  const y = window.scrollY + window.innerHeight / 3;
  let activeId = null;
  sections.forEach(sec => { if (sec.offsetTop <= y) activeId = sec.id; });
  navLinks.forEach(link => {
    const href = link.getAttribute('href')?.replace('#', '');
    link.classList.toggle('is-active', href === activeId);
  });
}

// Menú hamburguesa
navBurger.addEventListener('click', () => {
  const isOpen = navMenu.classList.toggle('is-open');
  navBurger.classList.toggle('is-open', isOpen);
  navBurger.setAttribute('aria-expanded', String(isOpen));
  document.body.style.overflow = isOpen ? 'hidden' : '';
});

navMenu.querySelectorAll('a').forEach(a => {
  a.addEventListener('click', () => {
    navMenu.classList.remove('is-open');
    navBurger.classList.remove('is-open');
    navBurger.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  });
});

// Tancar menú amb Escape
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && navMenu.classList.contains('is-open')) {
    navMenu.classList.remove('is-open');
    navBurger.classList.remove('is-open');
    navBurger.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  }
});

// ============================================================
// BOTÓ TORNAR A DALT
// ============================================================
backTop.addEventListener('click', () => {
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ============================================================
// ANIMACIONS EN SCROLL (IntersectionObserver)
// ============================================================
const animObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (!entry.isIntersecting) return;
    const siblings = Array.from(entry.target.parentElement.children)
      .filter(el => el.hasAttribute('data-animate'));
    const idx = siblings.indexOf(entry.target);
    entry.target.style.transitionDelay = `${idx * 70}ms`;
    entry.target.classList.add('is-visible');
    animObserver.unobserve(entry.target);
  });
}, { threshold: 0.12, rootMargin: '0px 0px -32px 0px' });

document.querySelectorAll('[data-animate]').forEach(el => animObserver.observe(el));

// ============================================================
// BARRES D'HABILITATS
// ============================================================
const skillsEl = document.querySelector('.sobre__skills');
if (skillsEl) {
  new IntersectionObserver(([entry], obs) => {
    if (!entry.isIntersecting) return;
    skillsEl.classList.add('skills-animated');
    obs.disconnect();
  }, { threshold: 0.4 }).observe(skillsEl);
}

// ============================================================
// COMPTADORS ANIMATS
// ============================================================
const statsEl = document.querySelector('.stats');
if (statsEl) {
  new IntersectionObserver(([entry], obs) => {
    if (!entry.isIntersecting) return;
    document.querySelectorAll('.stat__num[data-count]').forEach(el => {
      const target = +el.dataset.count;
      const dur    = 1600;
      const start  = performance.now();
      const tick   = now => {
        const p      = Math.min((now - start) / dur, 1);
        const eased  = 1 - Math.pow(1 - p, 3);
        el.textContent = Math.floor(eased * target);
        if (p < 1) requestAnimationFrame(tick);
        else el.textContent = target;
      };
      requestAnimationFrame(tick);
    });
    obs.disconnect();
  }, { threshold: 0.5 }).observe(statsEl);
}

// ============================================================
// FILTRE PORTFOLIO
// ============================================================
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('is-active'));
    btn.classList.add('is-active');
    const filter = btn.dataset.filter;
    document.querySelectorAll('.portfolio-item').forEach(item => {
      const match = filter === 'all' || item.dataset.category === filter;
      item.style.opacity = match ? '1' : '0.12';
      item.style.pointerEvents = match ? '' : 'none';
      item.style.transition = 'opacity 0.35s ease';
    });
  });
});

// ============================================================
// FORMULARI DE CONTACTE
// ============================================================
const contactForm = document.getElementById('contact-form');
if (contactForm) {
  contactForm.addEventListener('submit', async e => {
    e.preventDefault();

    const btnText = contactForm.querySelector('.btn-text');
    const submitBtn = contactForm.querySelector('button[type="submit"]');
    const original = btnText.textContent;

    // Validació
    let valid = true;
    contactForm.querySelectorAll('[required]').forEach(field => {
      if (!field.value.trim()) {
        field.style.borderColor = '#e83232';
        field.style.boxShadow   = '0 0 0 3px rgba(232,50,50,0.12)';
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

    // TODO: Integra el teu backend o servei de formulari aquí
    // Exemple amb Formspree:
    // const res = await fetch('https://formspree.io/f/XXXXXXXX', {
    //   method: 'POST', headers: { 'Accept': 'application/json' },
    //   body: new FormData(contactForm)
    // });
    // if (!res.ok) { btnText.textContent = 'Error. Torna-ho a provar.'; submitBtn.disabled = false; return; }

    await new Promise(r => setTimeout(r, 1200));

    btnText.textContent = '✓ Missatge enviat!';
    contactForm.reset();

    setTimeout(() => {
      btnText.textContent = original;
      submitBtn.disabled  = false;
    }, 3500);
  });
}
