import re
#!/usr/bin/env python3
"""Génère le site statique ViZiBiLi (refonte octobre 2026) dans public/.

Usage :  python3 build.py
Option : TURNSTILE_SITE_KEY=<clé publique> python3 build.py   (active la vérification anti-robots)
Les textes sont ceux validés aux Gates 2 et 3 (PHASE3_TEXTES_LOT1 à LOT3).
"""
import json, os, html

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public')
SITE = 'https://vizibili.fr'
# Clé publique Turnstile (widget « ViZiBiLi formulaire », préproduction + vizibili.fr), fournie le 15/10/2026. La clé secrète reste un Secret Cloudflare.
TURNSTILE = os.environ.get('TURNSTILE_SITE_KEY', '0x4AAAAAAFX1uxcmUynbL_zn').strip()
LOGO = '/assets/logo-vizibili.png'
OG_IMAGE = '/assets/og-vizibili.png'
# Logo vectoriel sans fond (15/10/2026), redessiné d'après l'ancien PNG 92 px sur fond blanc.
LOGO_MARK = '<svg class="logo-mark" xmlns="http://www.w3.org/2000/svg" viewBox="14 14 72 100" width="72" height="100" aria-hidden="true" focusable="false"><path d="M50 112C40 96 16 78 16 50A34 34 0 1 1 84 50C84 78 60 96 50 112Z" fill="#141414"/><path d="M25 50A25 25 0 1 0 75 50A25 25 0 1 0 25 50Z" fill="#6B635B"/><path d="M27.5 50A22.5 22.5 0 1 0 72.5 50A22.5 22.5 0 1 0 27.5 50Z" fill="#141414"/><path d="M29.3 57.5A22 22 0 0 0 70.7 42.5Q58 78 29.3 57.5Z" fill="#D77229"/><path d="M50 59C36 50 37.5 37 45.5 37.5C48 37.7 49.6 39.6 50 42C50.4 39.6 52 37.7 54.5 37.5C62.5 37 64 50 50 59Z" fill="#FF9A4D"/></svg>'

NAV = [('/methode/', 'Méthode'), ('/entreprises-de-nettoyage/', 'Spécialité nettoyage'), ('/offre/', 'Offre'),
       ('/cas-clients/', 'Cas clients'), ('/a-propos/', 'À propos')]

ORG = {
    "@type": "ProfessionalService", "@id": SITE + "/#organisation", "name": "ViZiBiLi", "url": SITE + "/",
    "logo": SITE + LOGO, "image": SITE + LOGO, "email": "hello@vizibili.fr",
    "description": "Acquisition de clients sur Google pour les entreprises locales et les entreprises de nettoyage : annonces, pages dédiées et suivi des demandes jusqu'au client signé.",
    "address": {"@type": "PostalAddress", "streetAddress": "5 Rue des Sapins", "postalCode": "88390",
                "addressLocality": "Darnieulles", "addressRegion": "Vosges", "addressCountry": "FR"},
    "areaServed": [{"@type": "AdministrativeArea", "name": "Vosges"}, {"@type": "Country", "name": "France"}],
}


def esc(t):
    return html.escape(t, quote=True)


def page(chemin, titre, desc, corps, actif=None, jsonld=None, indexer=True, formulaire=False):
    canon = SITE + chemin
    ld = [ORG] + (jsonld or [])
    ld_txt = json.dumps({"@context": "https://schema.org", "@graph": ld}, ensure_ascii=False, indent=1).replace('</', '<\\/')
    nav = '\n'.join(
        f'      <a href="{u}"{" aria-current=\"page\"" if u == actif else ""}>{esc(l)}</a>' for u, l in NAV)
    robots = '' if indexer else '\n<meta name="robots" content="noindex">'
    turnstile = ('\n<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>'
                 if (formulaire and TURNSTILE) else '')
    barre = '' if formulaire or chemin.startswith('/premier-echange/') else (
        '\n<div class="barre-mobile"><a href="/premier-echange/" class="btn btn-plein">Demander un premier échange</a></div>')
    doc = f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(titre)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}">{robots}
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="48x48" href="/assets/favicon.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="preload" href="/fonts/archivo-800.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/inter-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/styles.css">
<meta property="og:title" content="{esc(titre)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_FR">
<meta property="og:image" content="{SITE}{OG_IMAGE}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<script type="application/ld+json">
{ld_txt}
</script>{turnstile}
<script src="/assets/site.js" defer></script>
</head>
<body>
<a class="evitement" href="#contenu">Aller au contenu</a>
<header class="site-header">
  <a href="/" class="logo" aria-label="ViZiBiLi, accueil">{LOGO_MARK}<span class="logo-nom">ViZiBiLi</span></a>
  <nav class="site-nav" id="navigation" aria-label="Navigation principale">
{nav}
  </nav>
  <a href="/premier-echange/" class="btn btn-plein">Demander un premier échange</a>
  <button type="button" class="bouton-menu" aria-controls="navigation" aria-expanded="false" aria-label="Ouvrir le menu">
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="#141414" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M3 5h14M3 10h14M3 15h14"/></svg>
  </button>
</header>
<main id="contenu">
{corps.strip()}
</main>
<footer class="pied">
  <div>© 2026 ViZiBiLi · 5 Rue des Sapins, 88390 Darnieulles · <a href="mailto:hello@vizibili.fr">hello@vizibili.fr</a></div>
  <nav aria-label="Nos pages" class="pied-pages"><a href="/methode/">Méthode</a><a href="/offre/">Offre</a><a href="/entreprises-de-nettoyage/">Entreprises de nettoyage</a><a href="/fiche-google-vosges/">Fiche Google dans les Vosges</a><a href="/cas-clients/">Cas clients</a><a href="/a-propos/">À propos</a><a href="/ressources/">Ressources</a><a href="/premier-echange/">Premier échange</a></nav>
  <nav aria-label="Informations légales"><a href="/mentions-legales/">Mentions légales</a><a href="/confidentialite/">Confidentialité</a></nav>
</footer>{barre}
</body>
</html>
'''
    dossier = os.path.join(RACINE, chemin.strip('/'))
    os.makedirs(dossier, exist_ok=True)
    with open(os.path.join(dossier, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(doc)
    return chemin


def bande(titre, texte, cta, lien='/premier-echange/'):
    return f'''
<section class="bande-finale">
  <h2>{titre}</h2>
  {f"<p>{texte}</p>" if texte else ""}
  <a href="{lien}" class="btn btn-plein">{cta}</a>
</section>'''


ICO_LOUPE = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="10.5" cy="10.5" r="6" fill="none" stroke="currentColor" stroke-width="2.6"/><path d="M15 15l5 5" stroke="currentColor" stroke-width="2.8" stroke-linecap="round"/></svg>'
ICO_CLIENT = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="12" cy="8.2" r="4" fill="currentColor"/><path d="M4.5 20.5c.8-4.3 3.8-6.6 7.5-6.6s6.7 2.3 7.5 6.6z" fill="currentColor"/></svg>'
ICO_COCHE = '<svg viewBox="0 0 12 12" aria-hidden="true" focusable="false"><path d="M2.6 6.3l2.2 2.2 4.6-4.8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
# Maillon de chaîne cassé : deux demi-maillons écartés et trois éclats. Le symbole le plus lisible pour « le lien est rompu ».
ICO_RUPTURE = ('<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">'
               '<path d="M13.2 10.4l-2.6-2.6a4.6 4.6 0 0 0-6.5 6.5l2.6 2.6" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>'
               '<path d="M18.8 21.6l2.6 2.6a4.6 4.6 0 0 0 6.5-6.5l-2.6-2.6" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>'
               '<path class="eclats" d="M12.5 19.5l-3 3M15.5 22.5l-.6 4M19.5 12.5l3-3M16.5 9.5l.6-4" stroke-width="2.4" stroke-linecap="round"/></svg>')


# ================================================================ COMPOSANTS LUDIQUES (V2, 16/10/2026)
def ico(corps, vb='0 0 24 24'):
    return f'<svg viewBox="{vb}" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{corps}</svg>'

I_ANNONCE = ico('<path d="M4 10v4a1 1 0 0 0 1 1h2l5 4V5L7 9H5a1 1 0 0 0-1 1z"/><path d="M16 9a4 4 0 0 1 0 6M18.5 6.5a7.5 7.5 0 0 1 0 11"/>')
I_PAGE = ico('<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8.5 8h7M8.5 12h7M8.5 16h4"/>')
I_SUIVI = ico('<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r=".9" fill="currentColor"/>')
I_FICHE = ico('<path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.4"/>')
I_DIAG = ico('<rect x="6" y="4" width="12" height="17" rx="2"/><path d="M9 4.5h6v2.5H9z"/><path d="M9 12l2 2 4-4"/>')
I_CONSTR = ico('<path d="M3 21h18"/><rect x="5" y="13" width="6" height="8"/><rect x="13" y="9" width="6" height="12"/><path d="M8 13V9M16 9V5"/>')
I_PILOT = ico('<path d="M4.5 17a8 8 0 1 1 15 0"/><path d="M12 13l4-4"/><circle cx="12" cy="13" r="1.3" fill="currentColor"/>')
I_COMM = ico('<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M8.5 16.5c1.2-1.6 2.2-1.6 2.8 0s1.6 1.6 2.8 0 1.6-1.6 2.4 0"/>')
I_DRAPEAU = ico('<path d="M5 21V4"/><path d="M5 4h12l-2.5 4L17 12H5"/>')
I_MAILLON = ico('<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>')
I_CLE = ico('<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M17 6l2 2M15 8l2 2"/>')
I_VOUS = ico('<circle cx="12" cy="8" r="4"/><path d="M4.5 20.5c.8-4.3 3.8-6.6 7.5-6.6s6.7 2.3 7.5 6.6"/>')
I_LOUPE = ico('<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>')
I_COCHE = ico('<path d="M5 12.5l4.5 4.5L19 7.5"/>')
I_NETTOYAGE = ico('<path d="M9 3h4v4H9z"/><path d="M8 7h6l1 4v9a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1v-9z"/><path d="M17 5h3M18.5 3.5v3M17.5 9.5h2"/>')
I_BOUTIQUE = ico('<path d="M4 9l1.5-5h13L20 9"/><path d="M4 9h16v2.5a2.7 2.7 0 0 1-5.3 0 2.7 2.7 0 0 1-5.4 0 2.7 2.7 0 0 1-5.3 0z"/><path d="M5.5 13v8h13v-8M10 21v-5h4v5"/>')
I_BUREAU = ico('<rect x="4" y="3" width="16" height="18" rx="1.5"/><path d="M8 7h2M14 7h2M8 11h2M14 11h2M8 15h2M14 15h2M11 21v-3h2v3"/>')
I_VITRE = ico('<rect x="4" y="4" width="16" height="16" rx="1.5"/><path d="M12 4v16M4 12h16"/><path d="M6.8 9.2l2.4-2.4M14.8 17.2l2.4-2.4"/>')
I_MAISON = ico('<path d="M3.5 11L12 4l8.5 7"/><path d="M6 9.5V20h12V9.5"/><path d="M10 20v-5h4v5"/>')
I_RECURRENT = ico('<rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M3.5 9.5h17M8 3v4M16 3v4"/><path d="M15.5 14.5a3.5 3.5 0 1 1-1.2-2.6"/><path d="M14.8 10.6l-.5 1.4 1.4.4"/>')
I_DEVIS = ico('<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M14.5 12.2a2.7 2.7 0 1 0 0 3.6M9.3 13.3h3.8M9.3 14.9h3.8"/>')
I_EURO = ico('<path d="M17.5 6.6A6.6 6.6 0 1 0 17.5 17.4"/><path d="M4.5 10.4h8.5M4.5 13.6h8.5"/>')
I_CLIC = ico('<path d="M7 3.5l11 6.8-5 1.3-2.1 4.9z"/><path d="M13 11.6l5 5"/>')
I_DEMANDE = ico('<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3.5 6.5L12 13l8.5-6.5"/>')
I_TRI = ico('<path d="M4 5h16l-6 7v6l-4 2v-8z"/>')
I_RDV = ico('<rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M3.5 9.5h17M8 3v4M16 3v4"/><path d="M9 14.5l2 2 4-4"/>')
I_MESURE = ico('<path d="M4 20h16"/><rect x="6" y="11" width="3" height="7" rx=".5"/><rect x="11" y="6.5" width="3" height="11.5" rx=".5"/><rect x="16" y="13" width="3" height="5" rx=".5"/>')
I_HAUSSE = ico('<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>')
I_BULLE = ico('<path d="M4 5h16v11H9.5L4 20.5z"/><path d="M8 9.5h8M8 12.5h5"/>')
I_OEIL = ico('<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>')
I_CADEAU = ico('<rect x="4" y="9" width="16" height="11" rx="1"/><path d="M3 9h18M12 9v11"/><path d="M12 9C10.5 6 7 5.5 7 7.6S12 9 12 9zM12 9c1.5-3 5-3.5 5-1.4S12 9 12 9z"/>')
I_LIVRE = ico('<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z"/><path d="M4 20.5V5.5M8 7.5h8"/>')
I_HORLOGE = ico('<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>')
I_FLECHE = ico('<path d="M5 12h14M13 6l6 6-6 6"/>')
I_CROIX = ico('<path d="M6 6l12 12M18 6L6 18"/>')
I_ECLAT = ico('<path d="M12 3.5l1.8 5.2 5.2 1.8-5.2 1.8L12 17.5l-1.8-5.2L5 10.5l5.2-1.8z"/><path d="M18.5 15.5l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7z"/>')


def tuiles(items, cols=3, numeros=False):
    """Cartes à pictogramme : (icône, titre, texte)."""
    t = []
    for k, (i, titre, texte) in enumerate(items):
        num = f'<span class="tu-num">{k + 1:02d}</span>' if numeros else ''
        t.append(f'      <article class="tuile rv" style="--i:{k}"><span class="tu-ico">{i}</span>{num}<h3>{titre}</h3><p>{texte}</p></article>')
    return f'<div class="tuiles t{cols}">\n' + '\n'.join(t) + '\n    </div>'


def route(etapes, arrivee=None, aria=''):
    """Route de jeu : jetons reliés par une ligne qui se remplit au défilement, pion voyageur, drapeau d'arrivée.
    etapes : (icône, étiquette, titre, texte, gain ou None, id ou None)."""
    n = len(etapes) + (1 if arrivee else 0)
    lis = []
    for k, (i, tag, titre, texte, gain, ident) in enumerate(etapes):
        g = f'<p class="rt-gain">{I_COCHE}<span><strong>Vous obtenez :</strong> {gain}</span></p>' if gain else ''
        idattr = f' id="{ident}"' if ident else ''
        lis.append(f'''      <li class="rt-etape rv"{idattr} style="--i:{k}">
        <span class="rt-jeton"><span class="rt-num">{k + 1}</span>{i}</span>
        <div class="rt-carte">
          <p class="rt-tag">{tag}</p>
          <h3>{titre}</h3>
          <p class="rt-texte">{texte}</p>{g}
        </div>
      </li>''')
    if arrivee:
        lis.append(f'      <li class="rt-arrivee rv" style="--i:{len(etapes)}"><span class="rt-jeton">{I_DRAPEAU}<span class="rt-confettis" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i></span></span><strong>{arrivee}</strong></li>')
    lab = f' aria-label="{aria}"' if aria else ''
    return (f'<div class="route-zone" data-route style="--n:{n}">\n    <span class="rt-ligne" aria-hidden="true"></span><span class="rt-pion" aria-hidden="true"></span>\n'
            f'    <ol class="route{" avec-fin" if arrivee else ""}"{lab}>\n' + '\n'.join(lis) + '\n    </ol>\n  </div>')


def parcours(etapes, label):
    """Piste de la dépense au revenu : les étapes s'allument une à une, la dernière (le revenu) en orange."""
    items = []
    for i, e in enumerate(etapes):
        fin = i == len(etapes) - 1
        items.append(f'<li{" class=\"fin\"" if fin else ""} style="--i:{i}"><span class="pi-point" aria-hidden="true">{I_EURO if fin else ""}</span><span class="pi-nom">{e}</span></li>')
    return f'<ol class="piste" aria-label="{label}">' + ''.join(items) + '</ol>'


def chemin_casse(etapes, casse, legende):
    """Mini-parcours ludique : progression orange jusqu'à la cassure, maillon rompu, suite perdue en pointillés.
    casse = index du segment rompu (entre etapes[casse] et etapes[casse + 1]), ou None si rien n'est mesuré."""
    n = len(etapes)
    mesure = casse is not None
    # Le tronçon rompu est plus long que les autres : la cassure respire et saute aux yeux.
    poids = [2.8 if (mesure and k == casse) else 1 for k in range(n - 1)]
    cumul = [0.0]
    for p_ in poids:
        cumul.append(cumul[-1] + p_)
    pos = lambda i: cumul[i] * 100 / cumul[-1]
    b = (pos(casse) + pos(casse + 1)) / 2 if mesure else 50
    bord = ' bord-g' if b < 22 else (' bord-d' if b > 78 else '')
    morceaux = []
    if mesure:
        morceaux.append(f'<span class="rail-ok" style="width:{b:.2f}%"></span>')
        morceaux.append(f'<span class="rail-perdu" style="left:{b:.2f}%"></span>')
    else:
        morceaux.append('<span class="rail-perdu" style="left:0"></span>')
    for i in range(1, n - 1):
        if not mesure and abs(pos(i) - 50) < 14:
            continue  # sous le point d'interrogation central
        etat = 'flou' if not mesure else ('ok' if i <= casse else 'perdu')
        contenu = ICO_COCHE if etat == 'ok' else ('?' if etat == 'flou' else '')
        morceaux.append(f'<span class="jalon {etat}" style="left:{pos(i):.2f}%;--d:{i}">{contenu}</span>')
    morceaux.append(f'<span class="borne depart {"ok" if mesure else "flou"}" style="left:0">{ICO_LOUPE}</span>')
    morceaux.append(f'<span class="borne arrivee {"perdu" if mesure else "flou"}" style="left:100%">{ICO_CLIENT}</span>')
    if mesure:
        morceaux.append(f'<span class="rupture{bord}" style="left:{b:.2f}%"><span class="bulle">Ça casse ici</span><span class="badge">{ICO_RUPTURE}</span></span>')
    else:
        morceaux.append(f'<span class="rupture inconnu" style="left:50%"><span class="bulle">Aucune mesure</span><span class="badge">?</span></span>')
    rail = f'<div class="rail{" sans-mesure" if not mesure else ""}" aria-hidden="true">{"".join(morceaux)}</div>'
    bornes = f'<div class="bornes" aria-hidden="true"><span>{etapes[0]}</span><span>{etapes[-1]}</span></div>'
    return f'<div class="signal">{rail}{bornes}<p class="ou">{legende}</p></div>'


def symptome(titre, texte, etapes, casse, legende):
    return f'''      <article class="symptome">
        {chemin_casse(etapes, casse, legende)}
        <h3>{titre}</h3>
        <p>{texte}</p>
      </article>'''


PAGES = []

CH_A = ['Recherche', 'Annonce', 'Page', 'Demande', 'Devis', 'Client']
CH_N = ['Recherche', 'Demande', 'Visite', 'Devis', 'Contrat']

# ---------------------------------------------------------------- ACCUEIL
FAQ_A = [
    ("Travaillez-vous seulement avec des entreprises de nettoyage ?", "Non. Nous accompagnons les entreprises locales de tous secteurs. La propreté est notre spécialité, parce que notre fondateur dirige lui-même une entreprise de nettoyage."),
    ("Le premier échange est-il payant ?", "Non. Il est offert et dure de 15 à 30 minutes. Il sert à comprendre votre situation et à vous dire franchement si nous pouvons vous aider."),
    ("Qu'est-ce que le diagnostic approfondi ?", "Une prestation distincte : analyse de votre acquisition actuelle, des blocages et des opportunités, puis une feuille de route priorisée. Son contenu et son prix vous sont donnés par écrit avant de commencer."),
    ("Le compte publicitaire m'appartient-il ?", "Oui. Les campagnes sont créées sur votre propre compte, à votre nom, et le budget publicitaire est payé directement par vous à Google. Vous gardez vos accès et vos données."),
    ("Garantissez-vous des résultats ?", "Non. Personne ne peut garantir honnêtement un nombre de clients. Nous nous engageons sur la méthode : préparer, mesurer, corriger une chose à la fois, et vous montrer les résultats tels qu'ils sont."),
    ("Intervenez-vous hors des Vosges ?", "Oui. Nous sommes basés dans les Vosges et nous accompagnons aussi des entreprises ailleurs en France, à distance, lorsque le travail s'y prête."),
]
faq_accueil = '\n'.join(f'      <details{" open" if i == 0 else ""}><summary>{q}</summary><p>{r}</p></details>' for i, (q, r) in enumerate(FAQ_A))
faq_ld_accueil = {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}} for q, r in FAQ_A]}

IT_ETAPES = [(I_LOUPE, "Recherche Google", "ce qui a été tapé"), (I_ANNONCE, "Annonce ou fiche Google", "les clics"), (I_PAGE, "Page dédiée", "les visites"),
             (I_TRI, "Demande, puis tri", "les demandes sérieuses"), (I_DEVIS, "Devis", "les devis émis")]
it_html = '\n'.join(f'        <li style="--i:{k}"><span class="it-pin">{i}</span><span class="it-nom">{n}</span><span class="it-mesure">{m}</span></li>' for k, (i, n, m) in enumerate(IT_ETAPES))
CONTACT = [
    (I_BULLE, '<span class="statut offert">Offert</span>', "Premier échange", "15 à 30 minutes pour comprendre votre situation et vous dire honnêtement si nous pouvons vous aider.", None, None),
    (I_DIAG, '<span class="statut">Prestation distincte</span>', "Diagnostic approfondi", "Si c'est utile : analyse de l'existant, blocages, opportunités et feuille de route. Son contenu et son prix vous sont donnés par écrit, avant de commencer.", None, None),
    (I_COMM, '<span class="statut">Sur proposition</span>', "Accompagnement", "Une proposition séparée : périmètre, honoraires, et budget publicitaire payé directement par vous à Google.", None, None),
]
LEVIERS_A = [
    (I_LOUPE, "Attirer les bonnes recherches", "Des annonces Google ciblées sur ce que vos clients tapent vraiment, dans votre zone d'intervention, complétées par votre fiche Google et votre site."),
    (I_DEMANDE, "Transformer les visites en demandes", "Une page claire pour chaque offre, un message qui répond aux vraies questions, un formulaire simple qui vous dit qui vous contacte et pourquoi."),
    (I_MESURE, "Mesurer ce qui se passe vraiment", "Nous suivons d'où viennent vos demandes, si elles sont sérieuses, et ce qu'elles deviennent. Vous voyez la différence entre un clic, une demande et un client."),
    (I_HAUSSE, "Améliorer selon les résultats", "Nous corrigeons une chose à la fois, quand les résultats le justifient, et nous vous expliquons pourquoi. Votre budget reste sous contrôle."),
]

PAGES.append(page('/', 'ViZiBiLi · Agence d\'acquisition de clients sur Google, Vosges',
    "ViZiBiLi aide les entreprises locales à transformer les recherches Google en demandes sérieuses, et à suivre les résultats jusqu'au contrat signé.",
f'''
<section class="heros-zone">
  <div class="contenu heros">
    <div>
      <p class="repere">Acquisition et croissance locale</p>
      <h1>Votre visibilité sur Google doit servir votre <em>développement commercial.</em></h1>
      <p class="sous-titre">ViZiBiLi accompagne les entreprises dans la construction de parcours d'acquisition mesurables : attirer les bonnes recherches, transformer les visites en demandes sérieuses et mieux suivre les résultats commerciaux.</p>
      <div class="actions">
        <a href="/premier-echange/" class="btn btn-plein">Demander un premier échange</a>
        <a href="/methode/" class="btn btn-ligne">Découvrir notre méthode</a>
      </div>
      <p class="reassurance">Pour les entreprises locales de tous secteurs, partout en France. Notre spécialité : les entreprises de nettoyage et de services d'entretien.</p>
    </div>
    <div class="itineraire" role="img" aria-label="Le chemin que nous suivons : recherche Google, annonce ou fiche Google, page dédiée, demande puis tri, devis, client signé. Chaque étape est mesurée.">
      <p class="it-titre">Le chemin que nous suivons</p>
      <div class="it-piste">
      <span class="it-voyageur" aria-hidden="true"></span>
      <ol class="it-etapes" aria-hidden="true">
{it_html}
        <li class="it-fin" style="--i:5"><span class="it-pin">{I_EURO}</span><span class="it-nom">Client signé</span><span class="it-mesure">ce qu'il rapporte</span></li>
      </ol>
      </div>
      <p class="it-legende">Chaque étape se mesure. C'est là que se joue la différence.</p>
    </div>
  </div>
