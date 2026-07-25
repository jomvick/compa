# Compa

> Bring Linux to Life.

Un petit Tux animé, discret et interactif, qui vit au-dessus du bureau Linux.

La direction produit, les limites de la V1 et les critères de sortie sont dans
[le MVP](mvp.md). La vision long-terme et les règles du projet sont dans
[le manifeste](THE_COMPA_MANIFESTO.md). Les versions à venir sont listées dans
[la roadmap](ROADMAP.md).

## Licence

Compa est open source sous licence [MIT](LICENSE).

## Prérequis Système & Dépendances

Compa utilise **GTK3 (PyGObject)** et **Cairo** pour offrir une transparence par pixel à 100% sans bordure sur les bureaux Linux (X11 et Wayland).

### 1. Installation des paquets système

Selon votre distribution, installez les dépendances système requises (GTK3, PyGObject, Cairo, Pillow) :

* **Ubuntu / Debian / Mint** :
  ```bash
  sudo apt update
  sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-pil
  ```

* **Fedora / RHEL** :
  ```bash
  sudo dnf install python3-gobject gtk3 python3-pillow
  ```

* **Arch Linux / Manjaro** :
  ```bash
  sudo pacman -S python-gobject gtk3 python-pillow
  ```

### 2. Installation Python (Virtual environment / Pip)

Si vous utilisez un environnement virtuel Python (`venv`), installez les dépendances listées dans `requirements.txt` :

```bash
python3 -m pip install -r requirements.txt
```

> **Note** : L'installation de `PyGObject` ou `pycairo` via `pip` nécessite les en-têtes de développement système (`libgirepository1.0-dev` / `cairo-devel`). Il est recommandé d'utiliser les paquets de votre distribution ci-dessus.

## Lancer la démo

```bash
python3 companion.py
```

Le script utilise automatiquement `GDK_BACKEND=x11` pour forcer le rendu en overlay transparent et sans aucune bordure sur Wayland et X11.

## Démarrage automatique de session (Autostart)

La façon fiable d'activer le démarrage automatique : cochez
**"Lancer au démarrage de la session"** dans les Réglages de Tux (clic droit
sur Tux → Réglages…). Compa génère alors lui-même un fichier XDG Autostart
correct (avec le chemin absolu vers `companion.py`) dans
`~/.config/autostart/compa.desktop`.

Un fichier [`compa.desktop.example`](compa.desktop.example) est fourni à
titre de référence uniquement — ne le copiez pas tel quel dans
`~/.config/autostart/`, son chemin relatif ne fonctionnera pas en dehors du
dossier du projet.

## Gestes & Interactions

- **clic simple** : Tux saute (physique sinusoïdale fluide) ;
- **double-clic** : Tux salue (`wave`) et affiche une bulle de dialogue ;
- **glisser-déposer (Drag & Drop)** : cliquez et déplacez Tux librement sur votre écran ;
- **clic droit** : ouvre le menu contextuel (Nourrir Tux 🐟, le Réveiller, Jouer, changer sa Personnalité ou ouvrir les Réglages).

## Portée de cette tranche

La démo rend déjà le bureau vivant : animations continues, événements aléatoires,
émotions, phrases rares et personnalités qui modulent réellement les probabilités
et la vitesse. Elle exclut volontairement IA, monitoring, launcher, widgets et
toute fonction de productivité — ce socle ne change pas de forme, y compris dans
les versions futures (voir [la roadmap](ROADMAP.md)).

Les intégrations système restantes — vrai multi-écran et emballage `.deb`/Flatpak — viennent après la démo initiale, par cible de distribution afin de respecter les règles X11/Wayland de chacune.
