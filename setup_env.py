#!/usr/bin/env python3
"""
setup_env.py

Crée un environnement virtuel local (.venv), installe les dépendances Python,
et vérifie la présence de ffmpeg.

Usage:
  python3 setup_env.py
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
REQ = ROOT / "requirements.txt"


def run(cmd, **kwargs):
    print("$", " ".join(cmd))
    subprocess.check_call(cmd, **kwargs)


def ensure_venv():
    if not VENV_DIR.exists():
        print("[INFO] Création du venv local .venv ...")
        run([sys.executable, "-m", "venv", str(VENV_DIR)])
    else:
        print("[INFO] venv .venv déjà présent.")


def pip_path():
    if platform.system() == "Windows":
        return str(VENV_DIR / "Scripts" / "pip")
    return str(VENV_DIR / "bin" / "pip")


def python_path():
    if platform.system() == "Windows":
        return str(VENV_DIR / "Scripts" / "python")
    return str(VENV_DIR / "bin" / "python")


def install_requirements():
    if not REQ.exists():
        print("[AVERTISSEMENT] requirements.txt introuvable — rien à installer côté Python.")
        return
    print("[INFO] Installation des dépendances Python ...")
    run([pip_path(), "install", "-U", "pip", "wheel", "setuptools"]) 
    run([pip_path(), "install", "-r", str(REQ)])


def which(cmd):
    from shutil import which as _which
    return _which(cmd)


def check_ffmpeg():
    if which("ffmpeg"):
        print("[OK] ffmpeg détecté dans le PATH.")
        return
    print("[ATTENTION] ffmpeg n'a pas été détecté dans le PATH.")
    print("Installez-le selon votre OS puis réessayez:")
    print("  - macOS (Homebrew): brew install ffmpeg")
    print("  - Ubuntu/Debian:    sudo apt-get update && sudo apt-get install -y ffmpeg")
    print("  - Autres:           https://ffmpeg.org/download.html")


def main():
    ensure_venv()
    install_requirements()
    check_ffmpeg()
    print("\n[FINI] Activez votre venv et lancez le script:")
    if platform.system() == "Windows":
        print("  .\\.venv\\Scripts\\activate && python scpdlwav.py")
    else:
        print("  source .venv/bin/activate && python3 scpdlwav.py")


if __name__ == "__main__":
    main()