</section>

<section class="fond-chaud">
  <div class="contenu">
    <div class="titre-section">
      <h2>Être visible ne suffit pas. Encore faut-il que cette visibilité devienne des clients.</h2>
      <p>Beaucoup d'entreprises sont présentes sur Google sans savoir ce que cela leur rapporte. Vous vous reconnaissez peut-être dans l'une de ces situations :</p>
    </div>
    <div class="symptomes">
{symptome("Des demandes hors sujet", "Des demandes qui ne correspondent pas à ce que vous vendez.", CH_A, 0, "Ça casse dès la recherche ciblée")}
{symptome("Une publicité sans résultat clair", "Une publicité qui dépense chaque mois, sans demande sérieuse au bout.", CH_A, 1, "Ça casse entre l'annonce et la demande")}
{symptome("Des visites sans demandes", "Des visites sur votre site, mais très peu de demandes.", CH_A, 2, "Ça casse entre la page et la demande")}
{symptome("Des formulaires sans suite", "Des formulaires reçus, puis jamais transformés en devis.", CH_A, 3, "Ça casse entre la demande et le devis")}
{symptome("Aucun lien avec vos encaissements", "Aucun lien clair entre ce que vous dépensez et ce que vous encaissez.", CH_A, 4, "Ça casse entre le devis et le client")}
{symptome("Un coût inconnu", "Aucune idée de ce que vous coûte un nouveau client.", CH_A, None, "Rien n'est mesuré, d'un bout à l'autre")}
    </div>
    <div class="constat rv">
      <span class="constat-ico" aria-hidden="true">{I_MAILLON}</span>
      <p>Le problème n'est presque jamais un seul outil. C'est le chemin entier, de la recherche jusqu'à la signature, que personne ne regarde.</p>
      <a href="/methode/" class="btn btn-plein">Découvrir notre méthode</a>
    </div>
  </div>
</section>

<section>
  <div class="contenu">
    <div class="titre-section">
      <h2>Une méthode structurée, de la dépense jusqu'au revenu signé.</h2>
      <p>Un clic n'est jamais l'objectif. Nous suivons chaque étape jusqu'à ce qu'elle rapporte, pour savoir où les clients se perdent et corriger au bon endroit.</p>
    </div>
    {parcours(["Dépense", "Clic", "Demande", "Prospect qualifié", "Rendez-vous ou visite", "Devis", "Contrat signé", "Revenu"], "De la dépense au revenu")}
    <p class="note">Le dispositif s'adapte aux outils que vous utilisez déjà. Nous ne mettons en place que ce qui est utile à votre situation. <a href="/methode/">Voir la méthode en 8 étapes</a></p>
  </div>
</section>

<section class="fond-chaud">
  <div class="contenu">
    <div class="titre-section"><h2>Quatre leviers, un seul objectif : des clients qui vous correspondent.</h2></div>
    {tuiles(LEVIERS_A, 4, numeros=True)}
  </div>
</section>

<section>
  <div class="contenu bloc-encre encre brillant">
    <div class="disposition">
      <div>
        <p class="repere">Notre spécialité</p>
        <h2>Une connaissance de terrain particulière : les entreprises de nettoyage.</h2>
        <p>Notre fondateur dirige lui-même une entreprise de nettoyage. Les contrats d'entretien de bureaux, le ménage à domicile, le lavage de vitres, les demandes ponctuelles qui ne débouchent sur rien, les devis à relancer : nous connaissons ces réalités de l'intérieur.</p>
        <p style="margin-top:12px">C'est sur ce terrain que notre méthode est née et qu'elle continue de s'améliorer. Si vous dirigez une entreprise de propreté, nous parlons le même langage.</p>
      </div>
      <div class="terrain" aria-hidden="true">
        <span style="--i:0">{I_BUREAU}<em>Bureaux</em></span><span style="--i:1">{I_MAISON}<em>Domicile</em></span><span style="--i:2">{I_VITRE}<em>Vitres</em></span><span style="--i:3">{I_DEVIS}<em>Devis</em></span>
      </div>
    </div>
    <a href="/entreprises-de-nettoyage/" class="btn btn-plein" style="margin-top:32px">Découvrir notre approche pour les entreprises de nettoyage</a>
  </div>
</section>

<section class="fond-chaud">
  <div class="contenu">
    <div class="titre-section"><h2>Des résultats racontés honnêtement.</h2></div>
    <div class="preuves">
      <div class="preuve rv" style="--i:0">
        <span class="etiquette">Visibilité locale · missions terminées</span>
        <div class="mini-clients" aria-hidden="true"><span>{I_NETTOYAGE}</span><span>{I_MAISON}</span><span>{I_MAISON}</span><span>{I_CADEAU}</span></div>
        <p>Quatre entreprises accompagnées sur leur présence locale, dont celle de notre fondateur : une entreprise de nettoyage, deux gîtes et une boutique de cadeaux, dans les Vosges. <a href="/fiche-google-vosges/">Notre travail sur les fiches Google</a></p>
        <p>Leur point commun : une présence locale remise en ordre, et des clients qui repartent propriétaires de tout ce qui a été construit.</p>
        <a href="/cas-clients/" class="btn btn-ligne">Voir les cas clients</a>
      </div>
      <div class="preuve en-cours rv" style="--i:1">
        <span class="etiquette en-cours">Campagnes Google · étude en cours</span>
        <div class="en-cours-barre" aria-hidden="true"><span></span></div>
        <p>Depuis septembre 2026, nous testons notre méthode de campagnes Google sur l'entreprise de nettoyage de notre fondateur. Nous publierons les résultats quand ils auront été mesurés sur une période suffisante, avec leurs dates et leurs limites. <strong>Pas avant.</strong></p>
      </div>
    </div>
  </div>
</section>

<section>
  <div class="contenu">
    <div class="titre-section">
      <h2>Comment se passe le premier contact.</h2>
      <p>Trois étapes distinctes, pour que vous sachiez toujours ce qui est offert, ce qui est payant, et ce qui vous engage.</p>
    </div>
    {route(CONTACT, aria="Les trois étapes du premier contact")}
    <div class="actions" style="margin-top:28px"><a href="/premier-echange/" class="btn btn-plein">Demander un premier échange</a><a href="/premier-echange/#diagnostic" class="btn btn-ligne">Le diagnostic en détail</a></div>
  </div>
</section>

<section class="fond-chaud">
  <div class="etroit">
    <h2>Questions fréquentes</h2>
    <div class="faq">
{faq_accueil}
    </div>
  </div>
