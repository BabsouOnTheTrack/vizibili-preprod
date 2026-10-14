/**
 * ViZiBiLi : Worker Cloudflare (site statique + formulaire de diagnostic).
 *
 * - Sert les fichiers de public/ (binding ASSETS).
 * - POST /api/diagnostic : contrôle, anti-robots, e-mail de notification à DESTINATAIRE.
 * - Anciennes adresses du blog : 410 (contenu supprimé). Redirections 301 : public/_redirects.
 * - Préproduction (ENVIRONNEMENT = "preproduction") : noindex sur tout ; mot de passe sauf si PROTECTION = "aucune".
 *
 * Aucun cookie, aucune donnée conservée par le Worker : la demande part par e-mail.
 */

// Anciennes adresses du site historique (export Search Console du 14/10/2026) : redirections permanentes
const REDIRECTIONS = {
  '/pages/contact': '/contact/',
  '/products/audit-creation-optimisation-fiche-google-business-profile': '/offre/',
  '/products/optimisation-gestion-continue-fiche-google-my-business': '/offre/',
  '/pages/a-propos-agence-referencement-local-vosges': '/a-propos/',
  '/pages/pourquoi-choisir-vizibili': '/methode/',
  '/pages/pourquoi-faire-appel-a-nous': '/methode/',
  '/collections/formules': '/offre/',
  '/collections/all': '/offre/'
};
const GONE = [/^\/blogs(\/|$)/, /^\/pages\/test-google-local-services\/?$/];
const LIMITES = { nom: 120, entreprise: 160, activite: 160, site: 300, contact: 160, besoin: 80, objectif: 2000,
  prov_source: 200, prov_support: 60, prov_campagne: 200, prov_arrivee: 300, prov_gclid: 5 };
const REQUIS = ['nom', 'entreprise', 'activite', 'contact', 'besoin'];
const BESOINS = ['Trouver plus de clients', 'Transformer mes demandes en devis signés', 'Savoir ce que me rapporte ma publicité', 'Autre'];
const RE_CONTACT = /^([^\s@]+@[^\s@]+\.[^\s@]{2,}|[+0-9][0-9 .()-]{8,})$/;

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
    if (url.pathname === '/api/diagnostic') {
      reponse = request.method === 'POST'
        ? await traiterDiagnostic(request, env, preprod)
        : new Response('Méthode non autorisée', { status: 405, headers: { Allow: 'POST' } });
    } else if (preprod && url.pathname === '/robots.txt') {
      reponse = new Response('User-agent: *\nDisallow: /\n', { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
    } else if (REDIRECTIONS[url.pathname.replace(/\/$/, '')]) {
      reponse = new Response(null, { status: 301, headers: { Location: new URL(REDIRECTIONS[url.pathname.replace(/\/$/, '')], url).toString() } });
    } else if (GONE.some((re) => re.test(url.pathname))) {
      const page = await env.ASSETS.fetch(new Request(new URL('/404.html', url), request));
      reponse = new Response(page.body, { status: 410, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
    } else {
      reponse = await env.ASSETS.fetch(request);
    }
    return securiser(reponse, preprod);
  }
};

function autorise(request, env) {
  const attendu = env.PREPROD_MOT_DE_PASSE;
  if (!attendu) return false; // préproduction sans mot de passe configuré : fermée par défaut
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

async function traiterDiagnostic(request, env, preprod) {
  const veutJson = (request.headers.get('Accept') || '').includes('application/json');
  const repondre = (ok, statut = 200) => veutJson
    ? new Response(JSON.stringify({ ok }), { status: statut, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' } })
    : Response.redirect(new URL(ok ? '/contact/merci/' : '/contact/?erreur=1', request.url).toString(), 303);

  let fd;
  try { fd = await request.formData(); } catch (e) { return repondre(false, 400); }

  // Champ piège rempli : robot. On répond « ok » sans rien envoyer.
  if ((fd.get('entreprise_web') || '').toString().trim() !== '') return repondre(true);

  const d = {};
  for (const [cle, max] of Object.entries(LIMITES)) {
    d[cle] = (fd.get(cle) || '').toString().replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '').trim().slice(0, max);
  }
  if (REQUIS.some((k) => !d[k])) return repondre(false, 422);
  if (!RE_CONTACT.test(d.contact)) return repondre(false, 422);
  if (!BESOINS.includes(d.besoin)) return repondre(false, 422);

  if (env.TURNSTILE_SECRET) {
    const jeton = (fd.get('cf-turnstile-response') || '').toString();
    const ok = await verifierTurnstile(jeton, env.TURNSTILE_SECRET, request.headers.get('CF-Connecting-IP'));
    if (!ok) return repondre(false, 403);
  }

  const date = new Date().toISOString();
  const lignes = [
    'Nouvelle demande de diagnostic' + (preprod ? ' (PRÉPRODUCTION, test)' : ''),
    '',
    `Nom : ${d.nom}`,
    `Entreprise : ${d.entreprise}`,
    `Activité : ${d.activite}`,
    `Site : ${d.site || '(non renseigné)'}`,
    `Contact : ${d.contact}`,
    `Besoin principal : ${d.besoin}`,
    `Objectif : ${d.objectif || '(non renseigné)'}`,
    '',
    'Provenance',
    `Source : ${d.prov_source || '(inconnue)'}`,
    `Support : ${d.prov_support || '(inconnu)'}`,
    `Campagne : ${d.prov_campagne || '(aucune)'}`,
    `Page d'arrivée : ${d.prov_arrivee || '(inconnue)'}`,
    `Clic publicitaire Google : ${d.prov_gclid || 'non'}`,
    `Date : ${date}`,
    '',
    'Statut à suivre dans le registre des demandes : soumise → réelle → sérieuse → rendez-vous → client signé.'
  ];

  if (!env.EMAIL || !env.DESTINATAIRE || !env.EXPEDITEUR) {
    // Préproduction sans e-mail configuré : la demande est acceptée et tracée dans les journaux du Worker.
    console.log('[diagnostic] e-mail non configuré, demande reçue :', JSON.stringify({ entreprise: d.entreprise, besoin: d.besoin, source: d.prov_source, date }));
    return repondre(preprod, preprod ? 200 : 503);
  }

  try {
    const { EmailMessage } = await import('cloudflare:email');
    const sujet = `${preprod ? '[PRÉPROD] ' : ''}Diagnostic : ${d.entreprise} (${d.besoin})`;
    const brut = mime(env.EXPEDITEUR, env.DESTINATAIRE, sujet, lignes.join('\r\n'), RE_EMAIL_SEUL.test(d.contact) ? d.contact : null);
    await env.EMAIL.send(new EmailMessage(env.EXPEDITEUR, env.DESTINATAIRE, brut));
    return repondre(true);
  } catch (e) {
    console.log('[diagnostic] échec d’envoi :', e && e.message);
    return repondre(false, 502);
  }
}

const RE_EMAIL_SEUL = /^[^\s@<>"]+@[^\s@<>"]+\.[^\s@<>"]{2,}$/;

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

export { traiterDiagnostic, mime, REDIRECTIONS };
