// Tests du Worker sans Cloudflare : ASSETS simulé par les fichiers de public/, cache de déduplication simulé.
import { readFile } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import worker, { mime, envoyerSmtp } from '../src/index.js';

const PUB = join(dirname(fileURLToPath(import.meta.url)), '..', 'public');
const ASSETS = {
  async fetch(req) {
    let p = new URL(req.url).pathname;
    if (p.endsWith('/')) p += 'index.html';
    try {
      const corps = await readFile(join(PUB, p));
      const type = p.endsWith('.html') ? 'text/html; charset=utf-8' : p.endsWith('.css') ? 'text/css' : 'application/octet-stream';
      return new Response(corps, { headers: { 'Content-Type': type } });
    } catch {
      return new Response(await readFile(join(PUB, '404.html')), { status: 404, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
    }
  }
};
// Cache de déduplication simulé (caches.default dans Cloudflare)
const memo = new Map();
globalThis.caches = { default: { async match(r) { return memo.get(r.url) || undefined; }, async put(r, v) { memo.set(r.url, v); } } };

let ok = 0, ko = 0;
function verifier(nom, cond, detail = '') { if (cond) { ok++; console.log('  ✓', nom); } else { ko++; console.log('  ✗', nom, detail); } }
const auth = (m) => ({ Authorization: 'Basic ' + btoa('recette:' + m) });
const prod = { ASSETS, ENVIRONNEMENT: 'production' };
const pre = { ASSETS, ENVIRONNEMENT: 'preproduction', PROTECTION: 'aucune' };
const preProtege = { ASSETS, ENVIRONNEMENT: 'preproduction', PREPROD_MOT_DE_PASSE: 'secret-test' };
const req = (chemin, init = {}) => new Request('https://vizibili.fr' + chemin, init);
let n = 0;
const nouvelId = () => 'VZ-20261014-' + String(++n).padStart(8, '0').replace(/./g, (c) => 'ABCDEF0123456789'[+c] || c).slice(0, 8);

function formulaire(extra = {}, id = nouvelId()) {
  const fd = new FormData();
  const base = { demande_id: id, nom: 'Marie Test', entreprise: 'Propre & Net', email: 'marie@exemple.fr', secteur: 'Nettoyage et propreté',
    objectif: 'Développer des contrats récurrents', recherche: 'Contrats récurrents', prov_source: 'google', prov_support: 'cpc', prov_arrivee: '/entreprises-de-nettoyage/', ...extra };
  for (const [k, v] of Object.entries(base)) if (v !== null) fd.append(k, v);
  fd.append('prestations', 'Entretien de bureaux et locaux');
  fd.append('prestations', 'Nettoyage de vitres');
  return fd;
}
const json = { Accept: 'application/json' };
const envoi = (corps, env, h = {}) => worker.fetch(req('/api/demande', { method: 'POST', body: corps, headers: { ...json, ...h } }), env);

console.log('Préproduction');
let r = await worker.fetch(req('/'), pre);
verifier('ouverte sans mot de passe (PROTECTION = aucune)', r.status === 200);
verifier('non indexable', r.headers.get('X-Robots-Tag') === 'noindex, nofollow');
r = await worker.fetch(req('/robots.txt'), pre);
verifier('robots.txt bloque tout', (await r.text()).includes('Disallow: /'));
r = await worker.fetch(req('/'), preProtege);
verifier('variante protégée : 401 sans mot de passe', r.status === 401);
r = await worker.fetch(req('/', { headers: auth('secret-test') }), preProtege);
verifier('variante protégée : 200 avec mot de passe', r.status === 200);
r = await envoi(formulaire(), pre);
verifier('demande de test acceptée sans e-mail configuré', r.status === 200 && (await r.json()).ok === true);

console.log('Production : pages et redirections');
r = await worker.fetch(req('/'), prod);
verifier('accueil : 200, pas de noindex', r.status === 200 && !r.headers.get('X-Robots-Tag'));
verifier('politique de sécurité présente', (r.headers.get('Content-Security-Policy') || '').includes("default-src 'self'"));
r = await worker.fetch(req('/premier-echange/'), prod);
verifier('page premier échange : 200', r.status === 200);
r = await worker.fetch(req('/contact/'), prod);
verifier('ancienne page /contact/ : 301 → /premier-echange/', r.status === 301 && r.headers.get('Location') === 'https://vizibili.fr/premier-echange/');
r = await worker.fetch(req('/contact/?besoin=nettoyage'), prod);
verifier('la redirection conserve les paramètres', r.headers.get('Location') === 'https://vizibili.fr/premier-echange/?besoin=nettoyage');
r = await worker.fetch(req('/contact/merci/'), prod);
verifier('ancienne confirmation : 301 → /premier-echange/merci/', r.headers.get('Location') === 'https://vizibili.fr/premier-echange/merci/');
r = await worker.fetch(req('/pages/contact'), prod);
verifier('ancien site /pages/contact : 301 → /premier-echange/', r.status === 301 && r.headers.get('Location').endsWith('/premier-echange/'));
r = await worker.fetch(req('/blogs/visibilite-locale/gerer-fiche-google-my-business'), prod);
verifier('ancien article : 410', r.status === 410);
r = await worker.fetch(req('/page-inconnue/'), prod);
verifier('adresse inconnue : 404', r.status === 404);
r = await worker.fetch(req('/api/demande'), prod);
verifier('GET sur le formulaire : 405', r.status === 405);

console.log('Formulaire');
const envProd = { ...prod, EMAIL: { send: async () => { throw new Error('hors Cloudflare'); } }, DESTINATAIRE: 'hello@vizibili.fr', EXPEDITEUR: 'formulaire@vizibili.fr' };
r = await envoi(formulaire({ entreprise_web: 'spam' }), prod);
verifier('champ piège : « ok » sans rien envoyer', r.status === 200 && (await r.json()).ok === true);
for (const [nom, extra] of [['nom manquant', { nom: '' }], ['e-mail invalide', { email: 'marie@' }], ['secteur hors liste', { secteur: 'Inventé' }],
  ['objectif hors liste', { objectif: 'Inventé' }], ['téléphone invalide', { telephone: '12' }]]) {
  r = await envoi(formulaire(extra), prod);
  verifier(`${nom} : 422`, r.status === 422);
}
r = await envoi(formulaire({ telephone: '' }), pre);
verifier('téléphone facultatif : accepté vide', r.status === 200);
r = await envoi(formulaire({ secteur: 'Artisanat et bâtiment', recherche: null }), pre);
verifier('prospect hors propreté : accepté (pas d’exclusion automatique)', r.status === 200);
r = await envoi(formulaire({ secteur: 'Autre secteur', objectif: 'Autre besoin' }), pre);
verifier('secteur « Autre » : accepté', r.status === 200);
r = await envoi(formulaire(), prod);
verifier('production sans e-mail configuré : 503 (jamais un faux succès)', r.status === 503);
r = await envoi(formulaire(), envProd);
verifier('échec d’envoi de l’e-mail : 502 (jamais un faux succès)', r.status === 502);
r = await worker.fetch(req('/api/demande', { method: 'POST', body: formulaire({ nom: '' }) }), prod);
verifier('sans JavaScript : retour au formulaire en erreur', r.status === 303 && r.headers.get('Location').includes('/premier-echange/?erreur=1'));
r = await envoi(formulaire(), { ...pre, TURNSTILE_SECRET: 'x' });
verifier('Turnstile actif sans jeton : 403', r.status === 403);

console.log('Déduplication');
const id = 'VZ-20261014-ABCDEF12';
r = await envoi(formulaire({}, id), pre);
const premier = await r.json();
r = await envoi(formulaire({}, id), pre);
const second = await r.json();
verifier('premier envoi enregistré', premier.ok === true && !premier.doublon);
verifier('second envoi du même identifiant : ignoré (doublon)', second.ok === true && second.doublon === true);
const envoyes = [];
const envCapture = { ...pre, EMAIL: { send: async (m) => envoyes.push(m) }, DESTINATAIRE: 'hello@vizibili.fr', EXPEDITEUR: 'formulaire@vizibili.fr' };
// Remplace l'import 'cloudflare:email' indisponible hors Cloudflare : on vérifie seulement qu'un doublon n'appelle jamais l'envoi
r = await envoi(formulaire({}, id), envCapture);
verifier('un doublon ne déclenche aucun e-mail', envoyes.length === 0);

console.log('E-mail');
const brut = mime('formulaire@vizibili.fr', 'hello@vizibili.fr', '[TEST] Premier échange : Propre & Net (Nettoyage et propreté)', 'Nom : Marie Test\r\nSecteur : Nettoyage et propreté', 'marie@exemple.fr');
const corps = brut.split('\r\n\r\n')[1].replace(/\r\n/g, '');
const decode = new TextDecoder().decode(Uint8Array.from(atob(corps), (c) => c.charCodeAt(0)));
verifier('corps UTF-8 décodable (accents)', decode.includes('Secteur : Nettoyage et propreté'));
verifier('réponse directe au prospect', brut.includes('Reply-To: <marie@exemple.fr>'));
verifier('lignes ≤ 78 caractères', brut.split('\r\n').every((l) => l.length <= 78));

console.log('SMTP (serveur de messagerie indépendant de Cloudflare)');
// Faux serveur SMTP : rejoue le dialogue et enregistre ce qu'il reçoit
function fauxSmtp({ starttls = false, plain = true, refuserAuth = false } = {}) {
  const journal = { commandes: [], message: '', tls: false };
  const dec = new TextDecoder(), enc = new TextEncoder();
  const fabriquer = () => {
    let ctrl, enData = false, tampon = '';
    const readable = new ReadableStream({ start(c) { ctrl = c; } });
    const envoyer = (t) => ctrl.enqueue(enc.encode(t + '\r\n'));
    const ehlo = () => envoyer(['250-smtp.exemple.fr', starttls && !journal.tls ? '250-STARTTLS' : null, plain ? '250-AUTH PLAIN LOGIN' : '250-AUTH LOGIN', '250 8BITMIME'].filter(Boolean).join('\r\n'));
    const writable = new WritableStream({ write(o) {
      tampon += dec.decode(o);
      if (enData) {
        const fin = tampon.indexOf('\r\n.\r\n');
        if (fin < 0) return;
        journal.message = tampon.slice(0, fin); tampon = tampon.slice(fin + 5); enData = false; envoyer('250 OK');
      }
      let i;
      while ((i = tampon.indexOf('\r\n')) >= 0 && !enData) {
        const l = tampon.slice(0, i); tampon = tampon.slice(i + 2); journal.commandes.push(l);
        if (/^EHLO/.test(l)) ehlo();
        else if (l === 'STARTTLS') envoyer('220 Go');
        else if (/^AUTH PLAIN/.test(l)) envoyer(refuserAuth ? '535 Refusé' : '235 OK');
        else if (l === 'AUTH LOGIN') envoyer('334 VXNlcm5hbWU6');
        else if (journal.commandes.at(-2) === 'AUTH LOGIN') envoyer('334 UGFzc3dvcmQ6');
        else if (journal.commandes.at(-3) === 'AUTH LOGIN') envoyer(refuserAuth ? '535 Refusé' : '235 OK');
        else if (/^MAIL FROM/.test(l)) envoyer('250 OK');
        else if (/^RCPT TO/.test(l)) envoyer('250 OK');
        else if (l === 'DATA') { envoyer('354 Go'); enData = true; }
        else if (l === 'QUIT') envoyer('221 Bye');
      }
    } });
    return { readable, writable, envoyer };
  };
  const connecter = (adresse, options) => {
    journal.adresse = adresse; journal.options = options;
    const s = fabriquer();
    s.startTls = () => { journal.tls = true; return fabriquer(); };
    s.close = () => {};
    s.envoyer('220 smtp.exemple.fr prêt');
    return s;
  };
  return { journal, connecter };
}
const envSmtp = { SMTP_HOTE: 'smtp.exemple.fr', SMTP_UTILISATEUR: 'hello@vizibili.fr', SMTP_MOT_DE_PASSE: 'secret' };
const msg = mime('hello@vizibili.fr', 'hello@vizibili.fr', '[TEST] Premier échange : Propre & Net', 'Ligne 1\r\n.ligne avec point', 'marie@exemple.fr');
let f = fauxSmtp();
await envoyerSmtp(envSmtp, 'hello@vizibili.fr', 'hello@vizibili.fr', msg, f.connecter);
verifier('port 465 : TLS direct', f.journal.adresse.port === 465 && f.journal.options.secureTransport === 'on');
verifier('authentification PLAIN', f.journal.commandes.some((c) => c.startsWith('AUTH PLAIN ')));
verifier('message transmis en entier', f.journal.message.includes('Subject:') && f.journal.message.includes('Reply-To: <marie@exemple.fr>'));
verifier('dialogue complet jusqu’à QUIT', f.journal.commandes.at(-1) === 'QUIT');
f = fauxSmtp({ starttls: true, plain: false });
await envoyerSmtp({ ...envSmtp, SMTP_PORT: '587' }, 'hello@vizibili.fr', 'hello@vizibili.fr', msg, f.connecter);
verifier('port 587 : STARTTLS puis AUTH LOGIN', f.journal.tls && f.journal.commandes.includes('STARTTLS') && f.journal.commandes.includes('AUTH LOGIN') && f.journal.message.length > 0);
f = fauxSmtp({ refuserAuth: true });
let erreur = null;
try { await envoyerSmtp(envSmtp, 'hello@vizibili.fr', 'hello@vizibili.fr', msg, f.connecter); } catch (e) { erreur = e.message; }
verifier('mot de passe refusé : erreur levée, mot de passe absent du message', erreur && erreur.includes('AUTH') && !erreur.includes('secret'));
erreur = null;
try { await envoyerSmtp({ ...envSmtp, SMTP_PORT: '25' }, 'a@b.fr', 'a@b.fr', msg, f.connecter); } catch (e) { erreur = e.message; }
verifier('port 25 refusé (bloqué par Cloudflare)', erreur && erreur.includes('25'));
r = await envoi(formulaire(), { ...prod, ...envSmtp, DESTINATAIRE: 'hello@vizibili.fr' });
verifier('SMTP injoignable en production : 502 (jamais un faux succès)', r.status === 502);

console.log('Attribution (SOP Google Ads, porte C)');
f = fauxSmtp();
r = await envoi(formulaire({ prov_gclid: 'Cj0KCQ_test-123', prov_terme: 'nettoyage bureaux', prov_contenu: 'annonce-a', prov_referent: 'www.google.com',
  prov_date_arrivee: '2026-10-14T09:00:00.000Z', prov_campagne: 'SEARCH | B2B' }), { ...pre, ...envSmtp, DESTINATAIRE: 'hello@vizibili.fr', _connecterSmtp: f.connecter });
const corpsMail = new TextDecoder().decode(Uint8Array.from(atob(f.journal.message.split('\r\n\r\n')[1].replace(/\r\n/g, '')), (c) => c.charCodeAt(0)));
const ligne = corpsMail.trim().split('\r\n').at(-1).split('\t');
verifier('envoi accepté', r.status === 200);
verifier('valeur du gclid transmise', corpsMail.includes('gclid:Cj0KCQ_test-123'));
verifier('terme, contenu, référent et heure d’arrivée transmis', corpsMail.includes('Terme : nettoyage bureaux') && corpsMail.includes('Contenu : annonce-a') && corpsMail.includes('www.google.com') && corpsMail.includes('2026-10-14T09:00'));
verifier('ligne de registre : 30 colonnes, comme le modèle CSV', ligne.length === 30, ligne.length);
verifier('ligne de registre : test marqué « Oui » et préfixe TEST', ligne[1] === 'Oui' && ligne[0].startsWith('TEST '));
f = fauxSmtp();
await envoi(formulaire({ prov_gclid: '<script>' , prov_wbraid: 'WB_abc' }), { ...pre, ...envSmtp, DESTINATAIRE: 'hello@vizibili.fr', _connecterSmtp: f.connecter });
const corps2 = new TextDecoder().decode(Uint8Array.from(atob(f.journal.message.split('\r\n\r\n')[1].replace(/\r\n/g, '')), (c) => c.charCodeAt(0)));
verifier('identifiant de clic invalide ignoré, wbraid retenu', !corps2.includes('<script>') && corps2.includes('wbraid:WB_abc'));

console.log(`\n${ok} réussis, ${ko} échoués`);
process.exit(ko ? 1 : 0);