</section>
{bande("Votre façon de trouver des clients vous apporte-t-elle les bons ?", "Faisons le point sur votre activité, vos objectifs et les leviers vraiment adaptés à votre situation.", "Demander un premier échange")}
''', actif=None, jsonld=[faq_ld_accueil]))

# ---------------------------------------------------------------- NETTOYAGE
FAQ_N = [
    ("Faut-il forcément faire de la publicité payante ?", "Non. Selon votre situation, votre fiche Google et votre site peuvent suffire, ou les annonces peuvent compléter ce que vous avez déjà. Le premier échange, puis le diagnostic si besoin, servent à le déterminer."),
    ("Le compte publicitaire m'appartient-il ?", "Oui. Les campagnes sont créées sur votre propre compte, à votre nom. Vous gardez l'accès et les données, quoi qu'il arrive."),
    ("Je travaille surtout avec des particuliers. Est-ce adapté ?", "Oui. Ménage à domicile et vitres chez les particuliers demandent une approche différente des contrats professionnels. Nous les séparons dès que leur valeur ou leur clientèle diffère."),
    ("Intervenez-vous hors des Vosges ?", "Oui. Nous accompagnons les entreprises de nettoyage partout en France, à distance."),
    ("Comment savoir si c'est rentable pour moi ?", "C'est l'objet du suivi : relier ce que vous dépensez aux devis signés. Tant que ce lien n'est pas mesuré, personne ne peut honnêtement vous répondre."),
]
faq_html = '\n'.join(f'      <details{" open" if i == 0 else ""}><summary>{q}</summary><p>{r}</p></details>' for i, (q, r) in enumerate(FAQ_N))
faq_ld = {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}} for q, r in FAQ_N]}
svc_n = {"@type": "Service", "name": "Acquisition de clients pour entreprises de nettoyage", "provider": {"@id": SITE + "/#organisation"},
         "areaServed": {"@type": "Country", "name": "France"}, "serviceType": "Acquisition de clients sur Google"}
SUJETS_N = [
    (I_BUREAU, "Entretien de bureaux et locaux professionnels", "Cibler les entreprises qui cherchent un prestataire régulier, et trier les demandes selon la taille des locaux et la fréquence souhaitée."),
    (I_VITRE, "Nettoyage de vitres", "Viser les particuliers comme les commerces avec vitrine, sur des recherches précises, pour des demandes faciles à chiffrer."),
    (I_MAISON, "Ménage à domicile", "Toucher les particuliers de votre zone au bon moment, et distinguer les demandes régulières des demandes ponctuelles."),
    (I_RECURRENT, "Acquisition de contrats récurrents", "Faire passer en priorité ce qui construit votre chiffre d'affaires dans la durée, plutôt que le volume de demandes."),
    (I_DEVIS, "Gestion des demandes et des devis", "Répondre vite, qualifier avant de se déplacer, relancer les devis : c'est souvent là que se perdent les contrats déjà gagnés à moitié."),
]
MOIS = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
mois_html = ''.join(f'<span style="--i:{k}">{m}</span>' for k, m in enumerate(MOIS))
TERRAIN_N = [(I_DEVIS, "Les devis à chiffrer"), (I_FICHE, "Les visites sur place"), (I_RECURRENT, "Les clients à fidéliser"), (I_HORLOGE, "Les demandes qui font perdre du temps")]
terrain_n = ''.join(f'<li class="rv" style="--i:{k}"><span>{i}</span>{t}</li>' for k, (i, t) in enumerate(TERRAIN_N))

PAGES.append(page('/entreprises-de-nettoyage/', 'Trouver des clients pour une entreprise de nettoyage · ViZiBiLi',
    "Bureaux, ménage à domicile, vitres : nous aidons les entreprises de nettoyage à obtenir des demandes sérieuses et à savoir ce qu'elles leur rapportent.",
f'''
<section class="heros-zone">
  <div class="contenu heros">
    <div>
      <p class="repere">Pour les entreprises de nettoyage et de propreté</p>
      <h1>Développez votre <em>entreprise de nettoyage</em> avec des demandes que vous pouvez <em>mesurer.</em></h1>
      <p class="sous-titre">Plus de contrats qui vous correspondent, moins de demandes inutiles, et une vision claire de ce que chaque nouveau client vous coûte et vous rapporte.</p>
      <div class="actions"><a href="/premier-echange/?secteur=proprete" class="btn btn-plein">Parlons de votre entreprise de nettoyage</a><a href="#pourquoi-la-signature" class="btn btn-ligne">Pourquoi suivre jusqu'à la signature</a></div>
      <p class="reassurance">Partout en France, à distance. Premier échange offert.</p>
    </div>
    <div class="fil-notif" aria-hidden="true">
      <div class="notif" style="--i:0"><span class="nt-ico">{I_LOUPE}</span><div><small>Une recherche</small><strong>« entreprise de nettoyage de bureaux »</strong></div></div>
      <div class="notif" style="--i:1"><span class="nt-ico">{I_DEMANDE}</span><div><small>Une demande sérieuse</small><strong>Entretien de bureaux, chaque semaine</strong></div></div>
      <div class="notif nt-fin" style="--i:2"><span class="nt-ico">{I_COCHE}</span><div><small>Un contrat signé</small><strong>Récurrent, suivi jusqu'au revenu</strong></div></div>
    </div>
  </div>
</section>

<section class="fond-chaud">
  <div class="contenu">
    <div class="titre-section"><h2>Vous connaissez sûrement l'une de ces situations.</h2></div>
    <div class="symptomes">
{symptome("Tout repose sur le bouche-à-oreille", "Votre activité dépend presque entièrement du bouche-à-oreille.", CH_N, 0, "Aucune entrée depuis Google")}
{symptome("Des demandes ponctuelles", "Vous cherchez des contrats d'entretien réguliers, mais vous recevez surtout des demandes ponctuelles.", CH_N, 0, "Ça casse dès la recherche ciblée")}
{symptome("Des demandes hors zone ou hors métier", "Des demandes arrivent pour des prestations que vous ne faites pas, ou hors de votre zone.", CH_N, 1, "Ça casse au tri des demandes")}
{symptome("Petits ménages ou bureaux ?", "Dix demandes de petits ménages ne valent pas un contrat de bureaux, mais rien ne vous permet de faire la différence avant de vous déplacer.", CH_N, 1, "Ça casse avant la visite sur place")}
{symptome("Des devis sans réponse", "Des prospects demandent un devis, puis ne répondent plus.", CH_N, 3, "Ça casse entre le devis et le contrat")}
{symptome("Une visibilité sans retour connu", "Vous payez pour être visible sans savoir ce que cela vous rapporte réellement.", CH_N, None, "Rien n'est mesuré, d'un bout à l'autre")}
    </div>
    <div class="constat rv">
      <span class="constat-ico" aria-hidden="true">{I_MAILLON}</span>
      <p>Ce ne sont pas des fatalités du métier. Ce sont des signaux que le chemin entre la recherche et le contrat n'est pas piloté.</p>
      <a href="/premier-echange/?secteur=proprete" class="btn btn-plein">Parlons de votre entreprise de nettoyage</a>
    </div>
  </div>
</section>

<section>
  <div class="contenu deux-temps">
    <div class="titre-section">
      <h2>Notre méthode est née dans une entreprise de nettoyage.</h2>
      <p>Notre fondateur dirige une entreprise de nettoyage dans les Vosges : bureaux, commerces, vitres, ménage à domicile, grands ménages. Il vit chaque semaine ce que vous vivez : les devis à chiffrer, les visites sur place, les clients à fidéliser, les demandes qui font perdre du temps.</p>
      <p style="margin-top:12px">C'est là que notre méthode a été construite, testée et corrigée. Nous savons qu'une demande n'a pas la même valeur selon la prestation, la fréquence et la distance, et que votre temps est votre ressource la plus rare.</p>
    </div>
    <div class="carnet" aria-hidden="true">
      <p class="carnet-titre">{I_NETTOYAGE}La semaine d'un dirigeant</p>
      <ul>{terrain_n}</ul>
    </div>
  </div>
</section>

<section class="fond-chaud">
  <div class="contenu">
    <div class="titre-section"><h2>Cinq sujets, cinq approches différentes.</h2><p>Chaque activité a ses recherches, ses clients et sa valeur. Nous les séparons quand leur valeur diffère et que le volume de recherches le permet, sans éparpiller un petit budget.</p></div>
    {tuiles(SUJETS_N, 3)}
  </div>
</section>

<section id="pourquoi-la-signature">
  <div class="contenu">
    <div class="titre-section">
      <h2>Pourquoi le suivi jusqu'à la signature compte autant dans la propreté.</h2>
      <p>Dans votre métier, deux demandes peuvent avoir une valeur sans commune mesure. Les compter de la même façon fausse toutes les décisions.</p>
    </div>
    <div class="comparatif">
      <div class="cmp-col rv" style="--i:0"><p class="cmp-titre">Une prestation ponctuelle</p><p class="cmp-valeur">1 facture</p><div class="cmp-factures" aria-hidden="true"><span class="plein" style="--i:0">{I_DEVIS}</span></div><p>Un grand ménage, un lavage de vitres unique. Utile, mais terminé une fois réalisé.</p></div>
      <div class="cmp-col cmp-fort rv" style="--i:1"><p class="cmp-titre">Un contrat récurrent</p><p class="cmp-valeur">12 factures par an</p><div class="cmp-mois" aria-hidden="true">{mois_html}</div><p>L'entretien mensuel de bureaux. Il se renouvelle, et sa valeur se compte sur l'année.</p></div>
    </div>
    <p class="exemple-fictif rv"><strong>Exemple fictif, pour illustrer :</strong> un grand ménage facturé 300 € et un contrat de bureaux à 300 € par mois arrivent tous deux comme « une demande ». Sur un an, le second représente 3 600 €. Un suivi qui s'arrête au nombre de demandes ne voit pas cette différence.</p>
    <p class="conclusion">C'est pourquoi nous évaluons chaque source de clients sur la valeur des contrats réellement signés, et non sur le nombre de clics ou de demandes.</p>
    {parcours(["Dépense", "Clic", "Demande", "Prospect qualifié", "Visite sur place", "Devis", "Contrat signé", "Revenu"], "De la dépense au revenu")}
    <p class="note">Le suivi s'appuie sur les outils que vous utilisez déjà. Nous ne vous imposons pas de logiciel.</p>
  </div>
</section>

<section>
  <div class="contenu bloc-encre">
    <h2>Une méthode en amélioration continue, présentée telle qu'elle est.</h2>
    <div class="disposition" style="align-items:flex-start;margin-top:12px">
      <div>
        <p>Notre méthode de campagnes Google est actuellement testée sur l'entreprise de nettoyage de notre fondateur, depuis septembre 2026. Nous préférons vous le dire clairement : nous ne vous montrerons pas de chiffres tant qu'ils n'auront pas été mesurés sur une période suffisante.</p>
        <p style="margin-top:12px">Ce que nous pouvons vous promettre, c'est la méthode : préparer avant de lancer, mesurer avant de décider, corriger une chose à la fois, et vous montrer les résultats tels qu'ils sont.</p>
      </div>
      <div>
        <p><strong>Ce que nous ne promettrons jamais :</strong></p>
        <ul class="liste-refus"><li><span>Un nombre garanti de clients</span></li><li><span>Un délai de signature</span></li><li><span>Une rentabilité garantie</span></li></ul>
      </div>
    </div>
  </div>
</section>

<section style="padding-top:0">
  <div class="etroit">
    <h2>Vos questions</h2>
    <div class="faq">
{faq_html}
    </div>
    <p class="note">À lire aussi : <a href="/ressources/trouver-clients-entreprise-de-nettoyage/">comment trouver des clients pour une entreprise de nettoyage</a>, <a href="/ressources/contrats-entretien-bureaux/">comment obtenir des contrats d'entretien de bureaux</a> et <a href="/ressources/publicite-google-entreprise-de-nettoyage/">publicité Google : ce qu'il faut vérifier</a>.</p>
  </div>
</section>
{bande("Parlons de votre entreprise de nettoyage.", "Dites-nous quelles prestations vous faites et quels clients vous cherchez. Le premier échange est offert : nous vous dirons honnêtement ce qui peut être amélioré, et par où commencer.", "Demander un premier échange", "/premier-echange/?secteur=proprete")}
''', actif='/entreprises-de-nettoyage/', jsonld=[svc_n, faq_ld]))

# ---------------------------------------------------------------- MÉTHODE
ETAPES = [
    ("Comprendre l'activité et les objectifs", "Vos prestations, vos clients idéaux, votre zone, votre capacité et ce que vous voulez avoir obtenu dans six mois.", "un objectif commercial clair, écrit avec vous."),
    ("Diagnostiquer l'acquisition actuelle", "D'où viennent vos clients aujourd'hui, ce que vous dépensez pour être visible, ce que deviennent vos demandes et vos devis.", "une lecture honnête de ce qui marche, de ce qui bloque et de ce qui n'est pas mesuré."),
    ("Définir une feuille de route adaptée", "Les actions classées par ordre d'importance, avec ce qui est visé et, noir sur blanc, ce qui ne l'est pas.", "un plan écrit, adapté à votre entreprise et à vos moyens."),
    ("Préparer les outils et les mesures", "Avant de dépenser le moindre euro : la page qui accueillera vos futurs clients, le formulaire, et le suivi qui indiquera d'où viennent vos demandes.", "un parcours prêt et une définition claire de ce qui compte comme résultat."),
    ("Lancer lorsque les contrôles sont validés", "Budget plafonné, zones, recherches exclues, mesure vérifiée : rien ne part tant que la liste de contrôle n'est pas complète et que vous n'avez pas donné votre accord écrit.", "une diffusion sous contrôle, sur votre propre compte."),
    ("Observer les premiers résultats", "Les recherches réellement tapées, les dépenses, les demandes reçues et leur sérieux, dès les premiers jours puis à intervalles réguliers.", "des points datés, lisibles, sans jargon."),
    ("Adapter la stratégie", "Une seule correction à la fois, quand les résultats le justifient. Changer tout en même temps empêche de savoir ce qui a marché.", "des décisions expliquées, jamais des réglages au hasard."),
    ("Suivre les résultats jusqu'à leur valeur commerciale", "Des demandes aux rendez-vous, des devis aux contrats signés, et ce qu'ils rapportent réellement.", "la réponse la plus juste que permettent vos données à la seule question qui compte : ce que vous coûte et vous rapporte un nouveau client. Les limites de la mesure vous sont dites clairement."),
]
PHASES = ['Comprendre', 'Comprendre', 'Préparer', 'Préparer', 'Lancer', 'Lancer', 'Améliorer', 'Améliorer']
ICONE_OK = '<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true"><circle cx="10" cy="10" r="9" fill="currentColor"/><path d="M5.8 10.3l2.7 2.7 5.7-5.9" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
frise = '\n'.join(
    f'''      <li class="fe">
        <span class="fe-point" aria-hidden="true">{i:02d}</span>
        <article class="fe-carte">
          <p class="fe-phase">Étape {i} · {PHASES[i-1]}</p>
          <h3>{t}</h3>
          <p class="fe-texte">{d}</p>
          <div class="fe-obtenu"><p class="fe-obtenu-titre">{ICONE_OK}Ce que vous obtenez</p><p>{o[0].upper() + o[1:]}</p></div>
        </article>
      </li>''' for i, (t, d, o) in enumerate(ETAPES, 1))
legende_phases = ''.join(f'<li><span>{n}</span> {p}<small>Étapes {a} et {b}</small></li>' for n, (p, a, b) in enumerate([('Comprendre', 1, 2), ('Préparer', 3, 4), ('Lancer', 5, 6), ('Améliorer', 7, 8)], 1))
PAGES.append(page('/methode/', 'Notre méthode pour trouver des clients sur Google · ViZiBiLi',
    "Huit étapes, de votre activité jusqu'à la valeur des contrats signés : une méthode qui mesure avant de promettre et s'adapte à chaque entreprise.",
f'''
<section class="heros-zone">
  <div class="contenu heros">
    <div>
      <p class="repere">Notre méthode</p>
      <h1>La stratégie doit <em>s'adapter à l'entreprise.</em> Pas l'entreprise à une recette marketing.</h1>
      <p class="sous-titre">Nous suivons une méthode en huit étapes, qui part de votre réalité, ne lance rien sans contrôle et ne change rien sans raison mesurée.</p>
      <div class="actions"><a href="/premier-echange/" class="btn btn-plein">Demander un premier échange</a><a href="#huit-etapes" class="btn btn-ligne">Voir les 8 étapes</a></div>
    </div>
    <div class="orbite" aria-hidden="true">
      <span class="ob-anneau"></span>
      <span class="ob-centre">8<small>étapes</small></span>
      <span class="ob-temps t1">{I_OEIL}<em>Comprendre</em></span><span class="ob-temps t2">{I_CONSTR}<em>Préparer</em></span><span class="ob-temps t3">{I_ANNONCE}<em>Lancer</em></span><span class="ob-temps t4">{I_HAUSSE}<em>Améliorer</em></span>
    </div>
  </div>
