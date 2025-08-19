#!/usr/bin/env python3
"""
scpdlwav.py

Script de téléchargement d'une playlist SoundCloud en M4A, MP3 ou OPUS puis conversion en WAV non compressé,
avec conservation des métadonnées (titre, artiste, genre, piste, date) et de la pochette si possible.
Utilise :
  - scdl (https://github.com/flyingrub/scdl)
  - ffmpeg
  - mutagen

Usage :
  python3 scpdlwav.py

Astuce d'installation rapide:
  - Créez et activez un venv local: python3 -m venv .venv && source .venv/bin/activate
  - Installez les dépendances: pip install -r requirements.txt
  - Installez ffmpeg (macOS: brew install ffmpeg | Ubuntu: sudo apt-get install ffmpeg)
"""
import subprocess
import sys
import os
import shutil  # déplacement des fichiers
import shutil as _shutil

# Gestion de l'absence de mutagen avec message clair
try:
    from mutagen.mp4 import MP4
    from mutagen.wave import WAVE
    from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TCON, TRCK, TDRC, COMM
    from mutagen.mp3 import MP3
    from mutagen.oggopus import OggOpus
    from mutagen import File
except ImportError as e:
    print("[ERREUR] Le module Python 'mutagen' est manquant.")
    print("Veuillez installer les dépendances dans un environnement virtuel:")
    print("  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt")
    sys.exit(1)

def sanitize_folder_name(name):
    """Sanitize folder name by removing or replacing invalid characters"""
    return "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in name).strip()


def embed_metadata(src_path, wav_path):
    """
    Copie les métadonnées et la pochette du fichier source (m4a/mp3/opus) vers le WAV via ID3 tags.
    Nécessite mutagen.
    """
    ext = os.path.splitext(src_path)[1].lower()
    tags_data = {}
    cover_data = None

    if ext == '.m4a':
        src = MP4(src_path)
        tags = src.tags or {}
        tags_data['title'] = tags.get('\xa9nam', [None])[0]
        tags_data['artist'] = tags.get('\xa9ART', [None])[0]
        tags_data['album'] = tags.get('\xa9alb', [None])[0]
        tags_data['genre'] = tags.get('\xa9gen', [None])[0]
        track = tags.get('trkn', [(None, None)])[0][0]
        tags_data['track'] = str(track) if track else None
        tags_data['date'] = tags.get('\xa9day', [None])[0]
        if 'covr' in tags and tags['covr']:
            cover_data = tags['covr'][0]
    elif ext == '.mp3':
        src = MP3(src_path, ID3=ID3)
        tags = src.tags or {}
        tags_data['title'] = tags.get('TIT2').text[0] if tags.get('TIT2') else None
        tags_data['artist'] = tags.get('TPE1').text[0] if tags.get('TPE1') else None
        tags_data['album'] = tags.get('TALB').text[0] if tags.get('TALB') else None
        tags_data['genre'] = tags.get('TCON').text[0] if tags.get('TCON') else None
        tags_data['track'] = tags.get('TRCK').text[0] if tags.get('TRCK') else None
        tags_data['date'] = tags.get('TDRC').text[0] if tags.get('TDRC') else None
        # Récupération des images APIC
        apic_frames = tags.getall('APIC') if hasattr(tags, 'getall') else []
        if apic_frames:
            cover_data = apic_frames[0].data
    elif ext == '.opus':
        src = OggOpus(src_path)
        tags = src.tags or {}
        tags_data['title'] = tags.get('TITLE', [None])[0]
        tags_data['artist'] = tags.get('ARTIST', [None])[0]
        tags_data['album'] = tags.get('ALBUM', [None])[0]
        tags_data['genre'] = tags.get('GENRE', [None])[0]
        tags_data['track'] = tags.get('TRACKNUMBER', [None])[0]
        tags_data['date'] = tags.get('DATE', [None])[0]
    else:
        src = File(src_path)
        tags = src.tags or {}
        tags_data['title'] = tags.get('title', [None])[0] if isinstance(tags.get('title'), list) else tags.get('title')
        tags_data['artist'] = tags.get('artist', [None])[0] if isinstance(tags.get('artist'), list) else tags.get('artist')

    # Embedding into WAV
    wav = WAVE(wav_path)
    try:
        wav.delete()
    except Exception:
        pass
    wav.add_tags()
    id3 = wav.tags

    # Ajout des tags textes
    if tags_data.get('title'): id3.add(TIT2(encoding=3, text=tags_data['title']))
    if tags_data.get('artist'): id3.add(TPE1(encoding=3, text=tags_data['artist']))
    if tags_data.get('album'): id3.add(TALB(encoding=3, text=tags_data['album']))
    if tags_data.get('genre'): id3.add(TCON(encoding=3, text=tags_data['genre']))
    if tags_data.get('track'): id3.add(TRCK(encoding=3, text=tags_data['track']))
    if tags_data.get('date'): id3.add(TDRC(encoding=3, text=tags_data['date']))

    # Ajout de la pochette si disponible
    if cover_data:
        mime = 'image/jpeg' if cover_data[:3] == b'\xff\xd8\xff' else 'image/png'
        id3.add(APIC(encoding=3, mime=mime, type=3, desc='Cover', data=cover_data))

    wav.save()


