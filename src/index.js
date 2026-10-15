/**
 * ViZiBiLi : Worker Cloudflare (site statique + formulaire de premier échange).
 *
 * - Sert les fichiers de public/ (binding ASSETS).
 * - POST /api/demande : contrôle, anti-robots, déduplication, e-mail de notification à DESTINATAIRE
 *   contenant une ligne prête à coller dans le registre des demandes.
 * - Anciennes adresses : 301 (REDIRECTIONS) ou 410 (GONE).
 * - Préproduction (ENVIRONNEMENT = "preproduction") : noindex partout, robots.txt bloquant,
 *   bandeau « environnement de test », demandes marquées TEST ; mot de passe sauf si PROTECTION = "aucune".
 *
 * Aucun cookie. Le Worker ne conserve aucune demande : seul l'identifiant sert, 24 h, à ignorer un doublon.
 */

const REDIRECTIONS = {
  // Site actuel (V1.0) → V1.1
  '/contact': '/premier-echange/',
  '/contact/merci': '/premier-echange/merci/',
  // Site historique (export Search Console du 14/10/2026)
  '/pages/contact': '/premier-echange/',
  '/products/audit-creation-optimisation-fiche-google-business-profile': '/premier-echange/',
  '/products/optimisation-gestion-continue-fiche-google-my-business': '/offre/',
  '/pages/a-propos-agence-referencement-local-vosges': '/a-propos/',
  '/pages/pourquoi-choisir-vizibili': '/methode/',
  '/pages/pourquoi-faire-appel-a-nous': '/methode/',
  '/collections/formules': '/offre/',
  '/collections/all': '/offre/'
};
const GONE = [/^\/blogs(\/|$)/, /^\/pages\/test-google-local-services\/?$/];
const LIMITES = { demande_id: 40, nom: 120, entreprise: 160, email: 160, telephone: 30, secteur: 80, objectif: 80, site: 300,
  recherche: 40, prov_source: 200, prov_support: 60, prov_campagne: 200, prov_terme: 200, prov_contenu: 200, prov_arrivee: 300,
  prov_referent: 200, prov_date_arrivee: 30, prov_gclid: 200, prov_gbraid: 200, prov_wbraid: 200 };
const REQUIS = ['nom', 'entreprise', 'email', 'secteur', 'objectif'];
const SECTEURS = ['Nettoyage et propreté', 'Artisanat et bâtiment', 'Commerce de proximité', 'Professions libérales et santé',
  'Hôtellerie, restauration, tourisme', 'Services aux entreprises', 'Services aux particuliers', 'Autre secteur'];
const OBJECTIFS = ['Obtenir davantage de demandes qualifiées', 'Développer des contrats récurrents', 'Améliorer la transformation des prospects',
  'Comprendre les performances actuelles', 'Structurer son acquisition sur Google', 'Autre besoin'];