</section>

<section class="fond-chaud" id="huit-etapes">
  <div class="contenu">
    <div class="titre-section"><h2>Huit étapes, de votre activité jusqu'à la valeur des contrats signés.</h2><p>Quatre temps, toujours dans le même ordre. Chaque étape vous laisse quelque chose de concret entre les mains.</p></div>
    <ol class="fe-phases" aria-label="Les quatre temps de la méthode">{legende_phases}</ol>
    <ol class="frise-etapes">
{frise}
    </ol>
  </div>
</section>

<section>
  <div class="contenu bloc-encre">
    <h2>Ce que nous ne ferons pas.</h2>
    <ul class="liste-refus" style="margin-top:20px">
      <li><span><strong>Vous promettre un nombre de clients.</strong> Personne ne peut le garantir honnêtement avant d'avoir mesuré.</span></li>
      <li><span><strong>Vous montrer des chiffres flatteurs qui ne veulent rien dire.</strong> Un clic n'est pas un client. Nous vous parlons de demandes, de devis et de contrats.</span></li>
      <li><span><strong>Créer vos campagnes sur notre compte.</strong> Tout est à votre nom, vous gardez l'accès quoi qu'il arrive.</span></li>
      <li><span><strong>Annoncer un résultat avant de l'avoir mesuré.</strong> Y compris les nôtres : notre propre test est en cours depuis septembre 2026, et nous publierons ses résultats seulement quand ils seront solides.</span></li>
      <li><span><strong>Tout changer d'un coup.</strong> Une modification à la fois, pour savoir ce qui fonctionne vraiment.</span></li>
    </ul>
  </div>
</section>

<section class="fond-chaud">
  <div class="contenu">
    <div class="titre-section">
      <h2>Une méthode née sur le terrain, pas dans un bureau.</h2>
      <p>Notre fondateur dirige une entreprise de nettoyage. C'est d'abord pour elle que cette méthode a été construite : trouver des clients sérieux, sans gaspiller ni temps ni budget, et savoir enfin ce que chaque action rapporte.</p>
      <p style="margin-top:12px">Elle continue de s'améliorer à chaque mesure. Quand une étape ne tient pas ses promesses, nous la corrigeons, et nous le disons.</p>
    </div>
    <a href="/entreprises-de-nettoyage/" class="btn btn-ligne">Découvrir notre approche pour les entreprises de nettoyage</a>
  </div>
</section>
{bande("Voyons ensemble par quelle étape commencer.", "Chaque situation a sa priorité. Parfois c'est la publicité, parfois la fiche Google, parfois simplement la façon de répondre aux demandes.", "Demander un premier échange")}
''', actif='/methode/'))

# ---------------------------------------------------------------- OFFRE
LEVIERS = [
    (I_ANNONCE, "Les annonces Google", "Pour apparaître au moment précis où quelqu'un cherche votre service, dans votre zone. C'est le moyen d'être visible le plus vite, à condition d'être bien préparé et bien suivi. Un clic ne prouve rien : seules les demandes et les contrats comptent."),
    (I_PAGE, "Une page dédiée à votre offre", "Pour que la personne qui clique trouve immédiatement ce qu'elle cherche, et puisse vous écrire facilement."),
    (I_SUIVI, "Le suivi des demandes", "Pour savoir d'où viennent vos demandes, si elles sont sérieuses et ce qu'elles deviennent. Sans ce suivi, personne ne peut dire si la publicité est rentable."),
    (I_FICHE, "Votre fiche Google et votre site", "Ils restent des appuis essentiels, et nous les améliorons quand c'est nécessaire. Mais ils ne sont qu'une partie du chemin. <a href=\"/fiche-google-vosges/\">La fiche Google, dans le détail</a>"),
]
MODS = [
    (I_DIAG, "Étape 1", "Diagnostic d'acquisition", "Nous analysons votre situation : vos clients actuels, vos canaux, vos dépenses et ce qui bloque. Vous repartez avec des priorités claires, même si vous décidez de continuer seul. Prestation distincte du premier échange offert, au prix communiqué par écrit avant de commencer.", "Vos priorités, par écrit", None),
    (I_CONSTR, "Étape 2", "Construction du parcours", "Nous préparons et lançons ce qui manque : annonces Google, page dédiée, suivi des demandes, et si besoin votre fiche Google ou votre site.", "Un parcours prêt à recevoir des demandes", None),
    (I_PILOT, "Étape 3", "Pilotage et amélioration", "Nous surveillons les dépenses, trions les demandes avec vous et corrigeons une chose à la fois. Vous recevez un point régulier, clair et honnête.", "Un point régulier, clair et honnête", None),
    (I_COMM, "Étape 4", "Suivi commercial", "Nous relions les demandes à vos devis et à vos contrats signés, avec les outils que vous utilisez déjà. C'est là que vous voyez, autant que vos données le permettent, ce que vous coûte et vous rapporte un nouveau client.", "Vos demandes reliées à vos contrats", None),
]
leviers_html = '\n'.join(
    f'''      <article class="of-levier rv" style="--i:{k}">
        <span class="tu-ico">{i}</span>
        <h3>{t}</h3>
        <p>{d}</p>
        {f'<span class="of-lien" aria-hidden="true">{I_MAILLON}</span>' if k < len(LEVIERS) - 1 else ''}
      </article>''' for k, (i, t, d) in enumerate(LEVIERS))
PROPRIETE = ["Compte publicitaire", "Page dédiée", "Site", "Fiche Google", "Données de suivi"]
propriete_html = ''.join(f'<li class="rv" style="--i:{k}">{I_CLE}<span>{p}</span></li>' for k, p in enumerate(PROPRIETE))
svc_o = [{"@type": "Service", "name": t, "description": d, "provider": {"@id": SITE + "/#organisation"}} for _, _, t, d, _, _ in MODS]
SENTIER = "M40 40 C 160 40, 260 60, 240 120 S 60 150, 70 210 S 200 270, 262 262"
PAGES.append(page('/offre/', 'Notre accompagnement pour trouver des clients · ViZiBiLi',
    "Annonces Google, page dédiée, suivi des demandes jusqu'au devis signé : un accompagnement en quatre étapes, adapté à votre entreprise, partout en France.",
f'''
<section class="heros-zone">
  <div class="contenu heros">
    <div>
      <p class="repere">Notre accompagnement</p>
      <h1>Un accompagnement construit autour d'un seul objectif : des <em>clients qui vous correspondent.</em></h1>
      <p class="sous-titre">Nous ne vendons pas un pack identique pour tous. Nous assemblons ce dont votre entreprise a besoin, dans le bon ordre, et nous mesurons ce que cela vous rapporte.</p>
      <div class="actions"><a href="/premier-echange/" class="btn btn-plein">Demander un premier échange</a><a href="#etapes" class="btn btn-ligne">Voir les 4 étapes</a></div>
    </div>
    <div class="of-apercu" aria-hidden="true">
      <svg class="of-sentier" viewBox="0 0 300 300"><path class="fond" d="{SENTIER}"/><path class="trace" pathLength="1" d="{SENTIER}"/><circle class="bille" r="7"><animateMotion dur="5s" begin="1.6s" repeatCount="indefinite" path="{SENTIER}" keyPoints="0;1" keyTimes="0;1" calcMode="linear"/></circle></svg>
      <span class="of-pion p1" style="--i:0">{I_DIAG}</span><span class="of-pion p2" style="--i:1">{I_CONSTR}</span><span class="of-pion p3" style="--i:2">{I_PILOT}</span><span class="of-pion p4" style="--i:3">{I_COMM}</span><span class="of-pion fin" style="--i:4">{I_DRAPEAU}</span>
    </div>
  </div>
</section>

<section class="fond-chaud">
  <div class="contenu">
    <div class="titre-section"><h2>Les leviers, et la place de chacun.</h2><p>Chaque levier est un maillon. Seul, il ne fait pas un client ; reliés dans le bon ordre, ils forment une chaîne solide.</p></div>
    <div class="of-chaine">
{leviers_html}
    </div>
  </div>
</section>

<section id="etapes">
  <div class="contenu">
    <div class="titre-section"><h2>Quatre étapes, à votre rythme.</h2><p>Vous avancez d'une étape à l'autre quand la précédente est en place. Vous pouvez vous arrêter après chacune.</p></div>
    {route(MODS, arrivee="Des clients qui vous correspondent", aria="Les quatre étapes de l'accompagnement")}
    <a href="/methode/" class="lien-suite">En savoir plus sur notre méthode</a>
  </div>
</section>

<section class="fond-chaud">
  <div class="contenu">
    <div class="titre-section"><h2>Ce que vous payez, et à qui.</h2></div>
    <div class="of-flux">
      <div class="of-noeud of-vous rv">{I_VOUS}<strong>Vous</strong></div>
      <div class="of-voies">
        <div class="of-voie rv" style="--i:1">
          <span class="of-fleche" aria-hidden="true"></span>
          <div class="of-destination"><span class="tu-ico">{I_LOUPE}</span><div><strong>Le budget publicitaire, à Google</strong><p>Payé directement par vous à Google, sur votre propre compte. Il ne passe jamais par nous, et vous le voyez en temps réel.</p></div></div>
        </div>
        <div class="of-voie rv" style="--i:2">
          <span class="of-fleche" aria-hidden="true"></span>
          <div class="of-destination"><span class="tu-ico of-ico-vz">{LOGO_MARK.replace('class="logo-mark" ', '')}</span><div><strong>Notre accompagnement, à ViZiBiLi</strong><p>Facturé séparément. Son prix dépend de votre situation et des étapes retenues : il vous est donné par écrit, avant de commencer, à l'issue du diagnostic.</p></div></div>
        </div>
      </div>
    </div>
    <p class="of-promesse rv" style="--i:3"><span>Pas de frais cachés</span><span>Pas de pourcentage prélevé sur votre budget publicitaire</span></p>
  </div>
</section>

<section>
  <div class="contenu of-proprio">
    <div class="rv">
      <h2>Tout ce que nous construisons <em>vous appartient.</em></h2>
      <p class="chapo" style="margin-top:16px">Tout est à votre nom dès le premier jour. Si vous décidez d'arrêter, vous repartez avec l'ensemble, prêt à fonctionner.</p>
    </div>
    <ul class="of-cles">{propriete_html}</ul>
  </div>
</section>

<section class="fond-chaud">
  <div class="contenu">
    <div class="titre-section"><h2>Pour qui nous travaillons.</h2></div>
    <div class="grille-2">
      <div class="of-cible rv" style="--i:0"><span class="of-badge">Notre spécialité</span><span class="tu-ico">{I_NETTOYAGE}</span><strong>Les entreprises de nettoyage et de propreté</strong><p>Partout en France, à distance. C'est notre spécialité. <a href="/entreprises-de-nettoyage/">Notre approche pour les entreprises de nettoyage</a></p></div>
      <div class="of-cible rv" style="--i:1"><span class="tu-ico">{I_BOUTIQUE}</span><strong>Les entreprises locales de tous secteurs</strong><p>Artisans, commerçants, indépendants, professions libérales et services, partout en France à distance, et sur place dans les Vosges. Pour celles qui veulent des demandes sérieuses plutôt que de simples visites.</p></div>
    </div>
  </div>
</section>
{bande("Commençons par un premier échange.", "Offert, de 15 à 30 minutes, pour savoir si nous pouvons vraiment vous aider.", "Demander un premier échange")}
''', actif='/offre/', jsonld=svc_o))

# ---------------------------------------------------------------- CAS CLIENTS
def cas(ancre, icone, etiq, nom, lieu, depart, fait, change, suite='', site=None):
    return f'''
    <article class="cas rv" id="{ancre}">
      <div class="cas-tete"><span class="tu-ico">{icone}</span><div><span class="etiquette">{etiq}</span><h2>{nom}</h2><p class="lieu">{lieu}</p></div></div>
      <ol class="cas-fil">
        <li><span class="cf-ico">{I_DRAPEAU}</span><h3>Point de départ</h3><p>{depart}</p></li>
        <li><span class="cf-ico">{I_CONSTR}</span><h3>Ce que nous avons fait</h3><p>{fait}</p></li>
        <li class="cf-fin"><span class="cf-ico">{I_HAUSSE}</span><h3>Ce qui a changé</h3><p>{change}</p></li>
      </ol>{suite}{f'<a class="lire voir-site" href="{site}" target="_blank" rel="noopener" aria-label="Voir le site : {nom} (nouvel onglet)">Voir le site{I_FLECHE}</a>' if site else ''}
    </article>'''

# Témoignages publiés : diffusion autorisée par les clients (fondateur, 16/10/2026). Orthographe corrigée à la marge, sans changer le sens.
TEMOIN = '\n      <blockquote class="temoin"><span class="guillemet" aria-hidden="true">“</span><p>{q}</p><cite>{a}</cite></blockquote>'
CAS_LISTE = [("limpid", I_NETTOYAGE, "Limpid"), ("un-cadeau-une-histoire", I_CADEAU, "Un Cadeau Une Histoire"), ("gite-chez-paul", I_MAISON, "Gîte Chez Paul"), ("gite-de-la-marie", I_MAISON, "Gîte de la Marie")]
sommaire_cas = ''.join(f'<a href="#{a}" class="rv" style="--i:{k}"><span>{i}</span>{n}</a>' for k, (a, i, n) in enumerate(CAS_LISTE))
PAGES.append(page('/cas-clients/', 'Cas clients dans les Vosges, racontés honnêtement · ViZiBiLi',
    "Quatre entreprises accompagnées, dont celle de notre fondateur : ce qui a été mis en place et ce qui a changé, raconté sans chiffres impossibles à vérifier.",
f'''
<section class="heros-zone">
  <div class="contenu heros-seul">
    <p class="repere">Cas clients</p>
    <h1>Des histoires vraies, racontées <em>honnêtement.</em></h1>
    <p class="sous-titre">Vous ne trouverez pas de pourcentages spectaculaires sur cette page, et c'est un choix. Un chiffre sans date, sans source et sans contexte ne prouve rien. Nous republierons nos résultats chiffrés quand chacun pourra être daté, sourcé et validé par le client concerné.</p>
    <p class="sous-titre" style="margin-bottom:0">En attendant, voici ce que nous avons fait, et ce que nos clients en disent.</p>
    <nav class="sommaire-cas" aria-label="Les quatre cas">{sommaire_cas}</nav>
  </div>
