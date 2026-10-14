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
  if (!lireProvenance()) {
    var p = new URLSearchParams(location.search);
    var ref = '';
    try { ref = document.referrer ? new URL(document.referrer).hostname : ''; } catch (e) { ref = ''; }
    if (ref === location.hostname) ref = '';
    var prov = {
      source: p.get('utm_source') || ref || 'direct',
      support: p.get('utm_medium') || (p.get('gclid') ? 'cpc' : (ref ? 'referral' : 'none')),
      campagne: p.get('utm_campaign') || '',
      arrivee: location.pathname,
      gclid: p.get('gclid') ? 'oui' : ''
    };
    try { sessionStorage.setItem(CLE, JSON.stringify(prov)); } catch (e) { /* stockage indisponible : la demande part sans provenance */ }
  }

  /* Formulaire de diagnostic */
  var form = document.getElementById('formulaire-diagnostic');
  if (!form) return;

  var params = new URLSearchParams(location.search);
  if (params.get('besoin') === 'nettoyage') {
    var act = form.querySelector('#activite');
    if (act && !act.value) act.value = 'Entreprise de nettoyage';
  }
  var prov2 = lireProvenance() || {};
  ['source', 'support', 'campagne', 'arrivee', 'gclid'].forEach(function (k) {
    var champ = form.querySelector('[name="prov_' + k + '"]');
    if (champ) champ.value = prov2[k] || '';
  });

  var reContact = /^([^\s@]+@[^\s@]+\.[^\s@]{2,}|[+0-9][0-9 .()-]{8,})$/;
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
      } else if (champ.id === 'contact') {
        ok = reContact.test(champ.value.trim());
      } else {
        ok = champ.value.trim().length > 0;
      }
      if (champ.type !== 'radio' || champ === form.querySelector('[name="' + champ.name + '"]')) marquer(champ, ok);
      if (!ok && !premierFaux) premierFaux = champ;
    });
    if (premierFaux) {
      var bloc = premierFaux.closest('.champ') || premierFaux;
      bloc.scrollIntoView({ block: 'center' });
      premierFaux.focus({ preventScroll: true });
    }
    return !premierFaux;
  }

  var alerte = document.getElementById('alerte-envoi');
  var envoyer = form.querySelector('button[type="submit"]');
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (alerte) alerte.classList.remove('visible');
    if (!verifier()) return;
    envoyer.disabled = true;
    envoyer.textContent = 'Envoi en cours…';
    fetch(form.action, { method: 'POST', body: new FormData(form), headers: { 'Accept': 'application/json' } })
      .then(function (r) { return r.json().catch(function () { return { ok: false }; }); })
      .then(function (rep) {
        if (rep && rep.ok) { location.href = '/contact/merci/'; return; }
        throw new Error('refus');
      })
      .catch(function () {
        envoyer.disabled = false;
        envoyer.textContent = 'Envoyer ma demande';
        if (alerte) { alerte.classList.add('visible'); alerte.focus(); }
      });
  });
})();
