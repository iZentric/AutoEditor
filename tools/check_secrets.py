"""Small offline credential guard. Print paths/types only, never matched values."""
from pathlib import Path
import re
import subprocess
import sys

PATTERNS = {
    'oauth-client-secret': re.compile(r'GOCSPX-[A-Za-z0-9_-]{16,}'),
    'google-refresh-token': re.compile(r'1//[A-Za-z0-9_-]{30,}'),
    'google-api-key': re.compile(r'AIza[A-Za-z0-9_-]{30,}'),
    'github-token': re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})'),
    'private-key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
}
MEDIA = {'.mp3', '.mp4', '.wav', '.ogg', '.m4a', '.flac', '.aac', '.opus',
         '.webm', '.png', '.jpg', '.jpeg', '.gif', '.zip'}
# Fonturi si alte binare de asset: nu contin text de scanat. Fara lista asta
# gardul bloca repo-ul la fiecare font adaugat (Monocraft.ttc a rupt CI-ul).
BINARY = {'.ttc', '.ttf', '.otf', '.woff', '.woff2', '.eot', '.ico', '.pdf',
          '.pyc', '.so', '.db', '.sqlite'}


def _looks_binary(path):
    """True pentru fisiere care nu sunt text (detectie dupa octeti NUL)."""
    try:
        with path.open('rb') as handle:
            return b'\0' in handle.read(4096)
    except OSError:
        return True


def scan_paths(paths):
    findings = []
    for path in paths:
        path = Path(path)
        if not path.is_file() or path.suffix.lower() in MEDIA or path.suffix.lower() in BINARY:
            continue
        if path.stat().st_size > 2 * 1024 * 1024:
            if _looks_binary(path):
                continue
            findings.append((str(path), 'text-too-large-for-guard'))
            continue
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            findings.append((str(path), 'unreadable-text-file'))
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append((str(path), label))
    return findings


def main():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
                            cwd=root, check=True, capture_output=True)
    names = sorted(set(name for name in result.stdout.decode().split('\0') if name))
    paths = []
    unsafe = []
    for name in names:
        path = root / name
        if path.is_symlink():
            unsafe.append((name, 'symlink-needs-manual-review'))
        else:
            paths.append(path)
    findings = scan_paths(paths)
    for path, label in findings:
        print(f'BLOCKED: {Path(path).relative_to(root)} ({label})')
    for path, label in unsafe:
        print(f'BLOCKED: {path} ({label})')
    if not findings and not unsafe:
        print(f'Credential guard: no supported credential patterns found in {len(paths)} candidate paths.')
    return 1 if findings or unsafe else 0


if __name__ == '__main__':
    sys.exit(main())