</section>
<section class="fond-chaud">
  <div class="contenu">
{cas("limpid", I_NETTOYAGE, "Fiche Google et lancement · Entreprise de notre fondateur", "Limpid", "Entreprise de nettoyage · Darnieulles (88)",
     "Limpid est l'entreprise de nettoyage de notre fondateur. À son lancement, sa fiche Google était presque invisible sur Maps : peu d'avis, aucune preuve visible, aucun contact.",
     "Mise en conformité complète de la fiche Google : catégories, zone d'intervention, éléments de confiance. Pour le lancement, une annonce payante de Google dédiée aux services locaux. Puis une démarche régulière pour recueillir des avis authentiques auprès des clients.",
     "Les premières demandes sérieuses sont arrivées de clients proches, dans la zone d'intervention, et l'entreprise a signé ses premiers clients.",
     '\n      <p class="pourquoi"><strong>Pourquoi commencer par ce cas.</strong> Avant de proposer cette méthode, notre fondateur l\'a appliquée à sa propre entreprise, avec son propre argent. C\'est aussi sur Limpid qu\'est testée, depuis septembre 2026, notre méthode de campagnes Google. Ce test fera l\'objet d\'un cas séparé, publié seulement quand ses résultats seront mesurés. <a href="/methode/">Découvrir notre méthode</a></p>', site="https://limpid-nettoyage.fr/")}
{cas("un-cadeau-une-histoire", I_CADEAU, "Site internet et fiche Google", "Un Cadeau Une Histoire", "Boutique de cadeaux personnalisés · Darnieulles (88)",
     "Une boutique appréciée de sa clientèle, mais une présence en ligne qui ne reflétait ni la qualité de son travail ni la richesse de ses créations.",
     "Création d'un nouveau site, rafraîchissement complet de la fiche Google, et des conseils concrets pour entretenir cette présence dans la durée.",
     "Selon sa gérante, la boutique est désormais plus visible, plus attractive, et davantage recommandée par ses clients.",
     TEMOIN.format(q="Le travail de ViZiBiLi a véritablement transformé notre présence locale. Grâce au nouveau site et à la fiche Google rafraîchie, nous sommes désormais visibles, attractifs et recommandés par nos clients locaux. De plus, tout au long de notre collaboration, Clément, le gérant de l'agence, nous a accompagnés et donné des conseils utiles à appliquer pour maintenir la qualité de notre visibilité. Une vraie réussite !", a="Annie, gérante"), site="https://uncadeau-unehistoire.com/")}
{cas("gite-chez-paul", I_MAISON, "Fiche Google", "Gîte Chez Paul", "Location de gîte touristique · Épinal (88)",
     "Un gîte bien tenu, mais une fiche Google qui ne le mettait pas en valeur auprès des voyageurs.",
     "Optimisation complète de la fiche Google et mise en avant des avis clients.",
     "Selon sa propriétaire, la fiche est devenue un vrai levier de réservations.",
     TEMOIN.format(q="ViZiBiLi a su transformer notre fiche Google en un vrai levier de réservations. Le travail est sérieux, structuré et orienté résultats. On voit clairement la différence.", a="La propriétaire"))}
{cas("gite-de-la-marie", I_MAISON, "Fiche Google", "Gîte de la Marie", "Location de gîte touristique · Épinal (88)",
     "Une fiche Google qui n'était pas à la hauteur du gîte qu'elle présentait.",
     "Remise en cohérence et optimisation de la fiche Google, avec une présentation claire et structurée.",
     "Selon sa propriétaire, le gîte a gagné en visibilité, en cohérence et en réservations.",
     TEMOIN.format(q="Grâce à l'accompagnement de ViZiBiLi, notre fiche Google est enfin à la hauteur de notre gîte. Nous avons gagné en visibilité, en cohérence et en réservations. Tout est clair, structuré et surtout efficace.", a="La propriétaire"))}
  </div>
</section>
{bande("Votre entreprise pourrait être la prochaine histoire.", "", "Demander un premier échange")}
''', actif='/cas-clients/'))

# ---------------------------------------------------------------- À PROPOS
PRINCIPES = [
    (I_OEIL, "Dire la vérité, même quand elle est moins vendeuse.", "Nous ne publions pas un résultat avant de l'avoir mesuré, y compris les nôtres."),
    (I_MESURE, "Mesurer avant de promettre.", "Une décision s'appuie sur ce que disent vos demandes, vos devis et vos contrats, pas sur une impression."),
    (I_CLE, "Vous laisser propriétaire de tout.", "Compte publicitaire, site, fiche Google, données : tout est à votre nom, dès le premier jour."),
]
PAGES.append(page('/a-propos/', 'À propos de ViZiBiLi, agence née du terrain dans les Vosges',
    "ViZiBiLi est née dans une entreprise de nettoyage des Vosges. Une structure à taille humaine, où vous échangez toujours directement avec son fondateur.",
f'''
<section class="heros-zone">
  <div class="contenu heros">
    <div>
      <p class="repere">À propos</p>
      <h1>Derrière ViZiBiLi, un dirigeant qui cherche lui aussi <em>ses clients.</em></h1>
      <p class="sous-titre">ViZiBiLi n'a pas été imaginée dans une agence. Elle est née dans une entreprise de nettoyage des Vosges, face à une question très concrète : comment trouver des clients sérieux sans gaspiller ni temps ni argent ?</p>
    </div>
    <div class="origine" aria-hidden="true">
      <span class="og-noeud og-a">{I_NETTOYAGE}<em>Une entreprise de nettoyage</em></span>
      <span class="og-trait"></span>
      <span class="og-noeud og-q"><b>?</b><em>Comment trouver des clients sérieux</em></span>
      <span class="og-trait"></span>
      <span class="og-noeud og-b">{LOGO_MARK.replace('class="logo-mark" ', '')}<em>ViZiBiLi</em></span>
    </div>
  </div>
</section>
<section class="fond-chaud">
  <div class="contenu titre-section">
    <h2>Une méthode construite pour soi, avant d'être proposée aux autres.</h2>
    <p>Clément, notre fondateur, dirige Limpid, une entreprise de nettoyage installée à Darnieulles. Comme beaucoup de dirigeants, il a d'abord payé pour être visible sans savoir précisément ce que cela lui rapportait.</p>
    <p style="margin-top:12px">Plutôt que de multiplier les outils, il a choisi de regarder le chemin entier : qui cherche, qui demande un devis, qui signe, et combien cela coûte vraiment. C'est de ce travail qu'est née la méthode de ViZiBiLi.</p>
  </div>
</section>
<section>
  <div class="contenu">
    <div class="titre-section"><h2>Trois principes, sans exception.</h2></div>
    {tuiles(PRINCIPES, 3)}
  </div>
</section>
<section class="fond-chaud">
  <div class="contenu deux-temps">
    <div class="titre-section">
      <h2>Vous parlez toujours à la même personne.</h2>
      <p>ViZiBiLi est une structure à taille humaine. Vous échangez directement avec son fondateur, du premier échange au suivi de vos résultats. Pas d'intermédiaire, pas de dossier qui passe de main en main.</p>
      <p style="margin-top:12px">Nous accompagnons les entreprises de nettoyage partout en France, à distance, et les entreprises locales des Vosges.</p>
    </div>
    <div class="direct" aria-hidden="true">
      <span class="dr-noeud">{I_VOUS}<em>Vous</em></span>
      <span class="dr-ligne"><i></i><i></i><b class="dr-barre">{I_CROIX}<small>Intermédiaires</small></b></span>
      <span class="dr-noeud dr-fond">{I_VOUS}<em>Clément, fondateur</em></span>
    </div>
  </div>
</section>
{bande("Faisons connaissance.", "Le premier échange est offert. Nous vous dirons franchement si nous pouvons vous aider.", "Demander un premier échange")}
''', actif='/a-propos/', jsonld=[{"@type": "AboutPage", "url": SITE + "/a-propos/"}]))

# ---------------------------------------------------------------- FICHE GOOGLE · VOSGES (16/10/2026, plan SEO)
FAQ_F = [
    ("Combien de temps faut-il pour voir un effet ?", "Les corrections apparaissent sur la fiche en quelques jours. Leur effet sur votre place dans les résultats prend en général plusieurs semaines, et dépend de votre métier, de votre zone et de vos concurrents. Nous ne promettons aucune position."),
    ("Faut-il un site internet en plus de la fiche ?", "Ce n'est pas obligatoire. Mais une fiche reliée à une page claire de votre offre transforme mieux les visites en demandes. Nous vous disons franchement si votre site actuel suffit."),
    ("Votre fiche est suspendue, ou vous n'y avez plus accès ?", "Oui. Nous vous aidons à comprendre la cause et à suivre les démarches prévues par Google pour retrouver l'accès ou faire réexaminer la fiche."),
    ("La fiche reste-t-elle à votre nom ?", "Oui. La fiche reste à votre nom et sous votre contrôle. Si nous avons besoin d'y accéder, c'est comme gestionnaire, et vous pouvez retirer cet accès à tout moment."),
    ("Combien coûte un audit de fiche Google ?", "Le prix dépend de votre situation. Il vous est donné par écrit avant de commencer, après un premier échange offert."),
]
faq_f = '\n'.join(f'      <details{" open" if i == 0 else ""}><summary>{q}</summary><p>{r}</p></details>' for i, (q, r) in enumerate(FAQ_F))
faq_ld_f = {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}} for q, r in FAQ_F]}
svc_f = {"@type": "Service", "name": "Audit et remise en ordre de fiche Google", "serviceType": "Fiche Google et visibilité locale",
         "provider": {"@id": SITE + "/#organisation"},
         "areaServed": [{"@type": "City", "name": "Épinal"}, {"@type": "AdministrativeArea", "name": "Vosges"}, {"@type": "Country", "name": "France"}]}
VERIFS = [
    (I_FICHE, "La catégorie principale", "Elle décide en grande partie des recherches où vous apparaissez. Une catégorie trop large, ou voisine de votre métier, vous rend invisible là où ça compte."),
    (I_SUIVI, "L'adresse et la zone desservie", "Votre adresse, ou les communes que vous desservez vraiment. Une zone vide ou démesurée nuit à votre présence dans les recherches proches de chez vous."),
    (I_COCHE, "La cohérence des informations", "Nom, adresse et coordonnées identiques sur la fiche, le site et les annuaires. Les petites incohérences brouillent le signal envoyé à Google."),
    (I_BULLE, "Les avis clients", "Des avis récents et authentiques, demandés au bon moment, et une réponse à chacun. Jamais d'avis achetés ou inventés."),
    (I_PAGE, "Les photos et les services", "Des photos de vos réalisations, des horaires exacts, des services décrits avec les mots de vos clients."),
    (I_MESURE, "Ce que la fiche vous rapporte", "Les appels, les demandes d'itinéraire, les visites du site et surtout les demandes venues de la fiche : pour savoir si elle travaille vraiment pour vous."),
]
ETAPES_F = [
    (I_LOUPE, "Étape 1", "Audit de votre fiche", "Nous passons votre fiche en revue avec vous, et nous la comparons à celles qui apparaissent avant vous sur les recherches de vos clients.", "La liste des corrections, par ordre d'importance", None),
    (I_CONSTR, "Étape 2", "Corrections", "Catégories, zone, description, services, photos, horaires : nous corrigeons, ou nous vous guidons pas à pas si vous préférez le faire vous-même.", "Une fiche complète et cohérente avec votre site", None),
    (I_BULLE, "Étape 3", "Avis clients", "Nous mettons en place une façon simple de demander un avis à vos clients satisfaits, au bon moment, et de répondre à chacun.", "Une routine que vous gardez", None),
    (I_MESURE, "Étape 4", "Suivi des demandes", "Nous regardons ce que la fiche vous apporte : appels, itinéraires, visites, et surtout les demandes qui en viennent.", "Une vision claire de ce que la fiche rapporte", None),
]
PREUVES_F = [
    (I_NETTOYAGE, "Limpid", "Entreprise de nettoyage · Darnieulles", "Une fiche presque invisible à son lancement, mise en conformité complète, puis une démarche régulière pour recueillir des avis authentiques.", "limpid"),
    (I_MAISON, "Gîte Chez Paul et Gîte de la Marie", "Locations de gîtes · Épinal", "Des fiches optimisées et des avis clients mis en avant, pour des gîtes enfin présentés à leur juste valeur.", "gite-chez-paul"),
    (I_CADEAU, "Un Cadeau Une Histoire", "Boutique de cadeaux · Darnieulles", "Une fiche Google rafraîchie, un nouveau site, et des conseils pour entretenir cette présence dans la durée.", "un-cadeau-une-histoire"),
]
preuves_f = '\n'.join(f'      <a class="tuile rv" style="--i:{k}" href="/cas-clients/#{a}"><span class="tu-ico">{i}</span><h3>{n}</h3><p class="lieu-mini">{l}</p><p>{t}</p><span class="lire">Lire le cas{I_FLECHE}</span></a>' for k, (i, n, l, t, a) in enumerate(PREUVES_F))
CHECK_F = ["Catégorie principale", "Zone desservie", "Horaires exacts", "Avis récents", "Photos de vos réalisations"]
check_f = ''.join(f'<li style="--i:{k}"><span>{I_COCHE}</span>{c}</li>' for k, c in enumerate(CHECK_F))

PAGES.append(page('/fiche-google-vosges/', 'Audit de fiche Google et visibilité locale · Vosges · ViZiBiLi',
    "Audit de fiche Google à Épinal et dans les Vosges : catégorie, zone, avis, photos, pour que votre visibilité locale devienne des demandes.",
f'''
<section class="heros-zone">
  <div class="contenu heros">
    <div>
      <p class="repere">Fiche Google · Épinal et Vosges</p>
      <h1>Votre fiche Google, remise en ordre pour devenir <em>une source de demandes.</em></h1>
      <p class="sous-titre">Quand un client cherche votre métier près de chez lui, c'est souvent votre fiche Google qu'il voit en premier. Nous l'auditons, nous la corrigeons, et nous vérifions qu'elle vous apporte des demandes, pas seulement des vues.</p>
      <div class="actions"><a href="/premier-echange/" class="btn btn-plein">Demander un premier échange</a><a href="#verifications" class="btn btn-ligne">Ce que nous vérifions</a></div>
      <p class="reassurance">Sur place à Épinal, Darnieulles et dans tout le département des Vosges. À distance partout en France. Premier échange offert.</p>
    </div>
    <div class="fiche-demo" aria-hidden="true">
      <div class="fd-tete"><span class="fd-pin">{I_FICHE}</span><div><strong>Votre entreprise</strong><small>Votre métier · Épinal</small></div></div>
      <ul class="fd-liste">{check_f}</ul>
      <div class="fd-pied"><span>{I_DEMANDE}</span>Une demande reçue depuis votre fiche</div>
    </div>
  </div>
</section>

<section class="fond-chaud" id="verifications">
  <div class="contenu">
    <div class="titre-section"><h2>Ce que nous vérifions sur votre fiche.</h2><p>Six points, toujours dans cet ordre. Les deux premiers décident souvent à eux seuls si vous apparaissez quand on cherche votre métier près de chez vous.</p></div>
    {tuiles(VERIFS, 3, numeros=True)}
  </div>
</section>

<section>
  <div class="contenu">
    <div class="titre-section"><h2>Quatre étapes, de l'audit aux demandes.</h2><p>Vous pouvez vous arrêter après l'audit et faire les corrections vous-même : la liste vous appartient.</p></div>
    {route(ETAPES_F, arrivee="Des demandes qui viennent de votre fiche", aria="Les quatre étapes de la remise en ordre d'une fiche Google")}
  </div>
</section>

<section class="fond-chaud">
  <div class="contenu">
    <div class="titre-section"><h2>Des fiches que nous avons déjà remises en ordre.</h2><p>Dans les Vosges, racontées sans chiffres impossibles à vérifier.</p></div>
    <div class="tuiles t3 preuves-fiche">
{preuves_f}
    </div>
  </div>
</section>

