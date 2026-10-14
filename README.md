# vizibili.fr · refonte octobre 2026 · paquet de préproduction

Site statique servi par un Worker Cloudflare : pages, formulaire de diagnostic, redirections des anciennes adresses, préproduction protégée par mot de passe et non indexée.

**Ce paquet ne touche pas au site en ligne.** La commande ci-dessous crée un Worker séparé, `vizibili-preprod`, sur une adresse `workers.dev`.

## Contenu

| Élément | Rôle |
|---|---|
| `public/` | Le site généré : 14 pages, page 404, `sitemap.xml`, `robots.txt`, `assets/styles.css`, `assets/site.js` |
| `src/index.js` | Le Worker : formulaire, mot de passe de préproduction, 301 et 410, en-têtes de sécurité |
| `wrangler.jsonc` | Configuration Cloudflare (production et préproduction) |
| `build.py` | Régénère `public/` à partir des textes validés au Gate 3 |
| `tests/` | Contrôles des pages et tests du Worker |

## Avant de déployer : 4 fichiers à reprendre du site actuel

Copiez-les depuis le dossier du site en ligne, aux mêmes emplacements :

- `public/fonts/archivo-700.woff2`, `archivo-800.woff2`, `inter-400.woff2`, `inter-600.woff2`
  (la feuille de style actuelle les appelle déjà ; s'il en manque, le site retombe proprement sur la police système)
- `public/assets/favicon.png` et `public/assets/apple-touch-icon.png`

`public/assets/logo-vizibili.png` est déjà inclus (version 92 px que tu as transmise).

## Déployer la préproduction par GitHub (sans terminal)

**Ne jamais déposer ces fichiers dans le dépôt GitHub du site actuel** : il est relié à Cloudflare et publierait directement sur vizibili.fr.

1. GitHub › **New repository** › nom `vizibili-preprod`, **privé**, sans README.
2. Dans le dépôt vide : **uploading an existing file** (ou Add file › Upload files).
3. Décompresser le .zip, puis glisser **son contenu** (pas le dossier lui-même, pas le .zip) : `public`, `src`, `tests`, `build.py`, `package.json`, `README.md`, `wrangler.jsonc`. Puis **Commit changes**.
4. Cloudflare › Workers & Pages › **Create** › **Import a repository** › choisir `vizibili-preprod`. Nom du projet : `vizibili-preprod` (identique à `wrangler.jsonc`). Commande de déploiement : `npx wrangler deploy` (proposée par défaut). Aucune commande de build.
5. Une fois déployé : **Settings › Variables and Secrets › Add** › type **Secret**, nom `PREPROD_MOT_DE_PASSE`, valeur au choix.
6. Ouvrir l'adresse `vizibili-preprod.<sous-domaine>.workers.dev` : identifiant libre, mot de passe de l'étape 5.

Tant que l'étape 5 n'est pas faite, la préproduction reste fermée à tout le monde (voulu).

## Recevoir les demandes par e-mail

Le formulaire envoie chaque demande par e-mail, via Cloudflare, sans service tiers.

1. Dans Cloudflare, sur le domaine vizibili.fr : **Email › Email Routing** activé.
2. La boîte qui doit recevoir les demandes ajoutée et **vérifiée** comme adresse de destination.
3. Ensuite seulement, demander l'ajout de l'envoi d'e-mail à la configuration (une ligne `send_email`) : sans Email Routing actif, Cloudflare refuserait le déploiement.

En attendant, en préproduction le formulaire répond « envoyé » et la demande apparaît dans les journaux du Worker (Cloudflare › vizibili-preprod › Logs). En production, il refuse proprement (message d'erreur avec l'adresse e-mail) : jamais de faux succès.

## Protection anti-robots (recommandée avant la production)

Le formulaire a déjà un champ piège invisible. Pour ajouter Cloudflare Turnstile :

1. Cloudflare › Turnstile › créer un widget pour `vizibili.fr` (et l'adresse workers.dev de préproduction).
2. `TURNSTILE_SITE_KEY=<clé publique> python3 build.py`
3. Secret `TURNSTILE_SECRET` ajouté comme à l'étape 5 ci-dessus.
4. Redéployer.

## Vérifier localement

```
python3 build.py
python3 tests/verifier_pages.py
node tests/worker.test.mjs
```

## Production (Phase 6, uniquement après GO écrit)

Ce paquet ne contient **aucune** configuration de production. Elle sera fournie au Gate 6, avec le nom exact du Worker qui sert aujourd'hui vizibili.fr.
