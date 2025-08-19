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
import argparse
import logging
from urllib.parse import urlparse

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
        tags_data['title'] = tags.get('\xa9nam', [None])[0] if tags.get('\xa9nam') else None
        tags_data['artist'] = tags.get('\xa9ART', [None])[0] if tags.get('\xa9ART') else None
        tags_data['album'] = tags.get('\xa9alb', [None])[0] if tags.get('\xa9alb') else None
        tags_data['genre'] = tags.get('\xa9gen', [None])[0] if tags.get('\xa9gen') else None
        track_info = tags.get('trkn', [(None, None)])
        track = track_info[0][0] if track_info and track_info[0] else None
        tags_data['track'] = str(track) if track else None
        tags_data['date'] = tags.get('\xa9day', [None])[0] if tags.get('\xa9day') else None
        if 'covr' in tags and tags['covr']:
            cover_data = tags['covr'][0]
    elif ext == '.mp3':
        src = MP3(src_path, ID3=ID3)
        tags = src.tags or {}
        tags_data['title'] = tags.get('TIT2').text[0] if tags.get('TIT2') and tags.get('TIT2').text else None
        tags_data['artist'] = tags.get('TPE1').text[0] if tags.get('TPE1') and tags.get('TPE1').text else None
        tags_data['album'] = tags.get('TALB').text[0] if tags.get('TALB') and tags.get('TALB').text else None
        tags_data['genre'] = tags.get('TCON').text[0] if tags.get('TCON') and tags.get('TCON').text else None
        tags_data['track'] = tags.get('TRCK').text[0] if tags.get('TRCK') and tags.get('TRCK').text else None
        tags_data['date'] = tags.get('TDRC').text[0] if tags.get('TDRC') and tags.get('TDRC').text else None
        # Récupération des images APIC
        apic_frames = tags.getall('APIC') if hasattr(tags, 'getall') else []
        if apic_frames:
            cover_data = apic_frames[0].data
    elif ext == '.opus':
        src = OggOpus(src_path)
        tags = src.tags or {}
        tags_data['title'] = tags.get('TITLE', [None])[0] if tags.get('TITLE') else None
        tags_data['artist'] = tags.get('ARTIST', [None])[0] if tags.get('ARTIST') else None
        tags_data['album'] = tags.get('ALBUM', [None])[0] if tags.get('ALBUM') else None
        tags_data['genre'] = tags.get('GENRE', [None])[0] if tags.get('GENRE') else None
        tags_data['track'] = tags.get('TRACKNUMBER', [None])[0] if tags.get('TRACKNUMBER') else None
        tags_data['date'] = tags.get('DATE', [None])[0] if tags.get('DATE') else None
    else:
        src = File(src_path)
        tags = src.tags or {}
        tags_data['title'] = tags.get('title', [None])[0] if isinstance(tags.get('title'), list) else tags.get('title')
        tags_data['artist'] = tags.get('artist', [None])[0] if isinstance(tags.get('artist'), list) else tags.get('artist')

    # Embedding into WAV
    try:
        wav = WAVE(wav_path)
        try:
            wav.delete()
        except Exception:
            pass
        wav.add_tags()
        id3 = wav.tags
    except Exception as e:
        logging.warning(f"Impossible d'ajouter les métadonnées au fichier {wav_path}: {e}")
        return

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

    try:
        wav.save()
    except Exception as e:
        logging.warning(f"Erreur lors de la sauvegarde des métadonnées: {e}")


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
        return shutil.which(cmd)
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


def validate_soundcloud_url(url):
    """Valide qu'une URL est probablement une playlist SoundCloud."""
    parsed = urlparse(url)
    return (parsed.netloc in ['soundcloud.com', 'www.soundcloud.com'] and 
            '/sets/' in parsed.path)

