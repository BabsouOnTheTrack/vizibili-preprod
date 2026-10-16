/* ViZiBiLi : menu mobile, provenance des demandes, formulaire de diagnostic.
   Aucun cookie, aucun outil tiers. La provenance est gardée en sessionStorage
   (effacée à la fermeture de l'onglet) uniquement pour l'attribuer à la demande. */
(function () {
  'use strict';

  /* Menu mobile */
  var bouton = document.querySelector('.bouton-menu');
  var nav = document.getElementById('navigation');
  if (bouton && nav) {
    bouton.addEventListener('click', function () {
      var ouvert = nav.classList.toggle('ouvert');
      bouton.setAttribute('aria-expanded', ouvert ? 'true' : 'false');
      bouton.setAttribute('aria-label', ouvert ? 'Fermer le menu' : 'Ouvrir le menu');
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('ouvert')) {
        nav.classList.remove('ouvert');
        bouton.setAttribute('aria-expanded', 'false');
        bouton.setAttribute('aria-label', 'Ouvrir le menu');
        bouton.focus();
      }
    });
  }

  /* Provenance : mémorisée à la première page vue de la session */
  var CLE = 'vz-provenance';
  function lireProvenance() {
    try { return JSON.parse(sessionStorage.getItem(CLE) || 'null'); } catch (e) { return null; }
  }
  /* Première page de la visite, OU arrivée par une nouvelle campagne (annonce, lien suivi) :
     un clic publicitaire ou des paramètres de campagne remplacent toujours la provenance précédente. */
  var pUrl = new URLSearchParams(location.search);
  var nouvelleCampagne = ['gclid', 'gbraid', 'wbraid', 'utm_source', 'utm_medium', 'utm_campaign'].some(function (k) { return pUrl.get(k); });
  if (!lireProvenance() || nouvelleCampagne) {
    var p = pUrl;
    var ref = '';
    try { ref = document.referrer ? new URL(document.referrer).hostname : ''; } catch (e) { ref = ''; }
    if (ref === location.hostname) ref = '';
    var idClic = function (k) { var v = p.get(k) || ''; return /^[A-Za-z0-9_\-]{1,200}$/.test(v) ? v : ''; };
    var clic = idClic('gclid') || idClic('gbraid') || idClic('wbraid');
    var prov = {
      source: p.get('utm_source') || (clic ? 'google' : '') || ref || 'direct',
      support: p.get('utm_medium') || (clic ? 'cpc' : (ref ? 'referral' : 'none')),
      campagne: p.get('utm_campaign') || '',
      terme: p.get('utm_term') || '',
      contenu: p.get('utm_content') || '',
      arrivee: location.pathname,
      referent: ref,
      date_arrivee: new Date().toISOString(),
      gclid: idClic('gclid'),
      gbraid: idClic('gbraid'),
      wbraid: idClic('wbraid')
    };
    try { sessionStorage.setItem(CLE, JSON.stringify(prov)); } catch (e) { /* stockage indisponible : la demande part sans provenance */ }
  }

  /* Formulaire de premier échange */
  var form = document.getElementById('formulaire-demande');
  if (!form) return;

  /* Identifiant de la demande : généré une fois par affichage du formulaire.
     Deux envois de la même demande portent le même identifiant : le serveur ignore le second. */
  var idChamp = form.querySelector('[name="demande_id"]');
  if (idChamp && !idChamp.value) {
    var alea = (window.crypto && crypto.getRandomValues) ? Array.from(crypto.getRandomValues(new Uint8Array(4))).map(function (b) { return b.toString(16).padStart(2, '0'); }).join('') : Math.random().toString(16).slice(2, 10);
    var d = new Date();
    idChamp.value = 'VZ-' + d.getFullYear() + String(d.getMonth() + 1).padStart(2, '0') + String(d.getDate()).padStart(2, '0') + '-' + alea.toUpperCase();
  }

  var secteur = form.querySelector('#secteur');
  var complement = document.getElementById('complement-proprete');
  var PROPRETE = 'Nettoyage et propreté';
  function majComplement() {
    if (!complement || !secteur) return;
    var actif = secteur.value === PROPRETE;
    complement.hidden = !actif;
    complement.querySelectorAll('input').forEach(function (i) { i.disabled = !actif; });
  }
  var params = new URLSearchParams(location.search);
  if (secteur && (params.get('secteur') === 'proprete' || params.get('besoin') === 'nettoyage')) secteur.value = PROPRETE;
  if (secteur) secteur.addEventListener('change', majComplement);
  majComplement();

  var prov2 = lireProvenance() || {};
  ['source', 'support', 'campagne', 'terme', 'contenu', 'arrivee', 'referent', 'date_arrivee', 'gclid', 'gbraid', 'wbraid'].forEach(function (k) {
    var champ = form.querySelector('[name="prov_' + k + '"]');
    if (champ) champ.value = prov2[k] || '';
  });

  var reEmail = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  var reTel = /^[+0-9][0-9 .()-]{8,}$/;
  function marquer(champ, ok) {
    var bloc = champ.closest('.champ');
    if (!bloc) return;
    bloc.classList.toggle('erreur', !ok);
    champ.setAttribute('aria-invalid', ok ? 'false' : 'true');
  }
  function verifier() {
    var premierFaux = null;
    form.querySelectorAll('[data-requis]').forEach(function (champ) {
      var ok;
      if (champ.type === 'radio') {
        ok = !!form.querySelector('[name="' + champ.name + '"]:checked');
      } else if (champ.id === 'email') {
        ok = reEmail.test(champ.value.trim());
      } else {
        ok = champ.value.trim().length > 0;
      }
      if (champ.type !== 'radio' || champ === form.querySelector('[name="' + champ.name + '"]')) marquer(champ, ok);
      if (!ok && !premierFaux) premierFaux = champ;
    });
    var tel = form.querySelector('#telephone');
    if (tel) {
      var okTel = !tel.value.trim() || reTel.test(tel.value.trim());
      marquer(tel, okTel);
      if (!okTel && !premierFaux) premierFaux = tel;
    }
    if (premierFaux) {
      var bloc = premierFaux.closest('.champ') || premierFaux;
      bloc.scrollIntoView({ block: 'center' });
      premierFaux.focus({ preventScroll: true });
    }
    return !premierFaux;
  }

  var alerte = document.getElementById('alerte-envoi');
  var envoyer = form.querySelector('button[type="submit"]');
  var enCours = false;
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (enCours) return;
    if (alerte) alerte.classList.remove('visible');
    if (!verifier()) return;
    enCours = true;
    envoyer.disabled = true;
    envoyer.textContent = 'Envoi en cours…';
    fetch(form.action, { method: 'POST', body: new FormData(form), headers: { 'Accept': 'application/json' } })
      .then(function (r) { return r.json().catch(function () { return { ok: false }; }); })
      .then(function (rep) {
        /* La confirmation ne s'affiche qu'après accusé de réception du serveur */
        if (rep && rep.ok) { location.replace('/premier-echange/merci/'); return; }
        throw new Error('refus');
      })
      .catch(function () {
        enCours = false;
        envoyer.disabled = false;
        envoyer.textContent = 'Envoyer ma demande';
        if (alerte) { alerte.classList.add('visible'); alerte.focus(); }
      });
  });
})();

