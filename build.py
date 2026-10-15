#!/usr/bin/env python3
"""Génère le site statique ViZiBiLi (refonte octobre 2026) dans public/.

Usage :  python3 build.py
Option : TURNSTILE_SITE_KEY=<clé publique> python3 build.py   (active la vérification anti-robots)
Les textes sont ceux validés aux Gates 2 et 3 (PHASE3_TEXTES_LOT1 à LOT3).
"""
import json, os, html

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public')
SITE = 'https://vizibili.fr'
TURNSTILE = os.environ.get('TURNSTILE_SITE_KEY', '').strip()
LOGO = '/assets/logo-vizibili.png'

NAV = [('/methode/', 'Méthode'), ('/entreprises-de-nettoyage/', 'Nettoyage'), ('/offre/', 'Offre'),
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
<link rel="icon" type="image/png" href="/assets/favicon.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="preload" href="/fonts/archivo-800.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/inter-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/styles.css">
<meta property="og:title" content="{esc(titre)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_FR">
<meta property="og:image" content="{SITE}{LOGO}">
<script type="application/ld+json">
{ld_txt}
</script>{turnstile}
<script src="/assets/site.js" defer></script>
</head>
<body>
<a class="evitement" href="#contenu">Aller au contenu</a>
<header class="site-header">
  <a href="/" class="logo" aria-label="ViZiBiLi, accueil"><img src="{LOGO}" alt="ViZiBiLi" width="92" height="92"></a>
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
  <nav aria-label="Liens de pied de page"><a href="/ressources/">Ressources</a><a href="/premier-echange/">Premier échange</a><a href="/mentions-legales/">Mentions légales</a><a href="/confidentialite/">Confidentialité</a></nav>
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


def parcours(etapes, label):
    items = []
    for i, e in enumerate(etapes):
        if i:
            items.append('<li class="fleche" aria-hidden="true">→</li>')
        cls = ' class="fin"' if i == len(etapes) - 1 else ''
        items.append(f'<li{cls}>{e}</li>')
    return f'<ol class="parcours" aria-label="{label}">' + ''.join(items) + '</ol>'


def chemin_casse(etapes, casse, legende):
    """Mini-parcours : où le chemin casse. casse = index du segment rompu, ou None si rien n'est mesuré."""
    n = len(etapes)
    w, y, x0, x1 = 300, 18, 10, 290
    pas = (x1 - x0) / (n - 1)
    xs = [x0 + i * pas for i in range(n)]
    seg = []
    for i in range(n - 1):
        a, b = xs[i] + 6, xs[i + 1] - 6
        if casse is None:
            seg.append(f'<line class="flou" x1="{a:.1f}" y1="{y}" x2="{b:.1f}" y2="{y}"/>')
        elif i == casse:
            m = (a + b) / 2
            seg.append(f'<circle class="halo" cx="{m:.1f}" cy="{y}" r="13"/>'
                       f'<line class="rompu" x1="{a:.1f}" y1="{y}" x2="{m - 5:.1f}" y2="{y}"/>'
                       f'<polyline class="eclair" points="{m - 5:.1f},{y} {m - 1:.1f},{y - 7} {m + 2:.1f},{y + 7} {m + 5:.1f},{y}"/>'
                       f'<line class="perdu" x1="{m + 5:.1f}" y1="{y}" x2="{b:.1f}" y2="{y}"/>')
        elif i > casse:
            seg.append(f'<line class="perdu" x1="{a:.1f}" y1="{y}" x2="{b:.1f}" y2="{y}"/>')
        else:
            seg.append(f'<line class="ok" x1="{a:.1f}" y1="{y}" x2="{b:.1f}" y2="{y}"/>')
    pts = []
    for i, x in enumerate(xs):
        etat = 'flou' if casse is None else ('ok' if i <= casse else 'perdu')
        pts.append(f'<circle class="pt {etat}" cx="{x:.1f}" cy="{y}" r="5"/>')
    lab = (f'<text x="{x0}" y="44" class="lab">{etapes[0]}</text>'
           f'<text x="{x1}" y="44" class="lab" text-anchor="end">{etapes[-1]}</text>')
    svg = f'<svg class="chemin-casse" viewBox="0 0 {w} 50" aria-hidden="true" focusable="false">{"".join(seg)}{"".join(pts)}{lab}</svg>'
    return f'<div class="signal">{svg}<p class="ou">{legende}</p></div>'


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

PAGES.append(page('/', 'ViZiBiLi · Acquisition de clients sur Google, mesurée',
    "ViZiBiLi aide les entreprises locales à transformer les recherches Google en demandes sérieuses, et à suivre les résultats jusqu'au contrat signé.",
f'''
<section>
  <div class="contenu heros">
    <div>
      <p class="repere">Acquisition et croissance locale</p>
      <h1>Votre visibilité sur Google doit servir votre développement commercial.</h1>
      <p class="sous-titre">ViZiBiLi accompagne les entreprises dans la construction de parcours d'acquisition mesurables : attirer les bonnes recherches, transformer les visites en demandes sérieuses et mieux suivre les résultats commerciaux.</p>
      <div class="actions">
        <a href="/premier-echange/" class="btn btn-plein">Demander un premier échange</a>
        <a href="/methode/" class="btn btn-ligne">Découvrir notre méthode</a>
      </div>
      <p class="reassurance">Entreprises locales de tous secteurs, avec une spécialité : la propreté. Basés dans les Vosges.</p>
    </div>
    <div class="itineraire" role="img" aria-label="Le chemin que nous suivons : recherche Google, annonce ou fiche Google, page dédiée, demande puis tri, devis, client signé. Chaque étape est mesurée.">
      <p class="it-titre">Le chemin que nous suivons</p>
      <ol class="it-etapes" aria-hidden="true">
        <li><span class="it-pin"></span><span class="it-nom">Recherche Google</span><span class="it-mesure">ce qui a été tapé</span></li>
        <li><span class="it-pin"></span><span class="it-nom">Annonce ou fiche Google</span><span class="it-mesure">les clics</span></li>
        <li><span class="it-pin"></span><span class="it-nom">Page dédiée</span><span class="it-mesure">les visites</span></li>
        <li><span class="it-pin"></span><span class="it-nom">Demande, puis tri</span><span class="it-mesure">les demandes sérieuses</span></li>
        <li><span class="it-pin"></span><span class="it-nom">Devis</span><span class="it-mesure">les devis émis</span></li>
        <li class="it-fin"><span class="it-pin"></span><span class="it-nom">Client signé</span><span class="it-mesure">ce qu'il rapporte</span></li>
      </ol>
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
    <div class="constat">
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
    <div class="grille-4">
      <div class="pilier"><h3>Attirer les bonnes recherches</h3><p>Des annonces Google ciblées sur ce que vos clients tapent vraiment, dans votre zone d'intervention, complétées par votre fiche Google et votre site.</p></div>
      <div class="pilier"><h3>Transformer les visites en demandes</h3><p>Une page claire pour chaque offre, un message qui répond aux vraies questions, un formulaire simple qui vous dit qui vous contacte et pourquoi.</p></div>
      <div class="pilier"><h3>Mesurer ce qui se passe vraiment</h3><p>Nous suivons d'où viennent vos demandes, si elles sont sérieuses, et ce qu'elles deviennent. Vous voyez la différence entre un clic, une demande et un client.</p></div>
      <div class="pilier"><h3>Améliorer selon les résultats</h3><p>Nous corrigeons une chose à la fois, quand les résultats le justifient, et nous vous expliquons pourquoi. Votre budget reste sous contrôle.</p></div>
    </div>
  </div>
</section>

<section>
  <div class="contenu bloc-encre encre">
    <div class="disposition">
      <div>
        <p class="repere">Notre spécialité</p>
        <h2>Une connaissance de terrain particulière : les entreprises de nettoyage.</h2>
        <p>Notre fondateur dirige lui-même une entreprise de nettoyage. Les contrats d'entretien de bureaux, le ménage à domicile, le lavage de vitres, les demandes ponctuelles qui ne débouchent sur rien, les devis à relancer : nous connaissons ces réalités de l'intérieur.</p>
        <p style="margin-top:12px">C'est sur ce terrain que notre méthode est née et qu'elle continue de s'améliorer. Si vous dirigez une entreprise de propreté, nous parlons le même langage.</p>
      </div>
      <a href="/entreprises-de-nettoyage/" class="btn btn-plein">Découvrir notre approche pour les entreprises de nettoyage</a>
    </div>
  </div>
</section>

<section class="fond-chaud">
  <div class="contenu">
    <div class="titre-section"><h2>Des résultats racontés honnêtement.</h2></div>
    <div class="preuves">
      <div class="preuve">
        <span class="etiquette">Visibilité locale · missions terminées</span>
        <p>Quatre entreprises accompagnées sur leur présence locale, dont celle de notre fondateur : une entreprise de nettoyage, deux gîtes et une boutique de cadeaux, dans les Vosges.</p>
        <p>Leur point commun : une présence locale remise en ordre, et des clients qui repartent propriétaires de tout ce qui a été construit.</p>
        <a href="/cas-clients/" class="btn btn-ligne">Voir les cas clients</a>
      </div>
      <div class="preuve en-cours">
        <span class="etiquette en-cours">Campagnes Google · étude en cours</span>
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
    <ol class="etapes-contact">
      <li><span class="ec-statut">Offert</span><h3>Premier échange</h3><p>15 à 30 minutes pour comprendre votre situation et vous dire honnêtement si nous pouvons vous aider.</p></li>
      <li><span class="ec-statut">Prestation distincte</span><h3>Diagnostic approfondi</h3><p>Si c'est utile : analyse de l'existant, blocages, opportunités et feuille de route. Son contenu et son prix vous sont donnés par écrit, avant de commencer.</p></li>
      <li><span class="ec-statut">Sur proposition</span><h3>Accompagnement</h3><p>Une proposition séparée : périmètre, honoraires, et budget publicitaire payé directement par vous à Google.</p></li>
    </ol>
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

PAGES.append(page('/entreprises-de-nettoyage/', 'Trouver des clients pour une entreprise de nettoyage · ViZiBiLi',
    "Bureaux, ménage à domicile, vitres : nous aidons les entreprises de nettoyage à obtenir des demandes sérieuses et à savoir ce qu'elles leur rapportent.",
f'''
<section>
  <div class="contenu heros-seul">
    <p class="repere">Pour les entreprises de nettoyage et de propreté</p>
    <h1>Développez votre entreprise de nettoyage avec des demandes que vous pouvez <em>mesurer.</em></h1>
    <p class="sous-titre">Plus de contrats qui vous correspondent, moins de demandes inutiles, et une vision claire de ce que chaque nouveau client vous coûte et vous rapporte.</p>
    <div class="actions"><a href="/premier-echange/?secteur=proprete" class="btn btn-plein">Parlons de votre entreprise de nettoyage</a><a href="#pourquoi-la-signature" class="btn btn-ligne">Pourquoi suivre jusqu'à la signature</a></div>
    <p class="reassurance">Partout en France, à distance. Premier échange offert.</p>
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
    <div class="constat">
      <p>Ce ne sont pas des fatalités du métier. Ce sont des signaux que le chemin entre la recherche et le contrat n'est pas piloté.</p>
      <a href="/premier-echange/?secteur=proprete" class="btn btn-plein">Parlons de votre entreprise de nettoyage</a>
    </div>
  </div>
</section>

<section>
  <div class="contenu">
    <div class="titre-section">
      <h2>Notre méthode est née dans une entreprise de nettoyage.</h2>
      <p>Notre fondateur dirige une entreprise de nettoyage dans les Vosges : bureaux, commerces, vitres, ménage à domicile, grands ménages. Il vit chaque semaine ce que vous vivez : les devis à chiffrer, les visites sur place, les clients à fidéliser, les demandes qui font perdre du temps.</p>
      <p style="margin-top:12px">C'est là que notre méthode a été construite, testée et corrigée. Nous savons qu'une demande n'a pas la même valeur selon la prestation, la fréquence et la distance, et que votre temps est votre ressource la plus rare.</p>
    </div>
  </div>
</section>

<section class="fond-chaud">
  <div class="contenu">
    <div class="titre-section"><h2>Cinq sujets, cinq approches différentes.</h2><p>Chaque activité a ses recherches, ses clients et sa valeur. Nous les séparons quand leur valeur diffère et que le volume de recherches le permet, sans éparpiller un petit budget.</p></div>
    <div class="grille-3">
      <div class="pilier"><h3>Entretien de bureaux et locaux professionnels</h3><p>Cibler les entreprises qui cherchent un prestataire régulier, et trier les demandes selon la taille des locaux et la fréquence souhaitée.</p></div>
      <div class="pilier"><h3>Nettoyage de vitres</h3><p>Viser les particuliers comme les commerces avec vitrine, sur des recherches précises, pour des demandes faciles à chiffrer.</p></div>
      <div class="pilier"><h3>Ménage à domicile</h3><p>Toucher les particuliers de votre zone au bon moment, et distinguer les demandes régulières des demandes ponctuelles.</p></div>
      <div class="pilier"><h3>Acquisition de contrats récurrents</h3><p>Faire passer en priorité ce qui construit votre chiffre d'affaires dans la durée, plutôt que le volume de demandes.</p></div>
      <div class="pilier"><h3>Gestion des demandes et des devis</h3><p>Répondre vite, qualifier avant de se déplacer, relancer les devis : c'est souvent là que se perdent les contrats déjà gagnés à moitié.</p></div>
    </div>
  </div>
</section>

<section id="pourquoi-la-signature">
  <div class="contenu">
    <div class="titre-section">
      <h2>Pourquoi le suivi jusqu'à la signature compte autant dans la propreté.</h2>
      <p>Dans votre métier, deux demandes peuvent avoir une valeur sans commune mesure. Les compter de la même façon fausse toutes les décisions.</p>
    </div>
    <div class="comparatif">
      <div class="cmp-col"><p class="cmp-titre">Une prestation ponctuelle</p><p class="cmp-valeur">1 facture</p><p>Un grand ménage, un lavage de vitres unique. Utile, mais terminé une fois réalisé.</p></div>
      <div class="cmp-col cmp-fort"><p class="cmp-titre">Un contrat récurrent</p><p class="cmp-valeur">12 factures par an</p><p>L'entretien mensuel de bureaux. Il se renouvelle, et sa valeur se compte sur l'année.</p></div>
    </div>
    <p class="exemple-fictif"><strong>Exemple fictif, pour illustrer :</strong> un grand ménage facturé 300 € et un contrat de bureaux à 300 € par mois arrivent tous deux comme « une demande ». Sur un an, le second représente 3 600 €. Un suivi qui s'arrête au nombre de demandes ne voit pas cette différence.</p>
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
<section>
  <div class="contenu heros-seul">
    <p class="repere">Notre méthode</p>
    <h1>La stratégie doit s'adapter à l'entreprise. Pas l'entreprise à une recette marketing.</h1>
    <p class="sous-titre">Nous suivons une méthode en huit étapes, qui part de votre réalité, ne lance rien sans contrôle et ne change rien sans raison mesurée.</p>
    <div class="actions"><a href="/premier-echange/" class="btn btn-plein">Demander un premier échange</a></div>
  </div>
</section>

<section class="fond-chaud">
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
MODS = [
    ("Diagnostic d'acquisition", "Nous analysons votre situation : vos clients actuels, vos canaux, vos dépenses et ce qui bloque. Vous repartez avec des priorités claires, même si vous décidez de continuer seul. Prestation distincte du premier échange offert, au prix communiqué par écrit avant de commencer."),
    ("Construction du parcours", "Nous préparons et lançons ce qui manque : annonces Google, page dédiée, suivi des demandes, et si besoin votre fiche Google ou votre site."),
    ("Pilotage et amélioration", "Nous surveillons les dépenses, trions les demandes avec vous et corrigeons une chose à la fois. Vous recevez un point régulier, clair et honnête."),
    ("Suivi commercial", "Nous relions les demandes à vos devis et à vos contrats signés, avec les outils que vous utilisez déjà. C'est là que vous voyez, autant que vos données le permettent, ce que vous coûte et vous rapporte un nouveau client."),
]
mods_html = '\n'.join(f'      <li><h3>{t}</h3><p>{d}</p></li>' for t, d in MODS)
svc_o = [{"@type": "Service", "name": t, "description": d, "provider": {"@id": SITE + "/#organisation"}} for t, d in MODS]
PAGES.append(page('/offre/', 'Notre accompagnement pour trouver des clients · ViZiBiLi',
    "Annonces Google, page dédiée, suivi des demandes jusqu'au devis signé : un accompagnement en quatre étapes, adapté à votre entreprise, partout en France.",
f'''
<section>
  <div class="contenu heros-seul">
    <p class="repere">Notre accompagnement</p>
    <h1>Un accompagnement construit autour d'un seul objectif : des clients qui vous correspondent.</h1>
    <p class="sous-titre">Nous ne vendons pas un pack identique pour tous. Nous assemblons ce dont votre entreprise a besoin, dans le bon ordre, et nous mesurons ce que cela vous rapporte.</p>
    <div class="actions"><a href="/premier-echange/" class="btn btn-plein">Demander un premier échange</a></div>
  </div>
</section>

<section class="fond-chaud">
  <div class="contenu">
    <div class="titre-section"><h2>Les leviers, et la place de chacun.</h2></div>
    <div class="grille-4">
      <div class="pilier"><h3>Les annonces Google</h3><p>Pour apparaître au moment précis où quelqu'un cherche votre service, dans votre zone. C'est le moyen d'être visible le plus vite, à condition d'être bien préparé et bien suivi. Un clic ne prouve rien : seules les demandes et les contrats comptent.</p></div>
      <div class="pilier"><h3>Une page dédiée à votre offre</h3><p>Pour que la personne qui clique trouve immédiatement ce qu'elle cherche, et puisse vous écrire facilement.</p></div>
      <div class="pilier"><h3>Le suivi des demandes</h3><p>Pour savoir d'où viennent vos demandes, si elles sont sérieuses et ce qu'elles deviennent. Sans ce suivi, personne ne peut dire si la publicité est rentable.</p></div>
      <div class="pilier"><h3>Votre fiche Google et votre site</h3><p>Ils restent des appuis essentiels, et nous les améliorons quand c'est nécessaire. Mais ils ne sont qu'une partie du chemin.</p></div>
    </div>
  </div>
</section>

<section>
  <div class="contenu">
    <div class="titre-section"><h2>Quatre étapes, à votre rythme.</h2></div>
    <ol class="modules">
{mods_html}
    </ol>
    <a href="/methode/" class="lien-suite">En savoir plus sur notre méthode</a>
  </div>
</section>

<section class="fond-chaud">
  <div class="contenu grille-2" style="align-items:start">
    <div>
      <h2>Ce que vous payez, et à qui.</h2>
      <p style="margin-top:16px"><strong>Le budget publicitaire</strong> est payé directement par vous à Google, sur votre propre compte. Il ne passe jamais par nous, et vous le voyez en temps réel.</p>
      <p style="margin-top:12px"><strong>Notre accompagnement</strong> est facturé séparément. Son prix dépend de votre situation et des étapes retenues : il vous est donné par écrit, avant de commencer, à l'issue du diagnostic.</p>
      <p style="margin-top:12px">Pas de frais cachés, pas de pourcentage prélevé sur votre budget publicitaire.</p>
    </div>
    <div>
      <h2>Tout ce que nous construisons vous appartient.</h2>
      <p style="margin-top:16px">Compte publicitaire, page dédiée, site, fiche Google, données de suivi : tout est à votre nom dès le premier jour. Si vous décidez d'arrêter, vous repartez avec l'ensemble, prêt à fonctionner.</p>
    </div>
  </div>
</section>

<section>
  <div class="contenu">
    <div class="titre-section"><h2>Pour qui nous travaillons.</h2></div>
    <div class="grille-2">
      <div class="carte"><strong>Les entreprises de nettoyage et de propreté</strong><p>Partout en France, à distance. C'est notre spécialité. <a href="/entreprises-de-nettoyage/">Notre approche pour les entreprises de nettoyage</a></p></div>
      <div class="carte"><strong>Les entreprises locales de tous secteurs</strong><p>Artisans, commerçants, indépendants, professions libérales et services, partout en France à distance, et sur place dans les Vosges. Pour celles qui veulent des demandes sérieuses plutôt que de simples visites.</p></div>
    </div>
  </div>
</section>
{bande("Commençons par un premier échange.", "Offert, de 15 à 30 minutes, pour savoir si nous pouvons vraiment vous aider.", "Demander un premier échange")}
''', actif='/offre/', jsonld=svc_o))

# ---------------------------------------------------------------- CAS CLIENTS
def cas(etiq, nom, lieu, depart, fait, change, suite=''):
    return f'''
    <article class="cas">
      <span class="etiquette">{etiq}</span>
      <h2>{nom}</h2>
      <p class="lieu">{lieu}</p>
      <div class="blocs">
        <div><h3>Point de départ</h3><p>{depart}</p></div>
        <div><h3>Ce que nous avons fait</h3><p>{fait}</p></div>
        <div><h3>Ce qui a changé</h3><p>{change}</p></div>
      </div>{suite}
    </article>'''

TEMOIN = '\n      <!-- TÉMOIGNAGE : à publier uniquement après accord écrit (SOP_PREUVE)\n      <blockquote>{q}<cite>{a}</cite></blockquote>\n      -->'
PAGES.append(page('/cas-clients/', 'Cas clients racontés honnêtement · ViZiBiLi',
    "Quatre entreprises accompagnées, dont celle de notre fondateur : ce qui a été mis en place et ce qui a changé, raconté sans chiffres impossibles à vérifier.",
f'''
<section>
  <div class="contenu heros-seul">
    <p class="repere">Cas clients</p>
    <h1>Des histoires vraies, racontées honnêtement.</h1>
    <p class="sous-titre">Vous ne trouverez pas de pourcentages spectaculaires sur cette page, et c'est un choix. Un chiffre sans date, sans source et sans contexte ne prouve rien. Nous republierons nos résultats chiffrés quand chacun pourra être daté, sourcé et validé par le client concerné.</p>
    <p class="sous-titre" style="margin-bottom:0">En attendant, voici ce que nous avons fait, et ce que nos clients en disent.</p>
  </div>
</section>
<section class="fond-chaud">
  <div class="contenu">
{cas("Fiche Google et lancement · Entreprise de notre fondateur", "Limpid", "Entreprise de nettoyage · Darnieulles (88)",
     "Limpid est l'entreprise de nettoyage de notre fondateur. À son lancement, sa fiche Google était presque invisible sur Maps : peu d'avis, aucune preuve visible, aucun contact.",
     "Mise en conformité complète de la fiche Google : catégories, zone d'intervention, éléments de confiance. Pour le lancement, une annonce payante de Google dédiée aux services locaux. Puis une démarche régulière pour recueillir des avis authentiques auprès des clients.",
     "Les premières demandes sérieuses sont arrivées de clients proches, dans la zone d'intervention, et l'entreprise a signé ses premiers clients.",
     '\n      <p class="pourquoi"><strong>Pourquoi commencer par ce cas.</strong> Avant de proposer cette méthode, notre fondateur l\'a appliquée à sa propre entreprise, avec son propre argent. C\'est aussi sur Limpid qu\'est testée, depuis septembre 2026, notre méthode de campagnes Google. Ce test fera l\'objet d\'un cas séparé, publié seulement quand ses résultats seront mesurés. <a href="/methode/">Découvrir notre méthode</a></p>')}
{cas("Site internet et fiche Google", "Un Cadeau Une Histoire", "Boutique de cadeaux personnalisés · Darnieulles (88)",
     "Une boutique appréciée de sa clientèle, mais une présence en ligne qui ne reflétait ni la qualité de son travail ni la richesse de ses créations.",
     "Création d'un nouveau site, rafraîchissement complet de la fiche Google, et des conseils concrets pour entretenir cette présence dans la durée.",
     "Selon sa gérante, la boutique est désormais plus visible, plus attractive, et davantage recommandée par ses clients.",
     TEMOIN.format(q="« Le travail de ViZiBiLi a véritablement transformé notre présence locale. Grâce au nouveau site et à la fiche Google rafraîchit, nous sommes désormais visibles, attractifs et recommandés par nos clients locaux, de plus, tout au long de notre collaboration, Clément le gérant de l'agence nous a accompagné et donné des conseils utiles à appliquer pour maintenir la qualité de notre visibilité. Une vraie réussite ! »", a="Annie, gérante"))}
{cas("Fiche Google", "Gîte Chez Paul", "Location de gîte touristique · Épinal (88)",
     "Un gîte bien tenu, mais une fiche Google qui ne le mettait pas en valeur auprès des voyageurs.",
     "Optimisation complète de la fiche Google et mise en avant des avis clients.",
     "Selon sa propriétaire, la fiche est devenue un vrai levier de réservations.",
     TEMOIN.format(q="« ViZiBiLi a su transformer notre fiche Google en un vrai levier de réservations. Le travail est sérieux, structuré et orienté résultats. On voit clairement la différence. »", a="La propriétaire"))}
{cas("Fiche Google", "Gîte de la Marie", "Location de gîte touristique · Épinal (88)",
     "Une fiche Google qui n'était pas à la hauteur du gîte qu'elle présentait.",
     "Remise en cohérence et optimisation de la fiche Google, avec une présentation claire et structurée.",
     "Selon sa propriétaire, le gîte a gagné en visibilité, en cohérence et en réservations.",
     TEMOIN.format(q="« Grâce à l'accompagnement de ViZiBiLi, notre fiche Google est enfin à la hauteur de notre gîte. Nous avons gagné en visibilité, en cohérence et en réservations. Tout est clair, structuré et surtout efficace. »", a="La propriétaire"))}
  </div>
</section>
{bande("Votre entreprise pourrait être la prochaine histoire.", "", "Demander un premier échange")}
''', actif='/cas-clients/'))

# ---------------------------------------------------------------- À PROPOS
PAGES.append(page('/a-propos/', 'À propos de ViZiBiLi, née du terrain · Vosges',
    "ViZiBiLi est née dans une entreprise de nettoyage des Vosges. Une structure à taille humaine, où vous échangez toujours directement avec son fondateur.",
f'''
<section>
  <div class="contenu heros-seul">
    <p class="repere">À propos</p>
    <h1>Derrière ViZiBiLi, un dirigeant qui cherche lui aussi ses clients.</h1>
    <p class="sous-titre">ViZiBiLi n'a pas été imaginée dans une agence. Elle est née dans une entreprise de nettoyage des Vosges, face à une question très concrète : comment trouver des clients sérieux sans gaspiller ni temps ni argent ?</p>
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
    <div class="grille-3">
      <div class="pilier"><h3>Dire la vérité, même quand elle est moins vendeuse.</h3><p>Nous ne publions pas un résultat avant de l'avoir mesuré, y compris les nôtres.</p></div>
      <div class="pilier"><h3>Mesurer avant de promettre.</h3><p>Une décision s'appuie sur ce que disent vos demandes, vos devis et vos contrats, pas sur une impression.</p></div>
      <div class="pilier"><h3>Vous laisser propriétaire de tout.</h3><p>Compte publicitaire, site, fiche Google, données : tout est à votre nom, dès le premier jour.</p></div>
    </div>
  </div>
</section>
<section class="fond-chaud">
  <div class="contenu titre-section">
    <h2>Vous parlez toujours à la même personne.</h2>
    <p>ViZiBiLi est une structure à taille humaine. Vous échangez directement avec son fondateur, du premier échange au suivi de vos résultats. Pas d'intermédiaire, pas de dossier qui passe de main en main.</p>
    <p style="margin-top:12px">Nous accompagnons les entreprises de nettoyage partout en France, à distance, et les entreprises locales des Vosges.</p>
  </div>
</section>
{bande("Faisons connaissance.", "Le premier échange est offert. Nous vous dirons franchement si nous pouvons vous aider.", "Demander un premier échange")}
''', actif='/a-propos/', jsonld=[{"@type": "AboutPage", "url": SITE + "/a-propos/"}]))

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
<section>
  <div class="contenu heros-seul">
    <p class="repere">Premier échange et diagnostic</p>
    <h1>Commençons par un premier échange. Offert, et sans détour.</h1>
    <p class="sous-titre">Ce qui est offert, ce qui est payant et ce qui vous engage sont clairement séparés. Vous savez toujours où vous en êtes.</p>
  </div>
</section>

<section class="fond-chaud" style="padding-top:56px">
  <div class="contenu">
    <ol class="etapes-contact">
      <li id="premier-echange"><span class="ec-statut">Offert</span><h3>Premier échange</h3><p><strong>15 à 30 minutes</strong>, par téléphone ou en visio. Nous cherchons à comprendre votre situation et à déterminer si un accompagnement est réellement pertinent. Si ce n'est pas le cas, nous vous le disons.</p></li>
      <li id="diagnostic"><span class="ec-statut">Prestation distincte</span><h3>Diagnostic approfondi</h3><p>Analyse de l'existant, identification des blocages, étude des opportunités, priorisation, et une <strong>feuille de route exploitable</strong>, même si vous continuez seul. Son contenu et son prix vous sont donnés par écrit, avant de commencer.</p></li>
      <li id="ensuite"><span class="ec-statut">Sur proposition</span><h3>Et ensuite ?</h3><p>Si un accompagnement a du sens, il fait l'objet d'une <strong>proposition séparée</strong> : périmètre, honoraires, et budget publicitaire payé directement par vous à Google, sur votre propre compte.</p></li>
    </ol>
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
'''
<section>
  <div class="centre">
    <div class="pin-grand" aria-hidden="true"></div>
    <h1>Votre demande est bien reçue.</h1>
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
    ARTICLES.append((slug, h1, chapo))
    art_ld = {"@type": "Article", "headline": h1, "description": desc, "inLanguage": "fr-FR",
              "author": {"@id": SITE + "/#organisation"}, "publisher": {"@id": SITE + "/#organisation"},
              "mainEntityOfPage": SITE + f"/ressources/{slug}/"}
    return page(f'/ressources/{slug}/', titre, desc, f'''
<section>
  <article class="etroit article">
    <p class="fil"><a href="/ressources/">Ressources</a></p>
    <h1>{h1}</h1>
{corps.strip()}
  </article>
</section>''', jsonld=[art_ld])

PAGES.append(article('trouver-clients-entreprise-de-nettoyage', 'Comment trouver des clients pour une entreprise de nettoyage',
    "Contrats de bureaux, ménage à domicile, vitres : les sources de clients qui fonctionnent vraiment pour une entreprise de nettoyage, et comment les piloter.",
    "Comment trouver des clients pour une entreprise de nettoyage ?", '''
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
<p>Pour les contrats de bureaux et de commerces, attendre que le client vous trouve est souvent trop lent. Privilégiez les entreprises dirigées par des indépendants, à qui vous pouvez parler directement : la décision est plus rapide qu'auprès d'une enseigne ou d'un grand compte, où tout se décide au siège.</p>
<h2>5. Utilisez les annonces Google, mais avec méthode</h2>
<p>Les annonces Google vous placent devant quelqu'un qui cherche votre service maintenant. C'est puissant, à condition de :</p>
<ul><li>séparer les campagnes par type de clientèle, par exemple professionnels d'un côté et particuliers de l'autre ;</li><li>exclure les recherches qui ne vous concernent pas, comme les offres d'emploi ou les prestations que vous ne faites pas ;</li><li>mesurer les demandes et ce qu'elles deviennent, pas seulement les clics.</li></ul>
<h2>6. Mesurez ce que chaque source vous rapporte</h2>
<p>C'est l'étape que presque tout le monde oublie. Pour chaque nouveau client, notez d'où il vient. Au bout de quelques mois, vous saurez quelle source vous apporte des contrats durables, et laquelle ne vous apporte que des devis sans suite.</p>
<h2>En résumé</h2>
<p>Les entreprises de nettoyage qui se développent ne sont pas forcément celles qui reçoivent le plus de demandes. Ce sont celles qui savent quels clients elles veulent, d'où ils viennent, et ce qu'ils leur rapportent.</p>
<p style="margin-top:28px">Vous voulez savoir par où commencer pour votre entreprise ? <a href="/premier-echange/?secteur=proprete" class="btn btn-plein" style="margin-left:6px">Demander un premier échange</a></p>
''', "Les sources de clients qui fonctionnent vraiment, et comment savoir lesquelles vous rapportent."))

PAGES.append(article('publicite-google-rapporte-t-elle-des-clients', 'Votre publicité Google vous rapporte-t-elle des clients ?',
    "Clics, demandes, devis, contrats : comment savoir si votre publicité Google vous rapporte vraiment des clients, et ce qu'elle vous coûte par client signé.",
    "Votre publicité Google vous rapporte-t-elle vraiment des clients ?", '''
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
    "Pourquoi votre entreprise n'apparaît pas sur Google Maps ?", '''
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

cartes = '\n'.join(f'      <a href="/ressources/{s}/"><h2>{h}</h2><p>{c}</p></a>' for s, h, c in ARTICLES)
PAGES.append(page('/ressources/', 'Ressources pour trouver des clients sur Google · ViZiBiLi',
    "Des conseils concrets, issus du terrain, pour trouver des clients sur Google et savoir ce que chaque action vous rapporte vraiment.",
f'''
<section>
  <div class="contenu">
    <div class="titre-section">
      <p class="repere">Ressources</p>
      <h1>Des réponses concrètes, issues du terrain.</h1>
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
    <p>ViZiBiLi<br>[FORME JURIDIQUE : à compléter avant publication]<br>SIREN : 822 090 486<br>5 Rue des Sapins, 88390 Darnieulles, France<br>Contact : <a href="mailto:hello@vizibili.fr">hello@vizibili.fr</a><br>[TÉLÉPHONE : point légal ouvert, à confirmer avec un juriste ou l'expert-comptable avant publication]</p>
    <h2>Directeur de la publication</h2>
    <p>Monsieur Clément Vaillant-Hanne</p>
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
    <p>Dernière mise à jour : [DATE DE PUBLICATION]</p>
    <h2>Qui est responsable de vos données ?</h2>
    <p>ViZiBiLi, SIREN 822 090 486, 5 Rue des Sapins, 88390 Darnieulles, France. Contact pour toute question sur vos données : <a href="mailto:hello@vizibili.fr">hello@vizibili.fr</a></p>
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
      <li>[HÉBERGEUR DE MESSAGERIE : nom et pays à préciser avant publication] : acheminement et stockage de l'e-mail de notification.</li>
    </ul>
    <p>Cloudflare est établi aux États-Unis. [GARANTIES DE TRANSFERT : à préciser avant publication, par exemple l'adhésion au cadre de protection des données UE et États-Unis ou des clauses contractuelles types, à vérifier pour chaque prestataire.]</p>
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
p404 = page('/404-gabarit/', 'Page introuvable · ViZiBiLi', "Cette page n'existe pas ou plus.", '''
<section>
  <div class="centre">
    <div class="pin-grand" aria-hidden="true"></div>
    <h1>Cette page n'existe pas, ou plus.</h1>
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