def setup_logging(verbose=False):
    """Configure le système de logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

def main():
    parser = argparse.ArgumentParser(
        description="Télécharge une playlist SoundCloud et convertit en WAV avec métadonnées",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'usage:
  python3 scpdlwav.py --url https://soundcloud.com/user/sets/playlist
  python3 scpdlwav.py --interactive --verbose
  python3 scpdlwav.py --dry-run --url https://soundcloud.com/user/sets/playlist
        """
    )
    parser.add_argument('--url', '-u', help='URL de la playlist SoundCloud')
    parser.add_argument('--interactive', '-i', action='store_true', 
                       help='Mode interactif pour saisir l\'URL')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Active le mode verbeux')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simule les opérations sans les exécuter')
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    # Obtenir l'URL
    if args.url:
        url = args.url.strip()
    elif args.interactive or len(sys.argv) == 1:
        url = input("Entrez l'URL de la playlist SoundCloud : ").strip()
    else:
        parser.print_help()
        sys.exit(1)
    
    if not url:
        logging.error("URL invalide, veuillez réessayer.")
        sys.exit(1)
    
    if not validate_soundcloud_url(url):
        logging.warning("L'URL ne semble pas être une playlist SoundCloud valide")
        confirm = input("Continuer quand même ? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes', 'o', 'oui']:
            sys.exit(1)
    
    playlist_name = sanitize_folder_name(url.rstrip('/').split('/')[-1]) or 'playlist'
    base_dir = "downloads"
    playlist_dir = os.path.join(base_dir, playlist_name)
    wav_dir = os.path.join(playlist_dir, "WAV")
    
    logging.info(f"Dossier de téléchargement: {playlist_dir}")
    logging.info(f"Dossier WAV: {wav_dir}")
    
    if not args.dry_run:
        os.makedirs(playlist_dir, exist_ok=True)
        os.makedirs(wav_dir, exist_ok=True)
    
    # Vérifier ffmpeg avant les conversions (et tôt pour prévenir)
    _ensure_ffmpeg()

    # Construire la commande scdl en fonction de l'environnement
    scdl_cmd = _build_scdl_command(url)

    logging.info(f"Téléchargement de la playlist '{playlist_name}' dans '{playlist_dir}'...")
    if args.dry_run:
        logging.info(f"[DRY-RUN] Commande scdl: {' '.join(scdl_cmd)}")
    else:
        try:
            subprocess.run(scdl_cmd, check=True, cwd=playlist_dir)
        except subprocess.CalledProcessError as e:
            logging.error(f"Erreur lors du téléchargement avec scdl: {e}")
            sys.exit(1)
    
    # Si scdl crée un sous-dossier du nom de la playlist, déplacer son contenu vers playlist_dir
    if not args.dry_run:
        extra_folder = os.path.join(playlist_dir, playlist_name)
        if os.path.isdir(extra_folder):
            logging.debug(f"Déplacement du contenu de {extra_folder}")
            for item in os.listdir(extra_folder):
                shutil.move(os.path.join(extra_folder, item), playlist_dir)
            os.rmdir(extra_folder)
    
    # Recherche des fichiers audio dans playlist_dir en excluant le dossier WAV
    audio_files = []
    if args.dry_run:
        # En mode dry-run, chercher dans les fichiers existants pour simulation
        for root, dirs, files in os.walk(playlist_dir):
            # Exclure le dossier WAV de la recherche
            if os.path.abspath(root) == os.path.abspath(wav_dir):
                continue
            for f in files:
                if f.lower().endswith(('.m4a', '.mp3', '.opus')):
                    audio_files.append(os.path.join(root, f))
    else:
        for root, dirs, files in os.walk(playlist_dir):
            # Exclure le dossier WAV de la recherche
            if os.path.abspath(root) == os.path.abspath(wav_dir):
                continue
            for f in files:
                if f.lower().endswith(('.m4a', '.mp3', '.opus')):
                    audio_files.append(os.path.join(root, f))
    
    if not audio_files:
        if args.dry_run:
            logging.info("[DRY-RUN] Aucun fichier audio existant trouvé pour simulation")
            logging.info("[DRY-RUN] En mode normal, les fichiers seraient téléchargés d'abord")
            return
        else:
            logging.error(f"Aucun fichier audio (.m4a/.mp3/.opus) trouvé dans '{playlist_dir}'.")
            sys.exit(1)
    
    logging.info(f"Conversion de {len(audio_files)} fichier(s) en WAV non compressé avec métadonnées...")
    
    success_count = 0
    error_count = 0
    
    for src in audio_files:
        if not os.path.exists(src):
            logging.warning(f"Fichier source inexistant: {src}")
            error_count += 1
            continue
            
        base = sanitize_filename(os.path.basename(src), playlist_name)
        wav_file = os.path.join(wav_dir, f"{base}.wav")
        
        logging.info(f"→ Conversion: '{os.path.basename(src)}' → '{os.path.basename(wav_file)}'")
        
        if args.dry_run:
            logging.info(f"[DRY-RUN] ffmpeg -y -i '{src}' -c:a pcm_s16le -ar 44100 -ac 2 '{wav_file}'")
            logging.info(f"[DRY-RUN] Ajout des métadonnées de '{src}' vers '{wav_file}'")
            success_count += 1
            continue
        
        try:
            # Vérifier si le fichier WAV existe déjà
            if os.path.exists(wav_file):
                logging.debug(f"Le fichier {wav_file} existe déjà, il sera écrasé")
                
            subprocess.run([
                "ffmpeg", "-y", "-i", src,
                "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2", wav_file
            ], check=True, capture_output=True, text=True)
            
            embed_metadata(src, wav_file)
            success_count += 1
            logging.debug(f"Conversion réussie: {os.path.basename(wav_file)}")
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Erreur lors de la conversion de '{src}': {e}")
            error_count += 1
        except Exception as e:
            logging.error(f"Erreur inattendue pour '{src}': {e}")
            error_count += 1
    
    # Résumé final
    if args.dry_run:
        logging.info(f"[DRY-RUN] Simulation terminée: {success_count} fichiers simulés")
    else:
        logging.info(f"Conversion terminée: {success_count} réussies, {error_count} erreurs")
        if error_count == 0:
            logging.info("Tous les fichiers ont été convertis avec succès !")
        else:
            logging.warning(f"{error_count} fichiers n'ont pas pu être convertis")


if __name__ == "__main__":
    main()
