"""Cheap configuration checks before downloading or processing a VOD. No secret values logged."""
import os
from pathlib import Path
import re
import sys


def check(environment, root):
    errors, warnings = [], []
    if not environment.get('GEMINI_API_KEY', '').strip():
        errors.append('Lipseste Secret GEMINI_API_KEY; verificarea video este obligatorie.')
    models = [m.strip() for m in environment.get('GEMINI_MODEL', '').split(',') if m.strip()]
    if not models or any(not re.fullmatch(r'[A-Za-z0-9_.-]+', model) for model in models):
        errors.append('GEMINI_MODEL trebuie sa contina nume de modele separate prin virgule.')
    if not any((Path(root) / 'sunete_mele').rglob('*.mp3')):
        warnings.append('Nu sunt sunete mp3 in sunete_mele; nu se vor inventa efecte.')
    required = ('YT_CLIENT_ID', 'YT_CLIENT_SECRET', 'YT_REFRESH_TOKEN')
    if environment.get('YT_UPLOAD_ENABLED', 'false').lower() != 'true':
        warnings.append('Upload YouTube dezactivat explicit; livrarea in Releases continua.')
    elif not all(environment.get(name, '').strip() for name in required):
        warnings.append('Upload YouTube inactiv: lipsesc setari OAuth. Livrarea in Releases ramane disponibila.')
    return errors, warnings


def main():
    errors, warnings = check(os.environ, Path(__file__).resolve().parent)
    for warning in warnings:
        print('ATENTIE: ' + warning)
    for error in errors:
        print('OPRIT: ' + error)
    if not errors:
        print('Configuratie prezenta. Validitatea cheii si accesul la model se confirma la apelul API, nu aici.')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