def sanitize_filename(name, playlist_name):
    """Sanitize filename by removing or replacing invalid/special characters"""
    # Remove file extension if present
    base_name = os.path.splitext(name)[0]
    
    # Remove playlist name from the beginning if present
    if base_name.startswith(playlist_name):
        base_name = base_name[len(playlist_name):].lstrip(' -_')
    
    # Replace special characters
    sanitized = base_name.replace('◆', '-')
    sanitized = sanitized.replace('⚔', '-')
    sanitized = sanitized.replace('ô', 'o')
    sanitized = sanitized.replace('è', 'e')
    sanitized = sanitized.replace('ø', 'o')
    
    # Ne garder que les caractères alphanumériques et certains symboles
    sanitized = "".join(c if c.isalnum() or c in (' ', '-', '_', '[', ']', '.') else '_' for c in sanitized)
    
    # Supprimer les espaces multiples
    sanitized = ' '.join(sanitized.split())
    
    return sanitized.strip()

def _which(cmd: str):
    try:
        return _shutil.which(cmd)
    except Exception:
        return None


def _ensure_ffmpeg():
    if not _which("ffmpeg"):
        print("[ERREUR] ffmpeg n'est pas trouvé dans votre PATH.")
        print("Installez-le puis réessayez.")
        print("  - macOS (Homebrew): brew install ffmpeg")
        print("  - Ubuntu/Debian:    sudo apt-get update && sudo apt-get install -y ffmpeg")
        print("  - Autres:           https://ffmpeg.org/download.html")
        sys.exit(1)


def _build_scdl_command(url: str):
    # 1) Si le binaire scdl est disponible
    if _which("scdl"):
        return ["scdl", "-c", "-l", url]
    # 2) Sinon, tenter via le module Python "python -m scdl"
    try:
        import importlib.util
        spec = importlib.util.find_spec("scdl")
        if spec is not None:
            return [sys.executable, "-m", "scdl", "-c", "-l", url]
    except Exception:
        pass
    # 3) Sinon, afficher un message d'aide clair
    print("[ERREUR] scdl n'est pas installé ou non accessible.")
    print("Installez les dépendances Python dans un venv local puis réessayez:")
    print("  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt")
    sys.exit(1)


def main():
    url = input("Entrez l'URL de la playlist SoundCloud : ").strip()
    if not url:
        print("URL invalide, veuillez réessayer.")
        sys.exit(1)
    
    playlist_name = sanitize_folder_name(url.rstrip('/').split('/')[-1]) or 'playlist'
    base_dir = "downloads"
    playlist_dir = os.path.join(base_dir, playlist_name)
    wav_dir = os.path.join(playlist_dir, "WAV")
    os.makedirs(playlist_dir, exist_ok=True)
    os.makedirs(wav_dir, exist_ok=True)
    
    # Vérifier ffmpeg avant les conversions (et tôt pour prévenir)
    _ensure_ffmpeg()

    # Construire la commande scdl en fonction de l'environnement
    scdl_cmd = _build_scdl_command(url)

    print(f"\nTéléchargement de la playlist '{playlist_name}' dans '{playlist_dir}'...")
    try:
        subprocess.run(scdl_cmd, check=True, cwd=playlist_dir)
    except subprocess.CalledProcessError:
        print("Erreur lors du téléchargement avec scdl.")
        sys.exit(1)
    
    # Si scdl crée un sous-dossier du nom de la playlist, déplacer son contenu vers playlist_dir
    extra_folder = os.path.join(playlist_dir, playlist_name)
    if os.path.isdir(extra_folder):
        for item in os.listdir(extra_folder):
            shutil.move(os.path.join(extra_folder, item), playlist_dir)
        os.rmdir(extra_folder)
    
    # Recherche des fichiers audio dans playlist_dir en excluant le dossier WAV
    audio_files = []
    for root, dirs, files in os.walk(playlist_dir):
        # Exclure le dossier WAV de la recherche
        if os.path.abspath(root) == os.path.abspath(wav_dir):
            continue
        for f in files:
            if f.lower().endswith(('.m4a', '.mp3', '.opus')):
                audio_files.append(os.path.join(root, f))
    
    if not audio_files:
        print(f"Aucun fichier audio (.m4a/.mp3/.opus) trouvé dans '{playlist_dir}'.")
        sys.exit(1)
    
    print(f"\nConversion de {len(audio_files)} fichier(s) en WAV non compressé avec métadonnées...\n")
    for src in audio_files:
        base = sanitize_filename(os.path.basename(src), playlist_name)
        wav_file = os.path.join(wav_dir, f"{base}.wav")
        print(f"→ Conversion de '{os.path.basename(src)}' → '{os.path.basename(wav_file)}'")
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", src,
                "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2", wav_file
            ], check=True)
            embed_metadata(src, wav_file)
        except subprocess.CalledProcessError:
            print(f"Erreur lors de la conversion de '{src}'.")
    
    print("\nTous les fichiers ont été convertis avec succès !")


if __name__ == "__main__":
    main()
