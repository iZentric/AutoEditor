"""Rename delivery files inside episodes/, never into the repository root."""
from pathlib import Path
import re
from upload_release import slug_nume


def rename_deliverables(folder='episodes'):
    folder = Path(folder)
    used = set()
    for metadata in sorted(folder.glob('*_upload.txt')):
        old = metadata.name.removesuffix('_upload.txt')
        if not re.fullmatch(r'(EP|SHORT)\d+', old):
            continue  # Already public: repeat runs are idempotent.
        lines = metadata.read_text(encoding='utf-8').splitlines()
        title = ''
        for n, line in enumerate(lines):
            if line.startswith('TITLU:'):
                title = line.split(':', 1)[1].strip()
                if not title and n + 1 < len(lines):
                    title = lines[n+1].strip()
                break
        if not title:
            raise ValueError(f'Missing title: {metadata.name}')
        index = int(re.search(r'\d+$', old).group())
        base = slug_nume(title + (' SHORT' if old.startswith('SHORT') else ''),
                         nr=index).removesuffix('.mp4')
        sources = [f for f in folder.iterdir() if f.is_file()
                   and (f.name.startswith(old + '.') or f.name.startswith(old + '_'))]
        while base in used or any((folder / (base + f.name[len(old):])).exists() for f in sources):
            base += '_x'
        used.add(base)
        for source in sources:
            destination = folder / (base + source.name[len(old):])
            source.rename(destination)
            print(f'{source.name} -> {destination.name}')


if __name__ == '__main__':
    rename_deliverables()
