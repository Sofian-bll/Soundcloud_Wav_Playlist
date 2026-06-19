> [Read in English](README.md) | [Lire en Francais](README.fr.md)

<p align="center">
  <img src="assets/logo.svg" alt="SWP logo" width="160"/>
</p>

<h1 align="center" id="readme-top">Soundcloud WAV Playlist Downloader</h1>

<p align="center">
  Download SoundCloud playlists and convert tracks to lossless WAV.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue?style=flat" alt="License"/>
  <img src="https://img.shields.io/badge/Python-3-blue?style=flat&logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/ffmpeg-required-green?style=flat&logo=ffmpeg" alt="ffmpeg"/>
</p>

---

## Features

- Download complete SoundCloud playlists
- Automatic conversion to WAV (lossless, uncompressed)
- Metadata preservation (title, artist, genre, track number, date, cover art)
- Batch processing of multiple tracks

## Quick Start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

If you don't have it yet: `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux).

## Usage

```bash
# Interactive prompt
python scpdlwav.py

# Pass URL directly
python scpdlwav.py https://soundcloud.com/user/sets/playlist-name
```

## Requirements

- Python 3.x
- ffmpeg
- See `requirements.txt` for Python packages

## Legal Notice

For personal use only. Respect SoundCloud's Terms of Service and copyright laws. Only download content you have the right to access.

## License

MIT © 2026 Sofian — see [LICENSE](LICENSE).
