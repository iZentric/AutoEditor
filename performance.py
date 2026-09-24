"""Reusable analysis results without lower quality settings or cached API failures."""
import functools
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from contextlib import contextmanager

CACHE_SCHEMA = 1
_records = []


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix='.writing-', delete=False) as stream:
            temporary = stream.name
            json.dump(value, stream, ensure_ascii=False, allow_nan=False)
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def file_digest(path):
    """Hash all bytes; stat-only memoization is unsafe on coarse-timestamp filesystems.

    Pipeline callers compute this once for their immutable downloaded VOD and pass
    it explicitly to transcript/review stages. Independent calls always re-hash.
    """
    path = Path(path).resolve()
    before = path.stat()
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(block)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise RuntimeError('Source changed while computing its fingerprint')
    return digest.hexdigest()


def record(stage, seconds, cache_hit=False):
    _records.append({'stage': stage, 'seconds': round(seconds, 4), 'cache_hit': cache_hit})
    print(f'PERFORMANTA {stage}: {seconds:.2f}s' + (' (refolosit, fara reanaliza)' if cache_hit else ''), flush=True)
    path = os.environ.get('AE_PERFORMANCE_REPORT')
    if path:
        try:
            atomic_json(path, {'schema': 1, 'stages': _records})
        except OSError:
            print('Raportul de performanta nu a putut fi scris; procesarea continua.', flush=True)


@contextmanager
def stage(name):
    start = time.monotonic()
    try:
        yield
    finally:
        record(name, time.monotonic() - start)


def measured(name):
    def decorate(function):
        @functools.wraps(function)
        def wrapped(*args, **kwargs):
            with stage(name):
                return function(*args, **kwargs)
        return wrapped
    return decorate


def cached_json(namespace, identity, compute, valid, ttl=None):
    """Cache exact inputs only. Exceptions, malformed responses and partial writes miss."""
    start = time.monotonic()
    enabled = os.environ.get('AE_CACHE', '1') != '0'
    refresh = os.environ.get('AE_REANALYZE', '0') == '1'
    serialized = json.dumps({'schema': CACHE_SCHEMA, 'namespace': namespace, 'input': identity},
                            sort_keys=True, ensure_ascii=False, allow_nan=False)
    key = hashlib.sha256(serialized.encode()).hexdigest()
    root = Path(os.environ.get('AE_CACHE_DIR', Path(__file__).resolve().parent / '.cache' / 'autoeditor'))
    target = root / namespace / (key + '.json')
    if enabled and not refresh:
        try:
            document = json.loads(target.read_text(encoding='utf-8'))
            age = time.time() - document['created']
            value = document['value']
            if document['key'] == key and 0 <= age and (ttl is None or age <= ttl) and valid(value):
                record(namespace, time.monotonic() - start, cache_hit=True)
                return value
        except (OSError, ValueError, TypeError, KeyError):
            pass
    try:
        value = compute()
        if enabled and valid(value):
            try:
                atomic_json(target, {'key': key, 'created': time.time(), 'value': value})
            except (OSError, ValueError, TypeError):
                # A read-only/full cache must never stop a valid edit.
                pass
        return value
    finally:
        record(namespace, time.monotonic() - start)