<section>
  <div class="contenu bloc-encre">
    <div class="disposition">
      <div>
        <p class="repere">Au-delà de la fiche</p>
        <h2>Une fiche Google n'est qu'une partie du chemin.</h2>
        <p>Une fiche bien tenue vous rend visible. Mais être visible ne suffit pas : encore faut-il que les bonnes personnes vous écrivent, et que leurs demandes deviennent des devis signés. C'est pourquoi nous regardons aussi votre site, la façon dont vous répondez aux demandes et, quand c'est utile, les annonces Google.</p>
      </div>
      <a href="/methode/" class="btn btn-plein">Découvrir notre méthode</a>
    </div>
  </div>
</section>

<section class="fond-chaud">
  <div class="contenu deux-temps">
    <div class="titre-section">
      <h2>Pour qui ?</h2>
      <p>Les artisans, commerçants, indépendants, professions libérales, gîtes et entreprises de services d'Épinal, de Darnieulles et de tout le département des Vosges.</p>
      <p style="margin-top:12px">Et les entreprises de nettoyage partout en France : c'est notre spécialité. <a href="/entreprises-de-nettoyage/">Notre approche pour les entreprises de nettoyage</a></p>
    </div>
    <div class="carnet" aria-hidden="true">
      <p class="carnet-titre">{I_FICHE}Dans les Vosges</p>
      <ul><li class="rv" style="--i:0"><span>{I_FICHE}</span>Épinal et son agglomération</li><li class="rv" style="--i:1"><span>{I_MAISON}</span>Darnieulles et alentours</li><li class="rv" style="--i:2"><span>{I_SUIVI}</span>Tout le département</li><li class="rv" style="--i:3"><span>{I_BULLE}</span>À distance, partout en France</li></ul>
    </div>
  </div>
</section>

<section>
  <div class="etroit">
    <h2>Vos questions sur la fiche Google</h2>
    <div class="faq">
{faq_f}
    </div>
    <p class="note">Pour aller plus loin : <a href="/ressources/entreprise-absente-google-maps/">pourquoi votre entreprise n'apparaît pas sur Google Maps</a>.</p>
  </div>
</section>
{bande("Votre fiche Google vous apporte-t-elle des demandes ?", "Parlons-en 15 à 30 minutes. Le premier échange est offert.", "Demander un premier échange")}
''', actif=None, jsonld=[svc_f, faq_ld_f]))


# ---------------------------------------------------------------- PREMIER ÉCHANGE (conversion unique)
SECTEURS = ['Nettoyage et propreté', 'Artisanat et bâtiment', 'Commerce de proximité', 'Professions libérales et santé', 'Hôtellerie, restauration, tourisme', 'Services aux entreprises', 'Services aux particuliers', 'Autre secteur']
OBJECTIFS = ['Obtenir davantage de demandes qualifiées', 'Développer des contrats récurrents', 'Améliorer la transformation des prospects', 'Comprendre les performances actuelles', 'Structurer son acquisition sur Google', 'Autre besoin']
PRESTATIONS = ["Entretien de bureaux et locaux", "Nettoyage de vitres", "Ménage à domicile", "Grand ménage, fin de bail", "Autre prestation"]
opt_secteurs = '\n'.join(f'            <option value="{esc(x)}">{esc(x)}</option>' for x in SECTEURS)
opt_objectifs = '\n'.join(f'          <label class="choix"><input type="radio" name="objectif" value="{esc(x)}"{" data-requis required" if k == 0 else ""}> {esc(x)}</label>' for k, x in enumerate(OBJECTIFS))
opt_presta = '\n'.join(f'            <label class="choix"><input type="checkbox" name="prestations" value="{esc(x)}"> {esc(x)}</label>' for x in PRESTATIONS)
ts_widget = f'\n        <div class="cf-turnstile" data-sitekey="{esc(TURNSTILE)}" data-language="fr"></div>' if TURNSTILE else ''
FAQ_PE = [
    ("Le premier échange m'engage-t-il à quelque chose ?", "Non. Il est offert et ne vous engage à rien. À la fin, nous vous disons franchement si nous pouvons vous aider."),
    ("Pourquoi le diagnostic approfondi est-il une prestation distincte ?", "Parce qu'il demande un vrai travail d'analyse sur vos outils, vos données et vos devis. Vous connaissez son contenu et son prix par écrit avant de décider."),
    ("Je ne suis pas dans le nettoyage. Pouvez-vous m'aider ?", "Oui, peut-être. La propreté est notre spécialité, mais nous accompagnons des entreprises de tous secteurs. Le premier échange sert justement à le vérifier."),
    ("Que faites-vous de mes informations ?", "Elles servent uniquement à répondre à votre demande. Elles ne sont ni vendues ni partagées. Tout est expliqué dans notre politique de confidentialité."),
]
faq_pe = '\n'.join(f'      <details><summary>{q}</summary><p>{r}</p></details>' for q, r in FAQ_PE)
PAGES.append(page('/premier-echange/', "Demander un premier échange · ViZiBiLi",
    "Un premier échange offert de 15 à 30 minutes pour comprendre votre situation. Le diagnostic approfondi est une prestation distincte, au prix connu d'avance.",
f'''
<section class="heros-zone">
  <div class="contenu heros-seul">
    <p class="repere">Premier échange et diagnostic</p>
    <h1>Commençons par un premier échange. <em>Offert, et sans détour.</em></h1>
    <p class="sous-titre">Ce qui est offert, ce qui est payant et ce qui vous engage sont clairement séparés. Vous savez toujours où vous en êtes.</p>
  </div>
</section>

<section class="fond-chaud" style="padding-top:56px">
  <div class="contenu">
    {route([
      (I_BULLE, '<span class="statut offert">Offert</span>', "Premier échange", "<strong>15 à 30 minutes</strong>, par téléphone ou en visio. Nous cherchons à comprendre votre situation et à déterminer si un accompagnement est réellement pertinent. Si ce n'est pas le cas, nous vous le disons.", None, "premier-echange"),
      (I_DIAG, '<span class="statut">Prestation distincte</span>', "Diagnostic approfondi", "Analyse de l'existant, identification des blocages, étude des opportunités, priorisation, et une <strong>feuille de route exploitable</strong>, même si vous continuez seul. Son contenu et son prix vous sont donnés par écrit, avant de commencer.", None, "diagnostic"),
      (I_COMM, '<span class="statut">Sur proposition</span>', "Et ensuite ?", "Si un accompagnement a du sens, il fait l'objet d'une <strong>proposition séparée</strong> : périmètre, honoraires, et budget publicitaire payé directement par vous à Google, sur votre propre compte.", None, "ensuite"),
    ], aria="Ce qui est offert, ce qui est payant, ce qui vous engage")}
    <div class="pour-qui">
      <h2>Pour qui ?</h2>
      <p>Pour les entreprises qui veulent vraiment développer leurs demandes, et qui ont la capacité de les traiter quand elles arrivent. La propreté est notre spécialité, mais <strong>aucun secteur n'est exclu d'avance</strong> : le premier échange sert à le vérifier ensemble.</p>
    </div>
  </div>
</section>

<section id="demande">
  <div class="contenu diagnostic">
    <div>
      <h2>Votre demande de premier échange</h2>
      <p class="chapo" style="margin-bottom:24px">Sept questions, une minute. Le reste, nous en parlerons de vive voix.</p>
      <div class="jauge" aria-hidden="true"><div class="jauge-barre"><span></span></div><p class="jauge-texte">5 réponses obligatoires, c'est parti.</p></div>
      <form id="formulaire-demande" class="formulaire" action="/api/demande" method="post" novalidate>
        <div class="champ"><label for="nom">Nom et prénom <span class="requis" aria-hidden="true">*</span></label><input id="nom" name="nom" type="text" autocomplete="name" data-requis required aria-describedby="nom-err"><span class="message-erreur" id="nom-err">Indiquez votre nom.</span></div>
        <div class="champ"><label for="entreprise">Entreprise <span class="requis" aria-hidden="true">*</span></label><input id="entreprise" name="entreprise" type="text" autocomplete="organization" data-requis required aria-describedby="entreprise-err"><span class="message-erreur" id="entreprise-err">Indiquez le nom de votre entreprise.</span></div>
        <div class="champ"><label for="email">E-mail <span class="requis" aria-hidden="true">*</span></label><input id="email" name="email" type="email" inputmode="email" autocomplete="email" data-requis required aria-describedby="email-err"><span class="message-erreur" id="email-err">Indiquez une adresse e-mail valide, par exemple nom@entreprise.fr.</span></div>
        <div class="champ"><label for="telephone">Téléphone <span class="facultatif">(facultatif)</span></label><span class="aide" id="telephone-aide">Si vous préférez être rappelé.</span><input id="telephone" name="telephone" type="tel" inputmode="tel" autocomplete="tel" aria-describedby="telephone-aide telephone-err"><span class="message-erreur" id="telephone-err">Ce numéro ne semble pas complet.</span></div>
        <div class="champ"><label for="secteur">Secteur d'activité <span class="requis" aria-hidden="true">*</span></label><select id="secteur" name="secteur" data-requis required aria-describedby="secteur-err"><option value="">Choisissez votre secteur</option>
{opt_secteurs}
          </select><span class="message-erreur" id="secteur-err">Choisissez votre secteur, ou « Autre secteur ».</span></div>
        <fieldset class="champ complement-proprete" id="complement-proprete" hidden><legend>Pour une entreprise de propreté <span class="facultatif">(facultatif)</span></legend>
          <p class="aide">Vos prestations actuelles :</p>
          <div class="choix-multiples">
{opt_presta}
          </div>
          <p class="aide" style="margin-top:8px">Vous cherchez surtout :</p>
          <div class="choix-multiples">
            <label class="choix"><input type="radio" name="recherche" value="Contrats récurrents"> Des contrats récurrents</label>
            <label class="choix"><input type="radio" name="recherche" value="Prestations ponctuelles"> Des prestations ponctuelles</label>
            <label class="choix"><input type="radio" name="recherche" value="Les deux"> Les deux</label>
          </div>
        </fieldset>
        <div class="champ"><fieldset><legend>Votre objectif principal <span class="requis" aria-hidden="true">*</span></legend>
{opt_objectifs}
        </fieldset><span class="message-erreur">Choisissez votre objectif principal.</span></div>
        <div class="champ"><label for="site">Site internet <span class="facultatif">(facultatif)</span></label><input id="site" name="site" type="text" inputmode="url" autocomplete="url" placeholder="www.votre-entreprise.fr"></div>
        <div class="piege" aria-hidden="true"><label for="entreprise_web">Ne pas remplir</label><input id="entreprise_web" name="entreprise_web" type="text" tabindex="-1" autocomplete="off"></div>
        <input type="hidden" name="demande_id"><input type="hidden" name="prov_source"><input type="hidden" name="prov_support"><input type="hidden" name="prov_campagne"><input type="hidden" name="prov_terme"><input type="hidden" name="prov_contenu"><input type="hidden" name="prov_arrivee"><input type="hidden" name="prov_referent"><input type="hidden" name="prov_date_arrivee"><input type="hidden" name="prov_gclid"><input type="hidden" name="prov_gbraid"><input type="hidden" name="prov_wbraid">{ts_widget}
        <p class="mention">Vos informations servent uniquement à répondre à votre demande. Elles ne sont ni vendues ni partagées. <a href="/confidentialite/">Politique de confidentialité</a></p>
        <p id="alerte-envoi" class="alerte-envoi" tabindex="-1" role="alert">Votre demande n'a pas pu être envoyée. Vérifiez votre connexion et réessayez, ou écrivez-nous à <a href="mailto:hello@vizibili.fr">hello@vizibili.fr</a>.</p>
        <button type="submit" class="btn btn-plein">Envoyer ma demande</button>
      </form>
    </div>
    <aside class="encart">
      <h2>Ce qui se passe après votre demande.</h2>
      <ol class="etapes">
        <li><p><strong>Nous lisons votre demande</strong> et regardons rapidement votre présence actuelle sur Google.</p></li>
        <li><p><strong>Nous revenons vers vous</strong> pour convenir du premier échange, par téléphone ou en visio.</p></li>
        <li><p><strong>Nous vous disons franchement</strong> si nous pouvons vous aider. Si un diagnostic approfondi est utile, vous recevez son contenu et son prix par écrit, et vous décidez.</p></li>
      </ol>
      <p class="ecrire">Vous préférez écrire ? <a href="mailto:hello@vizibili.fr">hello@vizibili.fr</a></p>
    </aside>
  </div>
</section>

<section class="fond-chaud">
  <div class="etroit">
    <h2>Avant de nous écrire</h2>
    <div class="faq">
{faq_pe}
    </div>
  </div>
</section>
''', actif=None, jsonld=[{"@type": "ContactPage", "url": SITE + "/premier-echange/"}], formulaire=True))

PAGES.append(page('/premier-echange/merci/', 'Demande reçue · ViZiBiLi', "Votre demande de premier échange a bien été reçue.",
f'''
<section>
  <div class="centre">
    <div class="succes" aria-hidden="true"><span class="succes-coche">{I_COCHE}</span><span class="confettis"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></span></div>
    <h1>Votre demande est bien <em>reçue.</em></h1>
    <p class="sous-titre" style="margin:0 auto">Elle est arrivée chez nous et nous allons la lire attentivement.</p>
    <div class="encart">
      <h2>Et maintenant ?</h2>
      <ol class="etapes">
        <li><p><strong>Nous revenons vers vous</strong> pour convenir du premier échange offert. Nous ne promettons pas de délai précis : nous préférons répondre bien plutôt que vite.</p></li>
        <li><p><strong>Le premier échange</strong> dure de 15 à 30 minutes et ne vous engage à rien.</p></li>
        <li><p><strong>Si un diagnostic approfondi est utile</strong>, c'est une prestation distincte : vous recevez son contenu et son prix par écrit avant toute décision.</p></li>
      </ol>
    </div>
    <a href="/">Retour à l'accueil</a>
  </div>
</section>
''', indexer=False))

# ---------------------------------------------------------------- RESSOURCES
ARTICLES = []

def article(slug, titre, desc, h1, corps, chapo):
    h1_texte = re.sub(r'<[^>]+>', '', h1)  # balises d'accent retirées hors du titre affiché
    ARTICLES.append((slug, h1_texte, chapo))
    art_ld = {"@type": "Article", "headline": h1_texte, "description": desc, "inLanguage": "fr-FR",
              "author": {"@id": SITE + "/#organisation"}, "publisher": {"@id": SITE + "/#organisation"},
              "mainEntityOfPage": SITE + f"/ressources/{slug}/"}
    fil_ld = {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Accueil", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Ressources", "item": SITE + "/ressources/"},
        {"@type": "ListItem", "position": 3, "name": h1_texte, "item": SITE + f"/ressources/{slug}/"}]}
    return page(f'/ressources/{slug}/', titre, desc, f'''
<section>
  <article class="etroit article">
    <nav class="fil" aria-label="Fil d'Ariane"><a href="/">Accueil</a> › <a href="/ressources/">Ressources</a></nav>
    <h1>{h1}</h1>
{corps.strip()}
  </article>
</section>''', jsonld=[art_ld, fil_ld])

PAGES.append(article('trouver-clients-entreprise-de-nettoyage', 'Comment trouver des clients pour une entreprise de nettoyage',
    "Contrats de bureaux, ménage à domicile, vitres : les sources de clients qui fonctionnent vraiment pour une entreprise de nettoyage, et comment les piloter.",
    "Comment trouver des <em>clients</em> pour une entreprise de nettoyage ?", '''
