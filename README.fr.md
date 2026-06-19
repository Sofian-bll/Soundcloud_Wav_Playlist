> [Read in English](README.md) | [Lire en Francais](README.fr.md)

<p align="center">
  <img src="assets/logo.svg" alt="SWP logo" width="160"/>
</p>

<h1 align="center" id="readme-top">Soundcloud WAV Playlist Downloader</h1>

<p align="center">
  Telecharge des playlists SoundCloud et convertit les pistes en WAV sans perte.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue?style=flat" alt="License"/>
  <img src="https://img.shields.io/badge/Python-3-blue?style=flat&logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/ffmpeg-requis-green?style=flat&logo=ffmpeg" alt="ffmpeg"/>
</p>

---

## Fonctionnalites

- Telechargement de playlists SoundCloud completes
- Conversion automatique en WAV (sans perte, non compresse)
- Conservation des metadonnees (titre, artiste, genre, piste, date, pochette)
- Traitement par lot de plusieurs pistes

## Demarrage rapide

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Si ce n'est pas deja fait : `brew install ffmpeg` (macOS) ou `apt install ffmpeg` (Linux).

## Utilisation

```bash
# Saisie interactive
python scpdlwav.py

# URL passee en argument
python scpdlwav.py https://soundcloud.com/user/sets/nom-de-playlist
```

## Pre-requis

- Python 3.x
- ffmpeg
- Voir `requirements.txt` pour les paquets Python

## Note legale

Usage personnel uniquement. Respectez les conditions d'utilisation de SoundCloud et les droits d'auteur. Ne telechargez que le contenu auquel vous avez le droit d'acceder.

## Licence

MIT © 2026 Sofian — voir [LICENSE](LICENSE).
