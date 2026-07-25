# Compa — Roadmap

> La direction produit et les garde-fous complets sont dans
> [THE_COMPA_MANIFESTO.md](THE_COMPA_MANIFESTO.md) et [mvp.md](mvp.md).
> Ce document liste uniquement les versions et ce que chacune ajoute.

## Vision long-terme

Compa a deux temps, assumés dès maintenant :

1. **V1 → V3 : le socle.** Un compagnon purement vivant, émotionnel, sans
   aucune donnée ni fonction utile. C'est ce qui rend l'attachement possible.
2. **V4 et après : le projet communautaire.** Compa s'ouvre en open source
   (licence MIT) et peut devenir réellement utile, via des extensions
   optionnelles ("domain packs") — jamais en modifiant le socle.

Le socle ne change jamais de forme pour accueillir de l'utilité. L'utilité
vit uniquement dans les extensions, jamais dans Tux de base.

---

## V1 — LIVE ✅ *(validée)*

Tux vivant sur le bureau Linux : transparence réelle, drag and drop, clic/
double-clic, 5 personnalités, réglages complets, autostart. Zéro donnée,
zéro fonction utile — cf. critères de sortie dans [mvp.md](mvp.md).

## V1.1 — Distribution

- Exécutables : AppImage en priorité, `.deb` en complément
- Repo public sous licence MIT
- Matrice de compatibilité validée : Ubuntu/GNOME, Fedora/GNOME,
  Mint/Cinnamon, KDE Plasma (X11 + XWayland)
- Vrai multi-écran
- Vidéo démo < 20s

## V2 — Réactivité au bureau

- Événements légers (notification, nouvelle fenêtre, heure tardive) traduits
  en émotion, jamais en donnée affichée
- Son ambiant discret (saut, bâillement)
- Mémoire/continuité : Tux s'habitue aux horaires de l'utilisateur, petits
  rituels (ex. anniversaire d'installation)
- Cycles jour/nuit et saisons

## V3 — Multiplateforme

- Adapters Windows et macOS (le cœur portable reste identique, seul
  l'adapter desktop change)

## V4 — Domain packs (début du volet communautaire)

- 2-3 packs officiels créés en interne (ex. Coder, Fitness, Focus) pour
  valider le concept avant toute ouverture externe
- Un domain pack change le vocabulaire, les déclencheurs d'émotion et les
  accessoires de Tux — jamais un panneau, un graphique ou une liste
- La permissivité exacte (ce qu'un pack a le droit d'afficher comme
  "bonus" d'information) est **à formaliser avant de commencer cette
  version**, pas avant — cf. note dans le manifeste

## V5 — Focus Companion

- Le volet productivité, exprimé uniquement via l'humeur et le comportement
  de Tux — jamais de chiffres, barres de progression ou listes affichées en
  continu
- Connexion légère en lecture seule à un calendrier/todo externe

## Post-V5 — Écosystème ouvert

- API de création de domain packs ouverte à la communauté, avec garde-fous
  techniques (pas d'accès à un canvas de texte libre, uniquement des hooks
  émotion/événement)
- Présence sociale optionnelle entre amis (piste lointaine, non engagée)