/* Méthode : frise des huit étapes, apparition et ligne de progression au défilement */
(function () {
  var frise = document.querySelector('.frise-etapes');
  if (!frise) return;
  var calme = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var etapes = frise.querySelectorAll('.fe');
  if (calme || !('IntersectionObserver' in window)) {
    etapes.forEach(function (e) { e.classList.add('vu'); });
    return;
  }
  document.documentElement.classList.add('js-anim');
  var obs = new IntersectionObserver(function (entrees) {
    entrees.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('vu'); obs.unobserve(en.target); } });
  }, { rootMargin: '0px 0px -15% 0px', threshold: 0.15 });
  etapes.forEach(function (e) { obs.observe(e); });
  var attente = false;
  function maj() {
    attente = false;
    var r = frise.getBoundingClientRect();
    var p = (window.innerHeight * 0.65 - r.top) / r.height;
    frise.style.setProperty('--p', Math.max(0, Math.min(1, p)).toFixed(3));
  }
  window.addEventListener('scroll', function () { if (!attente) { attente = true; requestAnimationFrame(maj); } }, { passive: true });
  window.addEventListener('resize', maj);
  maj();
})();

/* Barre mobile « Demander un premier échange » : cachée tant que le bouton du haut de page est à l'écran */
(function () {
  var barre = document.querySelector('.barre-mobile');
  var bouton = Array.prototype.find.call(document.querySelectorAll('main .btn-plein'), function (b) { return !barre || !barre.contains(b); });
  if (!barre || !bouton || !('IntersectionObserver' in window)) return;
  new IntersectionObserver(function (entrees) {
    entrees.forEach(function (en) { barre.classList.toggle('cachee', en.isIntersecting); });
  }, { threshold: 0 }).observe(bouton);
})();

