#!/usr/bin/env python3
"""Recette statique des pages générées : liens, métadonnées, registre éditorial, accessibilité de base."""
import os, re, json, sys
from html.parser import HTMLParser

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public')
PUBLIC_ROUTES = set()
for d, _, fs in os.walk(RACINE):
    for f in fs:
        rel = os.path.relpath(os.path.join(d, f), RACINE).replace(os.sep, '/')
        PUBLIC_ROUTES.add('/' + rel)
        if f == 'index.html':
            PUBLIC_ROUTES.add('/' + os.path.relpath(d, RACINE).replace(os.sep, '/').strip('.') + ('/' if d != RACINE else ''))
PUBLIC_ROUTES.add('/')
EXTERNES_OK = {'/api/demande', '/fonts/archivo-800.woff2', '/fonts/inter-400.woff2', '/assets/favicon.png', '/assets/apple-touch-icon.png'}

# Registre éditorial (Gates 2 et 3) : interdits dans le texte visible
INTERDITS = [
    (r'—', 'tiret cadratin'), (r'sans engagement', '« sans engagement »'), (r'\bGGS\b|Growth System', 'GGS'),
    (r'\bje\b|\bj’|\bj\'', 'voix « je »'), (r'\bmienne?\b|\bmon agence\b', 'voix « je »'),
    (r'\blead', 'jargon : lead'), (r'\blanding', 'jargon : landing'), (r'\btracking', 'jargon : tracking'),
    (r'\bSEO\b', 'jargon : SEO'), (r'\bGA4\b', 'jargon : GA4'), (r'\bCRM\b', 'jargon : CRM'),
    (r'notre équipe|nos équipes|nos experts', 'équipe suggérée'), (r'\+\s?\d+\s?%', 'chiffre de résultat'),
    (r'garanti(?!e?s?\s+de)', None),  # contrôlé à la main ci-dessous
]

class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.texte = []; self.liens = []; self.h1 = 0; self.titre = ''; self._t = False
        self.meta = {}; self.canon = None; self.ld = []; self._ld = False; self.imgs_sans_alt = 0
        self.inputs = []; self.labels_for = set(); self.ignore = 0; self.robots = None
    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag in ('script', 'style'):
            self.ignore += 1
            if a.get('type') == 'application/ld+json': self._ld = True
        if tag == 'title': self._t = True
        if tag == 'h1': self.h1 += 1
        if tag == 'a' and 'href' in a: self.liens.append(a['href'])
        if tag == 'meta' and a.get('name') == 'description': self.meta['description'] = a.get('content')
        if tag == 'meta' and a.get('name') == 'robots': self.robots = a.get('content')
        if tag == 'link' and a.get('rel') == 'canonical': self.canon = a.get('href')
        if tag == 'img' and not a.get('alt'): self.imgs_sans_alt += 1
        if tag in ('input', 'textarea') and a.get('type') not in ('hidden', 'radio'): self.inputs.append(a.get('id'))
        if tag == 'label' and a.get('for'): self.labels_for.add(a['for'])
    def handle_endtag(self, tag):
        if tag in ('script', 'style'): self.ignore -= 1; self._ld = False
        if tag == 'title': self._t = False
    def handle_data(self, d):
        if self._t: self.titre += d
        if self._ld: self.ld.append(d)
        if not self.ignore: self.texte.append(d)
    def handle_comment(self, d):
        pass  # les témoignages en attente d'accord sont en commentaire : non publiés

erreurs, avert, titres, descs = [], [], {}, {}
pages = sorted(p for p in PUBLIC_ROUTES if p.endswith('.html'))
for p in pages:
    chemin = os.path.join(RACINE, p.lstrip('/'))
    src = open(chemin, encoding='utf-8').read()
    x = P(); x.feed(src)
    route = p[:-len('index.html')] if p.endswith('index.html') else p
    texte = re.sub(r'\s+', ' ', ' '.join(x.texte))
    if x.h1 != 1: erreurs.append(f'{route} : {x.h1} H1')
    if not x.titre: erreurs.append(f'{route} : pas de <title>')
    titres.setdefault(x.titre, []).append(route)
    if not x.meta.get('description'): erreurs.append(f'{route} : pas de meta description')
    else:
        descs.setdefault(x.meta['description'], []).append(route)
        if not (70 <= len(x.meta['description']) <= 160) and route not in ('/mentions-legales/', '/premier-echange/merci/', '/404.html'):
            avert.append(f'{route} : meta description de {len(x.meta["description"])} caractères')
    if len(x.titre) > 65: avert.append(f'{route} : title de {len(x.titre)} caractères')
    if route != '/404.html' and x.canon != 'https://vizibili.fr' + route: erreurs.append(f'{route} : canonique {x.canon}')
    for bloc in x.ld:
        try: json.loads(bloc)
        except Exception as e: erreurs.append(f'{route} : JSON-LD invalide ({e})')
    if x.imgs_sans_alt: erreurs.append(f'{route} : {x.imgs_sans_alt} image(s) sans alt')
    for i in x.inputs:
        if i and i not in x.labels_for: erreurs.append(f'{route} : champ #{i} sans label')
    for l in x.liens:
        if l.startswith(('mailto:', 'https://', 'http://', '#')): continue
        cible = l.split('?')[0].split('#')[0]
        if cible not in PUBLIC_ROUTES and cible not in EXTERNES_OK:
            erreurs.append(f'{route} : lien interne cassé {l}')
    for motif, nom in INTERDITS:
        if nom is None: continue
        for m in re.finditer(motif, texte, flags=re.I):
            ctx = texte[max(0, m.start() - 40): m.end() + 40]
            # Paroles du lecteur (questions de FAQ, questions citées) : autorisées
            if nom == 'voix « je »' and re.search(r'Je travaille surtout|Je ne suis pas dans|ai-je', ctx):
                continue
            erreurs.append(f'{route} : {nom} → « …{ctx}… »')
    for m in re.finditer(r'garanti\w*', texte):
        ctx = texte[max(0, m.start() - 140): m.end() + 20]
        if not re.search(r'jamais|ne pouvons|personne ne peut|ne promett|pas', ctx, flags=re.I):
            erreurs.append(f'{route} : promesse de garantie → « …{ctx}… »')
    if '[' in texte and re.search(r'\[[A-ZÉ ]{4,}', texte):
        avert.append(f'{route} : élément à compléter avant publication : ' + ', '.join(sorted(set(re.findall(r'\[([A-ZÉ][A-ZÉ ,]+)', texte)))))

for t, r in titres.items():
    if len(r) > 1: erreurs.append(f'title en double « {t} » : {r}')
for t, r in descs.items():
    if len(r) > 1: erreurs.append(f'meta description en double : {r}')

sitemap = open(os.path.join(RACINE, 'sitemap.xml'), encoding='utf-8').read()
for loc in re.findall(r'<loc>https://vizibili.fr(.*?)</loc>', sitemap):
    if loc not in PUBLIC_ROUTES: erreurs.append(f'sitemap : {loc} absent')
if '/premier-echange/merci/' in sitemap: erreurs.append('sitemap : page de confirmation indexée')

print(f'{len(pages)} pages contrôlées')
print(f'\nERREURS ({len(erreurs)})'); [print(' -', e) for e in erreurs]
print(f'\nÀ SAVOIR ({len(avert)})'); [print(' -', a) for a in avert]
sys.exit(1 if erreurs else 0)
