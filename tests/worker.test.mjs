// Tests du Worker sans Cloudflare : ASSETS simulé par les fichiers de public/.
import { readFile } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import worker, { mime } from '../src/index.js';

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

let ok = 0, ko = 0;
function verifier(nom, cond, detail = '') { if (cond) { ok++; console.log('  ✓', nom); } else { ko++; console.log('  ✗', nom, detail); } }
const auth = (m) => ({ Authorization: 'Basic ' + btoa('recette:' + m) });
const prod = { ASSETS, ENVIRONNEMENT: 'production' };
const pre = { ASSETS, ENVIRONNEMENT: 'preproduction', PREPROD_MOT_DE_PASSE: 'secret-test' };
const req = (chemin, init = {}) => new Request('https://vizibili.fr' + chemin, init);

function formulaire(extra = {}) {
  const fd = new FormData();
  const base = { nom: 'Marie Test', entreprise: 'Propre & Net', activite: 'Entreprise de nettoyage', contact: 'marie@exemple.fr',
    besoin: 'Trouver plus de clients', objectif: 'Des contrats de bureaux', prov_source: 'google', prov_support: 'cpc', prov_arrivee: '/entreprises-de-nettoyage/', ...extra };
  for (const [k, v] of Object.entries(base)) fd.append(k, v);
  return fd;
}
const json = { Accept: 'application/json' };

console.log('Préproduction');
let r = await worker.fetch(req('/'), pre);
verifier('sans mot de passe : 401', r.status === 401);
verifier('401 non indexable', r.headers.get('X-Robots-Tag') === 'noindex, nofollow');
r = await worker.fetch(req('/', { headers: auth('faux') }), pre);
verifier('mauvais mot de passe : 401', r.status === 401);
r = await worker.fetch(req('/', { headers: auth('secret-test') }), pre);
verifier('bon mot de passe : 200', r.status === 200);
verifier('page marquée noindex', r.headers.get('X-Robots-Tag') === 'noindex, nofollow');
r = await worker.fetch(req('/robots.txt', { headers: auth('secret-test') }), pre);
verifier('robots.txt bloque tout', (await r.text()).includes('Disallow: /'));
r = await worker.fetch(req('/'), { ...pre, PREPROD_MOT_DE_PASSE: '' });
verifier('mot de passe non configuré : fermé', r.status === 401);
r = await worker.fetch(req('/api/diagnostic', { method: 'POST', body: formulaire(), headers: { ...json, ...auth('secret-test') } }), pre);
verifier('formulaire sans e-mail configuré : accepté en préprod', r.status === 200 && (await r.json()).ok === true);

r = await worker.fetch(req('/'), { ...pre, PREPROD_MOT_DE_PASSE: '', PROTECTION: 'aucune' });
verifier('protection désactivée : ouvert sans mot de passe', r.status === 200);
verifier('protection désactivée : toujours noindex', r.headers.get('X-Robots-Tag') === 'noindex, nofollow');
r = await worker.fetch(req('/robots.txt'), { ...pre, PROTECTION: 'aucune' });
verifier('protection désactivée : robots.txt bloque toujours', (await r.text()).includes('Disallow: /'));

console.log('Production');
r = await worker.fetch(req('/'), prod);
verifier('accueil : 200', r.status === 200);
verifier('pas de noindex en production', !r.headers.get('X-Robots-Tag'));
verifier('politique de sécurité présente', (r.headers.get('Content-Security-Policy') || '').includes("default-src 'self'"));
verifier('nosniff', r.headers.get('X-Content-Type-Options') === 'nosniff');
r = await worker.fetch(req('/pages/contact'), prod);
verifier('ancienne page contact : 301 → /contact/', r.status === 301 && r.headers.get('Location') === 'https://vizibili.fr/contact/');
r = await worker.fetch(req('/products/audit-creation-optimisation-fiche-google-business-profile'), prod);
verifier('ancienne page audit : 301 → /offre/', r.status === 301 && r.headers.get('Location').endsWith('/offre/'));
r = await worker.fetch(req('/collections/formules/'), prod);
verifier('barre finale tolérée sur une redirection', r.status === 301);
r = await worker.fetch(req('/blogs/visibilite-locale/gerer-fiche-google-my-business'), prod);
verifier('ancien article : 410', r.status === 410);
verifier('410 affiche la page d’erreur', (await r.text()).includes("Cette page n'existe pas"));
r = await worker.fetch(req('/pages/test-google-local-services'), prod);
verifier('ancienne page de test : 410', r.status === 410);
r = await worker.fetch(req('/page-inconnue/'), prod);
verifier('adresse inconnue : 404', r.status === 404);
r = await worker.fetch(req('/api/diagnostic'), prod);
verifier('GET sur le formulaire : 405', r.status === 405);