/* Mini-parcours « où ça casse » : la progression avance puis le maillon casse, à l'apparition de chaque carte */
(function () {
  var signaux = document.querySelectorAll('.symptome .signal');
  if (!signaux.length || !('IntersectionObserver' in window)) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  document.documentElement.classList.add('sig-anim');
  var obs = new IntersectionObserver(function (entrees) {
    entrees.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('vu'); obs.unobserve(en.target); } });
  }, { rootMargin: '0px 0px -10% 0px', threshold: 0.4 });
  signaux.forEach(function (s) { obs.observe(s); });
})();

/* V2 ludique (16/10/2026) : en-tête vivant, apparitions au défilement, routes de jeu, pistes, jauge du formulaire.
   Sans JavaScript ou si le visiteur limite les animations, tout s'affiche directement dans son état final. */
(function () {
  var doc = document.documentElement;
  var calme = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var io = 'IntersectionObserver' in window;

  /* En-tête : ombre au défilement et barre de progression de lecture */
  var tete = document.querySelector('.site-header');
  if (tete) {
    var lu = document.createElement('span');
    lu.className = 'progression'; lu.setAttribute('aria-hidden', 'true');
    tete.appendChild(lu);
  }
  function enTete() {
    if (!tete) return;
    var h = doc.scrollHeight - window.innerHeight, y = window.scrollY || 0;
    tete.classList.toggle('defile', y > 8);
    tete.style.setProperty('--lu', h > 0 ? Math.min(1, y / h).toFixed(4) : '0');
  }

  /* Éléments qui apparaissent au défilement, avec un léger décalage entre voisins */
  var AUTO = ['.titre-section', '.liste-refus li', '.faq details', '.symptome', '.etapes li', '.fe-phases li', '.pour-qui', '.encart', '.formulaire',
              '.bloc-encre', '.carte', '.note', '.conclusion', '.constat', '.lien-suite', '.article h2', '.article .exemple', '.article .formule'];
  AUTO.forEach(function (sel) {
    document.querySelectorAll(sel).forEach(function (el) {
      if (el.classList.contains('rv')) return;
      var rang = 0, frere = el.previousElementSibling;
      while (frere && rang < 6) { if (frere.matches(sel)) rang++; frere = frere.previousElementSibling; }
      el.classList.add('rv');
      if (!el.style.getPropertyValue('--i')) el.style.setProperty('--i', rang);
    });
  });

  var routes = Array.prototype.slice.call(document.querySelectorAll('[data-route]')).map(function (z) {
    return { zone: z, etapes: Array.prototype.slice.call(z.querySelectorAll('.rt-etape, .rt-arrivee')), centres: [], vert: false };
  });
  function geometrie(r) {
    var zr = r.zone.getBoundingClientRect();
    r.centres = r.etapes.map(function (li) {
      var j = li.querySelector('.rt-jeton').getBoundingClientRect();
      return { x: j.left + j.width / 2 - zr.left, y: j.top + j.height / 2 - zr.top };
    });
    if (r.centres.length < 2) return;
    var a = r.centres[0], b = r.centres[r.centres.length - 1];
    r.vert = Math.abs(b.x - a.x) < 10;
    r.zone.classList.toggle('vert', r.vert);
    var s = r.zone.style;
    if (r.vert) { s.setProperty('--x0', (a.x - 3) + 'px'); s.setProperty('--y0', a.y + 'px'); s.setProperty('--lw', '6px'); s.setProperty('--lh', (b.y - a.y) + 'px'); }
    else { s.setProperty('--x0', a.x + 'px'); s.setProperty('--y0', (a.y - 3) + 'px'); s.setProperty('--lw', (b.x - a.x) + 'px'); s.setProperty('--lh', '6px'); }
  }
  function avancer(r, p) {
    var c = r.centres, m = c.length - 1;
    if (m < 1) return;
    r.zone.style.setProperty('--p', p.toFixed(3));
    var t = p * m, k = Math.min(m - 1, Math.floor(t)), f = t - k;
    r.zone.style.setProperty('--px', (c[k].x + (c[k + 1].x - c[k].x) * f).toFixed(1) + 'px');
    r.zone.style.setProperty('--py', (c[k].y + (c[k + 1].y - c[k].y) * f).toFixed(1) + 'px');
    r.zone.classList.toggle('actif', p > 0.001 && p < 0.999);
    r.etapes.forEach(function (li, j) { li.classList.toggle('atteint', t >= j - 0.02); });
  }
  function suivreRoutes() {
    var vh = window.innerHeight;
    routes.forEach(function (r) {
      if (r.centres.length < 2) return;
      var top = r.zone.getBoundingClientRect().top, p;
      if (r.vert) { var a = r.centres[0].y, b = r.centres[r.centres.length - 1].y; p = (vh * 0.62 - (top + a)) / (b - a); }
      else p = (vh * 0.82 - top) / (vh * 0.42);
      avancer(r, Math.max(0, Math.min(1, p)));
    });
  }

  if (calme || !io) {
    doc.classList.add('sans-anim');
    routes.forEach(function (r) { geometrie(r); avancer(r, 1); });
    window.addEventListener('resize', function () { routes.forEach(function (r) { geometrie(r); avancer(r, 1); }); });
    window.addEventListener('scroll', enTete, { passive: true });
    enTete();
  } else {
    doc.classList.add('anim');
    var obs = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('vu'); obs.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.12 });
    document.querySelectorAll('.rv, .piste').forEach(function (el) { obs.observe(el); });
    var attente = false;
    var tout = function () { attente = false; enTete(); suivreRoutes(); };
    window.addEventListener('scroll', function () { if (!attente) { attente = true; requestAnimationFrame(tout); } }, { passive: true });
    window.addEventListener('resize', function () { routes.forEach(geometrie); tout(); });
    routes.forEach(geometrie);
    tout();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { routes.forEach(geometrie); tout(); });
    window.addEventListener('load', function () { routes.forEach(geometrie); tout(); });
  }

  /* Jauge du formulaire : combien de réponses obligatoires restent */
  var form = document.getElementById('formulaire-demande'), jauge = document.querySelector('.jauge');
  if (form && jauge) {
    var texte = jauge.querySelector('.jauge-texte');
    var maj = function () {
      var ok = 0;
      ['nom', 'entreprise'].forEach(function (id) { var c = document.getElementById(id); if (c && c.value.trim().length > 1) ok++; });
      var em = document.getElementById('email'); if (em && /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(em.value.trim())) ok++;
      var se = document.getElementById('secteur'); if (se && se.value) ok++;
      if (form.querySelector('input[name="objectif"]:checked')) ok++;
      jauge.style.setProperty('--j', (ok / 5).toFixed(2));
      jauge.classList.toggle('complet', ok === 5);
      var reste = 5 - ok;
      texte.textContent = ok === 0 ? '5 réponses obligatoires, c\'est parti.' : (reste === 0 ? 'Tout est prêt : vous pouvez envoyer.' : 'Encore ' + reste + ' réponse' + (reste > 1 ? 's' : '') + ' obligatoire' + (reste > 1 ? 's' : '') + '.');
    };
    form.addEventListener('input', maj); form.addEventListener('change', maj); maj();
  }
})();
