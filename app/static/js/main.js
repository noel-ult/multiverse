/* Global navigation, feedback, and deliberately lightweight decoration. */
(() => {
  'use strict';
  const toggle = document.querySelector('#navToggle'), nav = document.querySelector('#mainNav');
  const closeNav = () => { if (nav) nav.classList.remove('open'); if (toggle) { toggle.setAttribute('aria-expanded', 'false'); toggle.setAttribute('aria-label', 'Open navigation'); } document.body.classList.remove('menu-open'); };
  if (toggle && nav) toggle.addEventListener('click', () => { const open = !nav.classList.contains('open'); nav.classList.toggle('open', open); toggle.setAttribute('aria-expanded', String(open)); toggle.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation'); document.body.classList.toggle('menu-open', open); });
  document.querySelectorAll('#mainNav a').forEach(a => a.addEventListener('click', closeNav)); document.addEventListener('keydown', e => { if (e.key === 'Escape') closeNav(); });
  document.querySelectorAll('[data-auto-dismiss]').forEach(el => { const remove = () => { el.classList.add('is-leaving'); setTimeout(() => el.remove(), 220); }; setTimeout(remove, 4500); el.querySelector('button')?.addEventListener('click', remove); });
  document.querySelectorAll('[data-password-toggle]').forEach(button => button.addEventListener('click', () => { const input = document.querySelector(button.dataset.passwordToggle); if (!input) return; const show = input.type === 'password'; input.type = show ? 'text' : 'password'; button.textContent = show ? 'HIDE' : 'SHOW'; }));
  document.querySelectorAll('[data-loading-form]').forEach(form => form.addEventListener('submit', () => { const button = form.querySelector('[type=submit]'); if (button && form.checkValidity()) { button.disabled = true; button.textContent = button.dataset.submitText || 'WORKING...'; } }));
  const holder = document.querySelector('#stars'); if (!holder || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const canvas = document.createElement('canvas'); holder.append(canvas); const ctx = canvas.getContext('2d'); let dots = [];
  const resize = () => { canvas.width = innerWidth; canvas.height = innerHeight; dots = Array.from({length: Math.min(100, Math.round(innerWidth / 14))}, () => [Math.random()*canvas.width, Math.random()*canvas.height, Math.random()*1.25+.25, Math.random()*Math.PI*2]); };
  const draw = t => { ctx.clearRect(0,0,canvas.width,canvas.height); dots.forEach(d => { ctx.fillStyle=`rgba(211,227,255,${.16+Math.sin(t/1300+d[3])*.12})`; ctx.beginPath(); ctx.arc(d[0],d[1],d[2],0,Math.PI*2); ctx.fill(); }); requestAnimationFrame(draw); };
  resize(); addEventListener('resize', resize); requestAnimationFrame(draw);
})();