console.log('Formulaire');
r = await worker.fetch(req('/api/diagnostic', { method: 'POST', body: formulaire({ entreprise_web: 'spam' }), headers: json }), prod);
verifier('champ piège : répond ok sans rien envoyer', r.status === 200 && (await r.json()).ok === true);
r = await worker.fetch(req('/api/diagnostic', { method: 'POST', body: formulaire({ nom: '' }), headers: json }), prod);
verifier('nom manquant : 422', r.status === 422);
r = await worker.fetch(req('/api/diagnostic', { method: 'POST', body: formulaire({ contact: 'marie@' }), headers: json }), prod);
verifier('contact invalide : 422', r.status === 422);
r = await worker.fetch(req('/api/diagnostic', { method: 'POST', body: formulaire({ besoin: 'inventé' }), headers: json }), prod);
verifier('besoin hors liste : 422', r.status === 422);
r = await worker.fetch(req('/api/diagnostic', { method: 'POST', body: formulaire({ contact: '06 12 34 56 78' }), headers: json }), prod);
verifier('production sans e-mail configuré : 503 (jamais un faux succès)', r.status === 503);
r = await worker.fetch(req('/api/diagnostic', { method: 'POST', body: formulaire({ nom: '' }) }), prod);
verifier('sans JavaScript : redirection vers le formulaire en erreur', r.status === 303 && r.headers.get('Location').endsWith('/contact/?erreur=1'));
r = await worker.fetch(req('/api/diagnostic', { method: 'POST', body: formulaire(), headers: { ...json, ...auth('secret-test') } }), { ...pre, TURNSTILE_SECRET: 'x' });
verifier('Turnstile actif sans jeton : 403', r.status === 403);

const env = [];
const envoi = { send: async (m) => env.push(m) };
r = await worker.fetch(req('/api/diagnostic', { method: 'POST', body: formulaire(), headers: json }), { ...prod, EMAIL: envoi, DESTINATAIRE: 'hello@vizibili.fr', EXPEDITEUR: 'formulaire@vizibili.fr' });
verifier('envoi e-mail hors Cloudflare : échec signalé (502), pas de faux succès', r.status === 502);

console.log('E-mail');
const brut = mime('formulaire@vizibili.fr', 'hello@vizibili.fr', 'Diagnostic : Propre & Net (Trouver plus de clients)', 'Nom : Marie Test\r\nActivité : Entreprise de nettoyage', 'marie@exemple.fr');
const corps = brut.split('\r\n\r\n')[1].replace(/\r\n/g, '');
const decode = new TextDecoder().decode(Uint8Array.from(atob(corps), (c) => c.charCodeAt(0)));
verifier('corps UTF-8 décodable (accents)', decode.includes('Activité : Entreprise de nettoyage'));
verifier('objet encodé', /^Subject: =\?UTF-8\?B\?/m.test(brut));
verifier('réponse directe au prospect', brut.includes('Reply-To: <marie@exemple.fr>'));
verifier('lignes ≤ 78 caractères', brut.split('\r\n').every((l) => l.length <= 78));

console.log(`\n${ok} réussis, ${ko} échoués`);
process.exit(ko ? 1 : 0);