<p>Trouver des clients n'est pas le plus difficile dans le nettoyage. Le plus difficile, c'est de trouver <strong>les bons</strong> : ceux dont les demandes correspondent à vos prestations, à votre zone et à votre capacité. Voici ce que nous avons appris sur le terrain, dans l'entreprise de nettoyage de notre fondateur.</p>
<h2>1. Décidez d'abord quels clients vous voulez</h2>
<p>Un contrat d'entretien de bureaux, un ménage à domicile chaque semaine, un grand ménage avant déménagement, un lavage de vitrine : ce ne sont pas les mêmes clients, ni les mêmes recherches, ni la même rentabilité.</p>
<p>Avant de chercher plus de demandes, écrivez noir sur blanc :</p>
<ul><li>les prestations que vous voulez développer en priorité ;</li><li>la zone où vous acceptez de vous déplacer ;</li><li>ce que vous refusez, par exemple des locaux trop grands pour votre équipe ou du matériel que vous n'avez pas.</li></ul>
<p>Ce que vous excluez compte autant que ce que vous visez : un mauvais client coûte plus de temps qu'il ne rapporte.</p>
<h2>2. Exploitez ce que vous avez déjà</h2>
<p>Vos clients satisfaits sont votre meilleure source de nouveaux clients. Trois réflexes simples :</p>
<ul><li><strong>demander un avis Google</strong> à chaque client content, au bon moment, juste après une prestation réussie ;</li><li><strong>demander une recommandation</strong>, tout simplement, à vos clients professionnels ;</li><li><strong>identifier les prescripteurs</strong> de votre zone : agences immobilières pour les fins de bail, gestionnaires de biens, déménageurs, conciergeries. Ils voient passer vos futurs clients avant vous.</li></ul>
<h2>3. Soignez votre fiche Google</h2>
<p>Quand un particulier cherche un prestataire près de chez lui, il regarde d'abord la carte. Une fiche complète, avec la bonne catégorie, votre vraie zone d'intervention, des photos de vos chantiers et des avis récents, fait souvent la différence entre un appel et un oubli.</p>
<h2>4. Allez chercher les professionnels directement</h2>
<p>Pour les contrats de bureaux et de commerces, attendre que le client vous trouve est souvent trop lent. Privilégiez les entreprises dirigées par des indépendants, à qui vous pouvez parler directement : la décision est plus rapide qu'auprès d'une enseigne ou d'un grand compte, où tout se décide au siège. Nous détaillons la démarche dans <a href="/ressources/contrats-entretien-bureaux/">comment obtenir des contrats d'entretien de bureaux</a>.</p>
<h2>5. Utilisez les annonces Google, mais avec méthode</h2>
<p>Les annonces Google vous placent devant quelqu'un qui cherche votre service maintenant. C'est puissant, à condition de :</p>
<ul><li>séparer les campagnes par type de clientèle (voir <a href="/ressources/publicite-google-entreprise-de-nettoyage/">ce qu'il faut vérifier</a>), par exemple professionnels d'un côté et particuliers de l'autre ;</li><li>exclure les recherches qui ne vous concernent pas, comme les offres d'emploi ou les prestations que vous ne faites pas ;</li><li>mesurer les demandes et ce qu'elles deviennent, pas seulement les clics.</li></ul>
<h2>6. Mesurez ce que chaque source vous rapporte</h2>
<p>C'est l'étape que presque tout le monde oublie. Pour chaque nouveau client, notez d'où il vient. Au bout de quelques mois, vous saurez quelle source vous apporte des contrats durables, et laquelle ne vous apporte que des devis sans suite.</p>
<h2>En résumé</h2>
<p>Les entreprises de nettoyage qui se développent ne sont pas forcément celles qui reçoivent le plus de demandes. Ce sont celles qui savent quels clients elles veulent, d'où ils viennent, et ce qu'ils leur rapportent.</p>
<p style="margin-top:28px">Vous voulez savoir par où commencer pour votre entreprise ? <a href="/premier-echange/?secteur=proprete" class="btn btn-plein" style="margin-left:6px">Demander un premier échange</a></p>
''', "Les sources de clients qui fonctionnent vraiment, et comment savoir lesquelles vous rapportent."))

PAGES.append(article('publicite-google-rapporte-t-elle-des-clients', 'Votre publicité Google vous rapporte-t-elle des clients ?',
    "Clics, demandes, devis, contrats : comment savoir si votre publicité Google vous rapporte vraiment des clients, et ce qu'elle vous coûte par client signé.",
    "Votre publicité Google vous rapporte-t-elle <em>vraiment des clients</em> ?", '''
<p>Beaucoup d'entreprises paient chaque mois des annonces Google sans pouvoir répondre à cette question simple. Elles voient des clics, parfois des appels, mais ne savent pas combien de clients ces annonces leur ont réellement apportés. Voici comment le savoir.</p>
<h2>Un clic n'est pas un client</h2>
<p>Entre la recherche et la signature, il y a plusieurs étapes, et chacune perd du monde :</p>
<p class="formule">Clic → Demande → Demande sérieuse → Devis → Client signé</p>
<p>Un rapport qui s'arrête aux clics ou aux appels vous montre le début du chemin, jamais la fin. Or c'est la fin qui paie vos factures.</p>
<h2>Les signes que votre publicité ne vous rapporte pas assez</h2>
<ul><li>Vous recevez des appels pour des prestations que vous ne faites pas.</li><li>Des demandes arrivent de trop loin pour que vous vous déplaciez.</li><li>Vous ne savez pas quelles recherches ont déclenché vos annonces.</li><li>Personne ne vous a jamais montré combien de devis ou de contrats sont venus de la publicité.</li><li>Votre compte publicitaire n'est pas à votre nom, ou vous n'y avez pas accès.</li></ul>
<p>Un seul de ces signes suffit pour vous poser la question.</p>
<h2>Les trois vérifications à faire vous-même</h2>
<p><strong>1. Regardez ce que les gens ont réellement tapé.</strong> Dans votre compte Google, la liste des recherches qui ont affiché vos annonces est souvent surprenante. Elle n'est jamais complète, car Google regroupe une partie des recherches sans les détailler, mais elle révèle déjà des clics payés pour rien.</p>
<p><strong>2. Comptez les demandes, pas les clics.</strong> Pendant un mois, notez chaque demande reçue et sa provenance. Un simple tableau suffit.</p>
<p><strong>3. Suivez ce qu'elles deviennent.</strong> Pour chaque demande : était-elle sérieuse ? A-t-elle donné un devis ? Un contrat ?</p>
<h2>Le seul calcul qui compte</h2>
<p class="formule">Ce que vous coûte un client = budget publicitaire de la période ÷ nombre de clients signés grâce à la publicité.</p>
<p class="exemple"><strong>Exemple fictif, pour illustrer le calcul :</strong> une entreprise dépense 400 € sur un mois et signe 2 clients grâce à ses annonces. Chaque client lui a coûté 200 €. Si un client lui rapporte plusieurs milliers d'euros sur un an, c'est un excellent placement. S'il ne commande qu'une prestation à 150 €, c'est une perte.</p>
<p>Sans ce calcul, impossible de savoir s'il faut augmenter, réduire ou arrêter.</p>
<h2>Ce que vous êtes en droit d'exiger</h2>
<p>Que vous gériez vos annonces vous-même ou avec un prestataire :</p>
<ul><li>un compte publicitaire <strong>à votre nom</strong>, auquel vous avez accès ;</li><li>un budget publicitaire que vous voyez et que vous payez directement à Google ;</li><li>des rapports qui parlent de demandes, de devis et de clients, pas seulement de clics.</li></ul>
<h2>En résumé</h2>
<p>La bonne question n'est pas « combien de clics ai-je eus ? », mais « combien de clients ai-je signés, et à quel prix ? ». Tant que vous ne pouvez pas y répondre, votre publicité n'est pas pilotée.</p>
<p style="margin-top:28px">Vous voulez savoir ce que votre publicité vous rapporte vraiment ? <a href="/premier-echange/" class="btn btn-plein" style="margin-left:6px">Demander un premier échange</a></p>
''', "Clics, demandes, devis, contrats : le seul calcul qui dit si votre publicité est rentable."))

PAGES.append(article('entreprise-absente-google-maps', "Pourquoi votre entreprise n'apparaît pas sur Google Maps",
    "Fiche non validée, mauvaise catégorie, informations incohérentes : les raisons les plus fréquentes pour lesquelles une entreprise est absente de Google Maps.",
    "Pourquoi votre entreprise <em>n'apparaît pas</em> sur Google Maps ?", '''
<p>Vous cherchez votre métier et votre ville sur Google, et votre entreprise n'apparaît pas sur la carte, alors que vos concurrents y sont. C'est l'une des questions que nous entendons le plus souvent. Les causes sont presque toujours les mêmes, et la plupart se corrigent.</p>
<h2>1. Votre fiche n'existe pas, ou n'est pas validée</h2>
<p>Une fiche Google doit être créée, puis validée par Google. Une fiche jamais validée, ou créée par quelqu'un d'autre et laissée à l'abandon, n'apparaîtra pas correctement. Vérifiez d'abord que vous avez bien accès à votre fiche et qu'elle est validée.</p>
<h2>2. La catégorie principale ne correspond pas à ce que l'on cherche</h2>
<p>Google s'appuie fortement sur la catégorie principale pour savoir quand afficher votre entreprise. Si vous êtes classé dans une catégorie trop générale ou voisine de votre métier, vous serez absent des recherches qui comptent.</p>
<h2>3. Vos informations ne sont pas cohérentes</h2>
<p>Le nom de l'entreprise, l'adresse et les coordonnées doivent être <strong>exactement</strong> les mêmes sur votre fiche, votre site et les annuaires où vous apparaissez. Une adresse écrite de deux façons différentes, un ancien nom resté en ligne : ces petites incohérences brouillent le signal.</p>
<h2>4. Votre zone d'intervention est mal renseignée</h2>
<p>Si vous vous déplacez chez vos clients, indiquez les communes que vous desservez réellement. Une zone vide, ou au contraire démesurée, nuit à votre présence dans les recherches locales.</p>
<h2>5. Votre fiche ne montre pas de signes de vie</h2>
<p>Peu d'avis, des avis anciens, aucune photo récente, des horaires approximatifs : Google, comme vos futurs clients, privilégie les entreprises qui semblent actives et fiables.</p>
<h2>6. La distance joue, et vous n'y pouvez rien</h2>
<p>Google tient compte de la distance entre la personne qui cherche et votre entreprise. Vous n'apparaîtrez pas partout, pour tout le monde. C'est normal : l'objectif est d'être bien présent là où se trouvent vos clients.</p>
<h2>7. Votre fiche a été suspendue</h2>
<p>Un nom d'entreprise rempli de mots-clés, une adresse non conforme ou certaines modifications peuvent entraîner une suspension. Si votre fiche a disparu du jour au lendemain, vérifiez son état dans votre espace Google.</p>
<h2>Par où commencer ?</h2>
<ol><li>Vérifiez que vous avez accès à votre fiche et qu'elle est validée.</li><li>Contrôlez la catégorie principale.</li><li>Comparez nom, adresse et coordonnées sur votre fiche et votre site.</li><li>Renseignez votre vraie zone d'intervention.</li><li>Demandez un avis à vos trois derniers clients satisfaits.</li></ol>
<p>Être sur la carte est un bon début. Mais apparaître ne suffit pas : encore faut-il que cette visibilité se transforme en demandes, puis en clients.</p>
<p style="margin-top:28px">Vous voulez comprendre pourquoi vos clients ne vous trouvent pas, et ce qui vous ferait gagner des demandes ? <a href="/premier-echange/" class="btn btn-plein" style="margin-left:6px">Demander un premier échange</a></p>
''', "Les sept causes les plus fréquentes, et par où commencer pour les corriger."))

PAGES.append(article('contrats-entretien-bureaux', "Comment obtenir des contrats d'entretien de bureaux",
    "Cibler les bons locaux, parler aux décideurs, chiffrer juste et relancer : comment une entreprise de nettoyage décroche des contrats de bureaux.",
    "Comment obtenir des <em>contrats d'entretien</em> de bureaux ?", '''
<p>Un contrat d'entretien de bureaux, c'est un chiffre d'affaires qui revient chaque mois, des horaires prévisibles et un client qui peut rester des années. C'est aussi un marché où l'on ne gagne pas en attendant que le téléphone sonne. Voici la démarche que nous appliquons dans l'entreprise de nettoyage de notre fondateur, et avec les entreprises que nous accompagnons.</p>
<h2>1. Choisissez les locaux que vous pouvez vraiment servir</h2>
<p>Tous les bureaux ne se valent pas pour votre entreprise. Avant de prospecter, décidez :</p>
<ul><li>la <strong>surface</strong> que votre équipe peut entretenir correctement, au rythme demandé ;</li><li>les <strong>créneaux</strong> que vous pouvez tenir : tôt le matin, le soir, le week-end ;</li><li>la <strong>zone</strong> au-delà de laquelle le trajet mange votre marge ;</li><li>les <strong>types de locaux</strong> où vous êtes à l'aise : cabinets, agences, petits sièges, espaces de coworking, locaux médicaux.</li></ul>
<p>Une liste courte et précise vaut mieux qu'une prospection tous azimuts : vous parlerez mieux à des clients qui vous ressemblent.</p>
<h2>2. Parlez à la personne qui décide</h2>
<p>Dans une petite structure, c'est souvent le dirigeant ou l'office manager. Dans un immeuble partagé, c'est parfois le gestionnaire ou le syndic. Dans une grande entreprise, la décision se prend au siège, souvent par appel d'offres : le chemin est long et la marge serrée.</p>
<p>Pour une entreprise de nettoyage locale, les cibles les plus accessibles sont en général les structures dirigées sur place : cabinets d'expertise comptable, avocats, notaires, architectes, agences immobilières, assurances, professions de santé, PME de services.</p>
<h2>3. Soyez trouvable au moment où l'on vous cherche</h2>
<p>Un dirigeant dont le prestataire vient de partir tape « entreprise de nettoyage bureaux » suivi de sa ville. Ce jour-là, trois choses comptent :</p>
<ul><li>une <strong>fiche Google</strong> complète, avec la bonne catégorie, votre zone, des photos de locaux entretenus et des avis récents de clients professionnels ;</li><li>une <strong>page qui parle aux professionnels</strong> : fréquences possibles, horaires, matériel, assurance, interlocuteur unique, délai pour une visite ;</li><li>un moyen simple de demander une visite ou un devis, avec une réponse rapide.</li></ul>
<p>Si vous voulez être présent plus vite sur ces recherches, les annonces Google peuvent compléter la fiche. Nous détaillons les réglages à vérifier dans <a href="/ressources/publicite-google-entreprise-de-nettoyage/">notre article sur la publicité Google pour une entreprise de nettoyage</a>.</p>
<h2>4. Allez au-devant des entreprises, sans les harceler</h2>
<p>La prospection directe reste efficace pour les bureaux, à condition d'être utile plutôt qu'insistant :</p>
<ul><li>repérez les entreprises de votre zone qui correspondent à votre liste ;</li><li>présentez-vous brièvement, par courrier, par e-mail ou en passant, avec une proposition concrète : une visite gratuite des locaux pour établir un devis précis ;</li><li>notez chaque contact, sa date et sa réponse, pour relancer au bon moment plutôt qu'au hasard.</li></ul>
<p>Pensez aussi aux prescripteurs : les agences immobilières d'entreprise, les gestionnaires d'immeubles, les centres d'affaires et les entreprises de travaux voient passer vos futurs clients avant vous.</p>
<h2>5. Faites une visite avant de chiffrer</h2>
<p>Un devis de bureaux fait à distance est presque toujours faux, dans un sens ou dans l'autre. La visite vous permet de mesurer les surfaces réelles, de compter les sanitaires et les postes de travail, de repérer les sols particuliers, et de comprendre ce qui déçoit le client dans sa prestation actuelle. C'est souvent là que se joue la signature.</p>
<h2>6. Rendez votre devis facile à accepter</h2>
<ul><li>détaillez les tâches et leur fréquence, pièce par pièce si besoin ;</li><li>indiquez clairement ce qui est inclus et ce qui ne l'est pas, par exemple les vitres ou les produits d'accueil ;</li><li>proposez une période de démarrage avec un point d'étape, pour rassurer un client qui change de prestataire ;</li><li>envoyez-le vite, tant que la visite est fraîche dans l'esprit du client.</li></ul>
<h2>7. Relancez, puis mesurez</h2>
<p>Beaucoup de devis ne sont pas refusés : ils sont oubliés. Une relance quelques jours après l'envoi, puis une seconde plus tard, suffit souvent à relancer la décision.</p>
<p>Enfin, pour chaque contrat signé, notez d'où vient le client : fiche Google, annonce, recommandation, prospection. Au bout de quelques mois, vous saurez quelle source vous apporte des contrats durables, et où mettre votre temps.</p>
<h2>En résumé</h2>
<p>Les contrats d'entretien de bureaux se gagnent rarement par hasard. Ils viennent d'une cible claire, d'une présence solide au moment où l'on vous cherche, d'une visite bien menée et d'un suivi régulier de chaque devis.</p>
<p>Pour une vue d'ensemble des sources de clients, lisez aussi <a href="/ressources/trouver-clients-entreprise-de-nettoyage/">comment trouver des clients pour une entreprise de nettoyage</a>.</p>
<p style="margin-top:28px">Vous voulez développer vos contrats de bureaux ? <a href="/premier-echange/?secteur=proprete" class="btn btn-plein" style="margin-left:6px">Demander un premier échange</a></p>
''', "Cibler, être trouvé, visiter, chiffrer, relancer : la démarche qui fait signer des contrats durables."))

PAGES.append(article('publicite-google-entreprise-de-nettoyage', "Publicité Google en nettoyage : ce qu'il faut vérifier",
    "Zone, recherches exclues, campagnes séparées, suivi des demandes : les réglages à vérifier pour la publicité Google d'une entreprise de nettoyage.",
    "Publicité Google pour une entreprise de nettoyage : <em>ce qu'il faut vérifier</em>", '''
<p>Pour une entreprise de nettoyage, les annonces Google ont un grand atout : elles vous placent devant quelqu'un qui cherche un prestataire maintenant. Elles ont aussi un piège : sans réglages précis, une bonne partie du budget part dans des clics qui ne deviendront jamais des clients. Voici ce que nous vérifions en premier.</p>
<h2>1. La zone : là où vous intervenez, pas plus loin</h2>
<p>Ciblez les communes ou le rayon que vous desservez réellement. Vérifiez aussi l'option de ciblage géographique : par défaut, Google peut montrer vos annonces à des personnes simplement « intéressées » par votre zone, même si elles n'y sont pas. Pour une entreprise de nettoyage, il est souvent plus sûr de viser les personnes qui s'y trouvent vraiment.</p>
<h2>2. Les recherches à exclure</h2>
<p>Le mot « nettoyage » attire beaucoup de recherches qui ne vous concernent pas. Les plus fréquentes :</p>
<ul><li>les <strong>offres d'emploi</strong> : « agent d'entretien recrutement », « emploi femme de ménage » ;</li><li>les <strong>conseils et astuces</strong> : « comment nettoyer », « produit pour » ;</li><li>les <strong>prestations que vous ne faites pas</strong> : nettoyage de voiture, de tapis, après sinistre, selon votre cas ;</li><li>les <strong>formations et devenir auto-entrepreneur</strong> dans le nettoyage.</li></ul>
<p>Ajoutez ces mots comme exclusions dès le départ, puis consultez régulièrement la liste des recherches qui ont déclenché vos annonces pour compléter.</p>
<h2>3. Une campagne par type de clientèle</h2>
<p>Un dirigeant qui cherche un contrat d'entretien de bureaux et un particulier qui cherche une aide ménagère ne tapent pas les mêmes mots, ne lisent pas la même page et ne vous rapportent pas la même chose. Séparez au minimum :</p>
<ul><li>les <strong>professionnels</strong> : bureaux, commerces, parties communes ;</li><li>les <strong>particuliers</strong> : ménage régulier, grand ménage, fin de bail ;</li><li>les <strong>prestations ponctuelles</strong> : vitres, fin de chantier, si vous les faites.</li></ul>
<p>Vous pourrez ainsi répartir le budget selon ce que chaque clientèle vous rapporte vraiment.</p>
<h2>4. Une page qui correspond à l'annonce</h2>
<p>Une annonce « nettoyage de bureaux » qui mène à une page d'accueil générale fait perdre des demandes. La personne doit retrouver immédiatement ce qu'elle cherche : la prestation, la zone, ce qui vous distingue, et un moyen simple de demander un devis ou une visite.</p>
<h2>5. Les horaires et le budget</h2>
<p>Si vous ne pouvez pas répondre au téléphone le soir, une annonce qui pousse à appeler à 22 heures gaspille des clics. Adaptez la diffusion à vos heures de réponse, ou privilégiez le formulaire en dehors. Fixez un budget quotidien que vous pouvez tenir plusieurs semaines : il faut du temps et des données pour juger une campagne.</p>
<h2>6. Le suivi des demandes, jusqu'au contrat</h2>
<p>C'est la vérification la plus importante, et la plus souvent oubliée. Votre compte doit au minimum compter les demandes de devis et les appels venus des annonces. Ensuite, notez ce que deviennent ces demandes : sérieuses ou non, devis envoyé, contrat signé. Sans ce suivi, impossible de savoir si la publicité vous rapporte des clients ou seulement des clics. Nous expliquons le calcul dans <a href="/ressources/publicite-google-rapporte-t-elle-des-clients/">votre publicité Google vous rapporte-t-elle des clients ?</a></p>
<h2>7. Un compte à votre nom</h2>
<p>Que vous gériez vos annonces seul ou avec un prestataire, le compte publicitaire doit être à votre nom, et le budget payé directement par vous à Google. Vous gardez ainsi l'historique, les données et la liberté de changer de prestataire.</p>
<h2>En résumé</h2>
<p>Une publicité Google bien réglée pour une entreprise de nettoyage, c'est une zone précise, des recherches inutiles exclues, une campagne par clientèle, une page adaptée, et un suivi qui va jusqu'au contrat signé. Personne ne peut vous garantir un nombre de clients, mais ces vérifications évitent l'essentiel du gaspillage.</p>
<p style="margin-top:28px">Vous voulez faire vérifier vos annonces, ou les lancer sur de bonnes bases ? <a href="/premier-echange/?secteur=proprete" class="btn btn-plein" style="margin-left:6px">Demander un premier échange</a></p>
''', "Zone, exclusions, campagnes séparées, suivi : les réglages qui évitent l'essentiel du gaspillage."))

ICO_ART = {'trouver-clients-entreprise-de-nettoyage': I_NETTOYAGE, 'publicite-google-rapporte-t-elle-des-clients': I_EURO, 'entreprise-absente-google-maps': I_FICHE, 'contrats-entretien-bureaux': I_BUREAU, 'publicite-google-entreprise-de-nettoyage': I_ANNONCE}
cartes = '\n'.join(f'      <a href="/ressources/{s}/" class="rv" style="--i:{k}"><span class="tu-ico">{ICO_ART[s]}</span><h2>{h}</h2><p>{c}</p><span class="lire">Lire l\'article{I_FLECHE}</span></a>' for k, (s, h, c) in enumerate(ARTICLES))
PAGES.append(page('/ressources/', 'Ressources pour trouver des clients sur Google · ViZiBiLi',
    "Des conseils concrets, issus du terrain, pour trouver des clients sur Google et savoir ce que chaque action vous rapporte vraiment.",
f'''
<section>
  <div class="contenu">
    <div class="titre-section">
      <p class="repere">Ressources</p>
      <h1>Des réponses concrètes, <em>issues du terrain.</em></h1>
      <p>Ce que nous apprenons en cherchant nos propres clients, partagé sans jargon.</p>
    </div>
    <div class="ressources">
{cartes}
    </div>
  </div>
</section>
{bande("Une question sur votre propre situation ?", "", "Demander un premier échange")}
'''))

# ---------------------------------------------------------------- LÉGAL
PAGES.append(page('/mentions-legales/', 'Mentions légales · ViZiBiLi', 'Mentions légales du site vizibili.fr.', '''
<section>
  <div class="etroit page-simple">
    <h1>Mentions légales</h1>
    <h2>Éditeur du site</h2>
    <p>Clément VAILLANT-HANNE, entrepreneur individuel (EI), sous le régime de la micro-entreprise<br>Activité exercée sous le nom « ViZiBiLi »<br>SIREN : 822 090 486<br>5 Rue des Sapins, 88390 Darnieulles, France<br>Contact : <a href="mailto:hello@vizibili.fr">hello@vizibili.fr</a><br>Téléphone : <a href="tel:+33621717841">06&nbsp;21&nbsp;71&nbsp;78&nbsp;41</a></p>
    <h2>Directeur de la publication</h2>
    <p>Monsieur Clément VAILLANT-HANNE</p>
    <h2>Hébergement</h2>
    <p>Site hébergé par Cloudflare, Inc., 101 Townsend Street, San Francisco, CA 94107, États-Unis (<a href="https://www.cloudflare.com" rel="noopener">cloudflare.com</a>).</p>
    <h2>Données personnelles</h2>
    <p>Ce site ne dépose aucun cookie de suivi ni aucun cookie publicitaire. Les données transmises par le formulaire de premier échange sont traitées comme décrit dans notre <a href="/confidentialite/">politique de confidentialité</a>.</p>
  </div>
</section>
'''))

PAGES.append(page('/confidentialite/', 'Politique de confidentialité · ViZiBiLi',
    "Comment ViZiBiLi collecte, utilise et protège vos données personnelles, et comment exercer vos droits.", '''
<section>
  <div class="etroit page-simple">
    <h1>Politique de confidentialité</h1>
    <p>Dernière mise à jour : 16 octobre 2026</p>
    <h2>Qui est responsable de vos données ?</h2>
    <p>Clément VAILLANT-HANNE, entrepreneur individuel (EI), activité exercée sous le nom « ViZiBiLi », SIREN 822 090 486, 5 Rue des Sapins, 88390 Darnieulles, France. Contact pour toute question sur vos données : <a href="mailto:hello@vizibili.fr">hello@vizibili.fr</a></p>
    <h2>Quelles données collectons-nous ?</h2>
    <p><strong>Quand vous remplissez le formulaire de premier échange :</strong> votre nom et prénom, le nom de votre entreprise, votre e-mail, votre téléphone si vous l'indiquez, votre secteur d'activité, votre objectif principal, votre site internet si vous l'indiquez et, pour une entreprise de propreté, les prestations et le type de clients que vous choisissez de préciser.</p>
    <p><strong>Avec votre demande, nous enregistrons aussi sa provenance :</strong> la page par laquelle vous êtes arrivé et l'heure d'arrivée, le site qui vous a envoyé vers nous, la source de votre visite (par exemple une recherche Google, une annonce ou un lien), les paramètres de campagne présents dans le lien et, si vous venez d'une annonce Google, l'identifiant technique du clic, qui permet de rattacher votre demande à l'annonce. Ces informations sont conservées dans votre navigateur le temps de votre visite seulement, puis jointes à votre demande si vous l'envoyez. Elles ne permettent pas de vous suivre sur d'autres sites.</p>
    <h2>Pourquoi, et sur quelle base ?</h2>
    <ul>
      <li><strong>Répondre à votre demande et préparer un éventuel accompagnement.</strong> Base légale : les mesures précontractuelles prises à votre demande.</li>
      <li><strong>Savoir quels canaux nous amènent des demandes, et suivre ce qu'elles deviennent.</strong> Base légale : notre intérêt légitime à mesurer l'efficacité de notre propre communication.</li>
    </ul>
    <p>Nous n'utilisons pas vos données pour de la publicité ciblée, et nous ne les vendons ni ne les louons jamais.</p>
    <h2>Qui y a accès ?</h2>
    <p>Uniquement ViZiBiLi. Nos prestataires techniques n'y accèdent que pour faire fonctionner le service :</p>
    <ul>
      <li>Cloudflare, Inc. : hébergement du site, traitement du formulaire, protection contre les envois automatiques ;</li>
      <li>OVHcloud, hébergeur établi en France : acheminement et stockage de l'e-mail de notification.</li>
    </ul>
    <p>Cloudflare est établi aux États-Unis. Les données qui lui sont transmises le sont dans le cadre de sa certification au cadre de protection des données UE et États-Unis (Data Privacy Framework), reconnu par la Commission européenne comme offrant un niveau de protection adéquat. L'accord de traitement des données de Cloudflare prévoit en complément les clauses contractuelles types de la Commission européenne. OVHcloud est établi en France : aucun transfert hors de l'Union européenne pour la messagerie.</p>
    <h2>Combien de temps ?</h2>
    <ul>
      <li><strong>Demande sans suite :</strong> 3 ans après notre dernier échange, puis suppression.</li>
      <li><strong>Client :</strong> pendant la durée de notre collaboration, puis pendant les durées imposées par la loi (comptabilité, contrats).</li>
    </ul>
    <h2>Cookies et mesure d'audience</h2>
    <p>Ce site ne dépose aucun cookie publicitaire ni aucun cookie de suivi. Nous mesurons la fréquentation avec un outil qui fonctionne sans cookie et ne vous identifie pas. [À CONFIRMER À LA MISE EN LIGNE : outil retenu et comportement exact de la protection contre les envois automatiques.]</p>
    <p>Si nous ajoutons un jour un outil qui nécessite votre accord, nous vous le demanderons avant tout dépôt, et cette page sera mise à jour.</p>
    <h2>Vos droits</h2>
    <p>Vous pouvez à tout moment accéder à vos données, les faire corriger ou supprimer, vous opposer à leur utilisation, en limiter l'usage ou les récupérer. Écrivez simplement à <a href="mailto:hello@vizibili.fr">hello@vizibili.fr</a> ; nous vous répondons dans un délai d'un mois au plus.</p>
    <p>Si vous estimez que vos droits ne sont pas respectés, vous pouvez saisir la CNIL (<a href="https://www.cnil.fr" rel="noopener">cnil.fr</a>).</p>
  </div>
</section>
'''))

# 404 (servie par le Worker pour toute adresse inconnue)
p404 = page('/404-gabarit/', 'Page introuvable · ViZiBiLi', "Cette page n'existe pas ou plus.", f'''
<section>
  <div class="centre">
    <div class="casse-404" aria-hidden="true">{ICO_RUPTURE}</div>
    <h1>Cette page n'existe pas, <em>ou plus.</em></h1>
    <p class="sous-titre" style="margin:0 auto 28px">Le site a évolué. Vous trouverez sans doute ce que vous cherchez à partir de l'accueil.</p>
    <div class="actions" style="justify-content:center"><a href="/" class="btn btn-plein">Retour à l'accueil</a><a href="/ressources/" class="btn btn-ligne">Voir les ressources</a></div>
  </div>
</section>
''', indexer=False)
os.replace(os.path.join(RACINE, '404-gabarit', 'index.html'), os.path.join(RACINE, '404.html'))
os.rmdir(os.path.join(RACINE, '404-gabarit'))
# (la 404 n est pas ajoutée à PAGES)

# ---------------------------------------------------------------- SITEMAP, ROBOTS, REDIRECTIONS
INDEXEES = [p for p in PAGES if p != '/premier-echange/merci/']
with open(os.path.join(RACINE, 'sitemap.xml'), 'w', encoding='utf-8') as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    for p in INDEXEES:
        f.write(f'  <url><loc>{SITE}{p}</loc></url>\n')
    f.write('</urlset>\n')
with open(os.path.join(RACINE, 'robots.txt'), 'w', encoding='utf-8') as f:
    f.write(f'User-agent: *\nAllow: /\nDisallow: /premier-echange/merci/\n\nSitemap: {SITE}/sitemap.xml\n')
# Redirections 301 et réponses 410 : gérées par le Worker (src/index.js)

print(f'{len(PAGES)} pages générées + 404 dans {RACINE}')
for p in PAGES:
    print(' ', p)