const PRESTATIONS = ['Entretien de bureaux et locaux', 'Nettoyage de vitres', 'Ménage à domicile', 'Grand ménage, fin de bail', 'Autre prestation'];
const RE_EMAIL = /^[^\s@<>"]+@[^\s@<>"]+\.[^\s@<>"]{2,}$/;
const RE_TEL = /^[+0-9][0-9 .()-]{8,}$/;
const RE_ID = /^VZ-\d{8}-[0-9A-F]{8}$/;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const preprod = env.ENVIRONNEMENT === 'preproduction';

    const protege = preprod && env.PROTECTION !== 'aucune';
    if (protege && !autorise(request, env)) {
      return new Response('Accès réservé à la recette.', {
        status: 401,
        headers: { 'WWW-Authenticate': 'Basic realm="ViZiBiLi recette", charset="UTF-8"', 'X-Robots-Tag': 'noindex, nofollow', 'Cache-Control': 'no-store' }
      });
    }

    let reponse;
    const chemin = url.pathname.replace(/\/$/, '');
    if (url.pathname === '/api/demande') {
      reponse = request.method === 'POST'
        ? await traiterDemande(request, env, preprod)
        : new Response('Méthode non autorisée', { status: 405, headers: { Allow: 'POST' } });
    } else if (preprod && url.pathname === '/robots.txt') {
      reponse = new Response('User-agent: *\nDisallow: /\n', { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
    } else if (REDIRECTIONS[chemin]) {
      const cible = new URL(REDIRECTIONS[chemin], url);
      cible.search = url.search; // garde ?secteur=… et les paramètres de campagne
      reponse = new Response(null, { status: 301, headers: { Location: cible.toString() } });
    } else if (GONE.some((re) => re.test(url.pathname))) {
      const page = await env.ASSETS.fetch(new Request(new URL('/404.html', url), request));
      reponse = new Response(page.body, { status: 410, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
    } else {
      reponse = await env.ASSETS.fetch(request);
    }
    reponse = securiser(reponse, preprod);
    if (preprod) reponse = bandeauTest(reponse);
    return reponse;
  }
};

function bandeauTest(reponse) {
  const type = reponse.headers.get('Content-Type') || '';
  if (!type.includes('text/html') || typeof HTMLRewriter === 'undefined') return reponse;
  return new HTMLRewriter().on('body', {
    element(el) {
      el.prepend('<div class="bandeau-test" role="note">Environnement de test. N’envoyez pas de vraie demande ici : elles ne sont pas traitées.</div>', { html: true });
    }
  }).transform(reponse);
}

function autorise(request, env) {
  const attendu = env.PREPROD_MOT_DE_PASSE;
  if (!attendu) return false; // préproduction protégée sans mot de passe configuré : fermée par défaut
  const h = request.headers.get('Authorization') || '';
  if (!h.startsWith('Basic ')) return false;
  let decode = '';
  try { decode = atob(h.slice(6)); } catch (e) { return false; }
  const mdp = decode.slice(decode.indexOf(':') + 1);
  return egaliteConstante(mdp, attendu);
}

function egaliteConstante(a, b) {
  if (a.length !== b.length) return false;
  let r = 0;
  for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}

function securiser(reponse, preprod) {
  const r = new Response(reponse.body, reponse);
  r.headers.set('X-Content-Type-Options', 'nosniff');
  r.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  r.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=(), interest-cohort=()');
  r.headers.set('X-Frame-Options', 'SAMEORIGIN');
  const type = r.headers.get('Content-Type') || '';
  if (type.includes('text/html')) {
    r.headers.set('Content-Security-Policy', [
      "default-src 'self'",
      "script-src 'self' https://challenges.cloudflare.com https://static.cloudflareinsights.com",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data:",
      "font-src 'self'",
      "connect-src 'self' https://cloudflareinsights.com",
      "frame-src https://challenges.cloudflare.com",
      "form-action 'self'",
      "base-uri 'self'",
      "frame-ancestors 'self'"
    ].join('; '));
  }
  if (preprod) {
    r.headers.set('X-Robots-Tag', 'noindex, nofollow');
    r.headers.set('Cache-Control', 'no-store');
  }
  return r;
}

/* Déduplication : un identifiant déjà reçu dans les 24 h est ignoré (réponse « ok », aucun second envoi). */
const CLE_DEDUP = (id) => new Request('https://dedup.vizibili.invalid/' + encodeURIComponent(id));
// Déduplication : stockage KV « DEDUP » si lié (global, fonctionne aussi sur workers.dev),
// sinon Cache API (ne fonctionne que sur un domaine personnalisé, par centre de données).
async function empreinte(texte) {
  const h = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(texte));
  return Array.from(new Uint8Array(h)).map((o) => o.toString(16).padStart(2, '0')).join('').slice(0, 32);
}
async function clesDedup(d) {
  // 1. même envoi (identifiant), 2. même personne et même entreprise renvoyant une demande peu après
  return [['id:' + d.demande_id, 86400], ['contenu:' + await empreinte(d.email.toLowerCase() + '|' + d.entreprise.toLowerCase()), 900]];
}
async function dejaRecue(env, cles) {
  for (const [cle] of cles) {
    try {
      if (env.DEDUP ? await env.DEDUP.get(cle) : await caches.default.match(CLE_DEDUP(cle))) return cle.split(':')[0];
    } catch (e) { /* stockage indisponible : on laisse passer plutôt que de perdre une demande */ }
  }
  return null;
}
async function marquerRecue(env, cles) {
  for (const [cle, duree] of cles) {
    try {
      if (env.DEDUP) await env.DEDUP.put(cle, '1', { expirationTtl: Math.max(60, duree) });
      else await caches.default.put(CLE_DEDUP(cle), new Response('1', { headers: { 'Cache-Control': 'max-age=' + duree } }));
    } catch (e) { /* sans stockage : pas de déduplication serveur */ }
  }
}

async function traiterDemande(request, env, preprod) {
  const veutJson = (request.headers.get('Accept') || '').includes('application/json');
  const repondre = (ok, statut = 200, extra = {}) => veutJson
    ? new Response(JSON.stringify({ ok, ...extra }), { status: statut, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' } })
    : Response.redirect(new URL(ok ? '/premier-echange/merci/' : '/premier-echange/?erreur=1#demande', request.url).toString(), 303);

  let fd;
  try { fd = await request.formData(); } catch (e) { return repondre(false, 400); }

  // Champ piège rempli : robot. On répond « ok » sans rien envoyer.
  if ((fd.get('entreprise_web') || '').toString().trim() !== '') return repondre(true);

  const propre = (v, max) => (v || '').toString().replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '').trim().slice(0, max);
  const d = {};
  for (const [cle, max] of Object.entries(LIMITES)) d[cle] = propre(fd.get(cle), max);
  d.prestations = fd.getAll('prestations').map((x) => propre(x, 60)).filter((x) => PRESTATIONS.includes(x));

  // Identifiants de clic Google : caractères attendus uniquement, sinon ignorés
  for (const k of ['prov_gclid', 'prov_gbraid', 'prov_wbraid']) if (d[k] && !/^[A-Za-z0-9_-]+$/.test(d[k])) d[k] = '';
  if (d.prov_date_arrivee && isNaN(Date.parse(d.prov_date_arrivee))) d.prov_date_arrivee = '';
  if (REQUIS.some((k) => !d[k])) return repondre(false, 422);
  if (!RE_EMAIL.test(d.email)) return repondre(false, 422);
  if (d.telephone && !RE_TEL.test(d.telephone)) return repondre(false, 422);
  if (!SECTEURS.includes(d.secteur) || !OBJECTIFS.includes(d.objectif)) return repondre(false, 422);
  if (!RE_ID.test(d.demande_id)) d.demande_id = 'VZ-' + new Date().toISOString().slice(0, 10).replace(/-/g, '') + '-' + crypto.randomUUID().slice(0, 8).toUpperCase();

  if (env.TURNSTILE_SECRET) {
    const jeton = (fd.get('cf-turnstile-response') || '').toString();
    const ok = await verifierTurnstile(jeton, env.TURNSTILE_SECRET, request.headers.get('CF-Connecting-IP'));
    if (!ok) return repondre(false, 403);
  }

  const cles = await clesDedup(d);
  const doublon = await dejaRecue(env, cles);
  if (doublon) { console.log('[demande] doublon ignoré :', doublon, d.demande_id); return repondre(true, 200, { doublon: true }); }

  const date = new Date().toISOString();
  const test = preprod ? 'TEST ' : '';
  const idClic = d.prov_gclid ? 'gclid:' + d.prov_gclid : d.prov_gbraid ? 'gbraid:' + d.prov_gbraid : d.prov_wbraid ? 'wbraid:' + d.prov_wbraid : '';
  // Même ordre de colonnes que le modèle VIZIBILI_REGISTRE_DEMANDES_modele.csv
  const ligneRegistre = [test + d.demande_id, preprod ? 'Oui' : 'Non', date.slice(0, 10), d.entreprise, d.nom, d.email, d.telephone, d.site, d.secteur, d.objectif,
    d.prestations.join(' | '), d.prov_source || 'inconnue', d.prov_support, d.prov_campagne, d.prov_terme, d.prov_contenu, d.prov_arrivee,
    d.prov_referent, d.prov_date_arrivee, idClic, 'Nouveau', '', '', '', '', '', '', '', date.slice(0, 10), 'Vérifier le contact']
    .map((v) => (v || '').toString().replace(/[\t\r\n]+/g, ' ')).join('\t');
  const lignes = [
    (preprod ? 'DEMANDE DE TEST (préproduction) : ne pas compter comme prospect réel.' : 'Nouvelle demande de premier échange'),
    '',
    `Identifiant : ${d.demande_id}`,
    `Nom : ${d.nom}`,
    `Entreprise : ${d.entreprise}`,
    `E-mail : ${d.email}`,
    `Téléphone : ${d.telephone || '(non renseigné)'}`,
    `Secteur : ${d.secteur}`,
    `Objectif principal : ${d.objectif}`,
    `Site : ${d.site || '(non renseigné)'}`,
    d.secteur === 'Nettoyage et propreté' ? `Prestations : ${d.prestations.join(', ') || '(non précisé)'}` : null,
    d.secteur === 'Nettoyage et propreté' ? `Recherche surtout : ${d.recherche || '(non précisé)'}` : null,
    '',
    'Provenance',
    `Source : ${d.prov_source || '(inconnue)'}`,
    `Support : ${d.prov_support || '(inconnu)'}`,
    `Campagne : ${d.prov_campagne || '(aucune)'}`,
    `Terme : ${d.prov_terme || '(aucun)'}`,
    `Contenu : ${d.prov_contenu || '(aucun)'}`,
    `Page d'arrivée : ${d.prov_arrivee || '(inconnue)'}`,
    `Site référent : ${d.prov_referent || '(aucun)'}`,
    `Arrivée sur le site : ${d.prov_date_arrivee || '(inconnue)'}`,
    `Identifiant de clic Google : ${idClic || 'aucun'}`,
    `Date : ${date}`,
    '',
    'Ligne à coller dans le registre des demandes (colonnes séparées par des tabulations) :',
    ligneRegistre
  ].filter((l) => l !== null);

  const smtp = !!(env.SMTP_HOTE && env.SMTP_UTILISATEUR && env.SMTP_MOT_DE_PASSE);
  const expediteur = env.EXPEDITEUR || env.SMTP_UTILISATEUR;
  if ((!smtp && !env.EMAIL) || !env.DESTINATAIRE || !expediteur) {
    // Préproduction sans e-mail configuré : la demande de test est acceptée et visible dans les journaux du Worker.
    console.log('[demande] e-mail non configuré :', JSON.stringify({ id: d.demande_id, test: preprod, secteur: d.secteur, objectif: d.objectif, source: d.prov_source, support: d.prov_support, campagne: d.prov_campagne, arrivee: d.prov_arrivee, clic: idClic ? idClic.split(':')[0] : 'aucun', date }));
    if (preprod) { await marquerRecue(env, cles); return repondre(true); }
    return repondre(false, 503);
  }

  try {
    const sujet = `${preprod ? '[TEST] ' : ''}Premier échange : ${d.entreprise} (${d.secteur})`;
    const brut = mime(expediteur, env.DESTINATAIRE, sujet, lignes.join('\r\n'), d.email);
    if (smtp) {
      // Serveur de messagerie du fondateur, indépendant de Cloudflare (SMTP authentifié, chiffré).
      await envoyerSmtp(env, expediteur, env.DESTINATAIRE, brut, env._connecterSmtp); // _connecterSmtp : uniquement pour les tests
    } else {
      const { EmailMessage } = await import('cloudflare:email');
      await env.EMAIL.send(new EmailMessage(expediteur, env.DESTINATAIRE, brut));
    }
    await marquerRecue(env, cles);
    return repondre(true);
  } catch (e) {
    console.log('[demande] échec d’envoi :', e && e.message);
    return repondre(false, 502);
  }
}

// ---------- Envoi SMTP (port 465 : TLS direct ; port 587 : STARTTLS). Le port 25 est bloqué par Cloudflare. ----------
async function envoyerSmtp(env, de, a, brut, connecter) {
  const port = Number(env.SMTP_PORT || 465);
  if (port === 25) throw new Error('port 25 interdit par Cloudflare : utiliser 465 ou 587');
  const starttls = port !== 465 && env.SMTP_SECURITE !== 'tls';
  if (!connecter) connecter = (await import('cloudflare:sockets')).connect;
  let socket = connecter({ hostname: env.SMTP_HOTE, port }, { secureTransport: starttls ? 'starttls' : 'on', allowHalfOpen: false });
  const delai = setTimeout(() => { try { socket.close(); } catch (e) {} }, 15000);
  let lecteur, ecrivain, tampon = '';
  const dec = new TextDecoder(), enc = new TextEncoder();
  const brancher = () => { lecteur = socket.readable.getReader(); ecrivain = socket.writable.getWriter(); tampon = ''; };
  const lire = async () => {
    // Lit une réponse complète (éventuellement sur plusieurs lignes « 250-… » puis « 250 … »)
    for (;;) {
      const lignes = tampon.split('\r\n');
      for (let i = 0; i < lignes.length - 1; i++) {
        if (/^\d{3} /.test(lignes[i]) || /^\d{3}$/.test(lignes[i])) {
          const rep = lignes.slice(0, i + 1);
          tampon = lignes.slice(i + 1).join('\r\n');
          return { code: Number(lignes[i].slice(0, 3)), texte: rep.join('\n') };
        }
      }
      const { value, done } = await lecteur.read();
      if (done) throw new Error('connexion SMTP fermée');
      tampon += dec.decode(value, { stream: true });
    }
  };
  const ecrire = (t) => ecrivain.write(enc.encode(t + '\r\n'));
  const commande = async (t, attendu, masque) => {
    if (t !== null) await ecrire(t);
    const r = await lire();
    if (!attendu.includes(r.code)) throw new Error(`SMTP ${masque || (t || 'accueil').split(' ')[0]} : ${r.texte.slice(0, 200)}`);
    return r;
  };
  try {
    brancher();
    await commande(null, [220]);
    const domaine = (de.split('@')[1] || 'vizibili.fr');
    let ehlo = await commande('EHLO ' + domaine, [250]);
    if (starttls) {
      await commande('STARTTLS', [220]);
      lecteur.releaseLock(); ecrivain.releaseLock();
      socket = socket.startTls();
      brancher();
      ehlo = await commande('EHLO ' + domaine, [250]);
    }
    const u = env.SMTP_UTILISATEUR, m = env.SMTP_MOT_DE_PASSE;
    if (/AUTH[ =][^\n]*PLAIN/i.test(ehlo.texte)) {
      await commande('AUTH PLAIN ' + b64('\u0000' + u + '\u0000' + m), [235], 'AUTH');
    } else {
      await commande('AUTH LOGIN', [334], 'AUTH');
      await commande(b64(u), [334], 'AUTH');
      await commande(b64(m), [235], 'AUTH');
    }
    await commande(`MAIL FROM:<${de}>`, [250]);
    await commande(`RCPT TO:<${a}>`, [250, 251]);
    await commande('DATA', [354]);
    // Point en début de ligne doublé (RFC 5321), puis fin de message
    await ecrivain.write(enc.encode(brut.replace(/\r\n\./g, '\r\n..') + '\r\n.\r\n'));
    await commande(null, [250], 'DATA');
    try { await ecrire('QUIT'); } catch (e) {}
  } finally {
    clearTimeout(delai);
    try { socket.close(); } catch (e) {}
  }
}

async function verifierTurnstile(jeton, secret, ip) {
  if (!jeton) return false;
  const corps = new FormData();
  corps.append('secret', secret);
  corps.append('response', jeton);
  if (ip) corps.append('remoteip', ip);
  try {
    const r = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'POST', body: corps });
    const j = await r.json();
    return !!j.success;
  } catch (e) {
    return false;
  }
}

function b64(texte) {
  const octets = new TextEncoder().encode(texte);
  let bin = '';
  for (const o of octets) bin += String.fromCharCode(o);
  return btoa(bin);
}

function enteteEncode(texte) {
  // Mots encodés de 30 caractères au plus, repliés sur plusieurs lignes (RFC 2047)
  const morceaux = [];
  const car = Array.from(texte);
  for (let i = 0; i < car.length; i += 30) morceaux.push(`=?UTF-8?B?${b64(car.slice(i, i + 30).join(''))}?=`);
  return morceaux.join('\r\n ');
}

function mime(de, a, sujet, texte, repondreA) {
  const corps = b64(texte).replace(/.{76}/g, '$&\r\n');
  return [
    `From: ViZiBiLi <${de}>`,
    `To: <${a}>`,
    repondreA ? `Reply-To: <${repondreA}>` : null,
    'Subject: ' + enteteEncode(sujet),
    `Date: ${new Date().toUTCString()}`,
    `Message-ID: <${crypto.randomUUID()}@${de.split('@')[1]}>`,
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=UTF-8',
    'Content-Transfer-Encoding: base64',
    '',
    corps
  ].filter((l) => l !== null).join('\r\n');
}

export { traiterDemande, mime, envoyerSmtp, REDIRECTIONS };
