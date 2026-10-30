#!/usr/bin/env python3
"""Inventory music, sound effects and meme audio from a YouTube video or local file.

The tool downloads/extracts audio only to a temporary directory, asks Gemini to
label audible events, optionally fingerprints music with AudD, compares effects
against local sound libraries, and returns searchable source links. It never
publishes or downloads replacement sound assets.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import wave

ROOT = Path(__file__).resolve().parent
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac', '.opus', '.wma'}
YOUTUBE_HOSTS = {'youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com',
                 'youtu.be', 'www.youtu.be', 'youtube-nocookie.com', 'www.youtube-nocookie.com'}
VIDEO_ID_RE = re.compile(r'^[A-Za-z0-9_-]{11}$')
GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
AUDD_URL = 'https://api.audd.io/'


def youtube_video_id(url: str) -> str | None:
    """Return an 11-character video ID only for known YouTube URL shapes."""
    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        return None
    host = (parsed.hostname or '').lower().rstrip('.')
    if parsed.scheme.lower() not in {'http', 'https'} or host not in YOUTUBE_HOSTS:
        return None
    segments = [part for part in parsed.path.split('/') if part]
    candidate = None
    if host in {'youtu.be', 'www.youtu.be'}:
        candidate = segments[0] if segments else None
    elif parsed.path.rstrip('/') == '/watch':
        candidate = urllib.parse.parse_qs(parsed.query).get('v', [None])[0]
    elif len(segments) >= 2 and segments[0] in {'shorts', 'live', 'embed', 'v'}:
        candidate = segments[1]
    return candidate if candidate and VIDEO_ID_RE.fullmatch(candidate) else None


def youtube_url(video_id: str) -> str:
    if not VIDEO_ID_RE.fullmatch(video_id):
        raise ValueError('ID YouTube invalid')
    return f'https://www.youtube.com/watch?v={video_id}'


def read_secret(name: str, root: Path = ROOT) -> str | None:
    """Read an optional key from the environment or a local, non-symlink .env."""
    value = os.environ.get(name, '').strip()
    if value:
        return value
    env_path = Path(root) / '.env'
    if not env_path.is_file() or env_path.is_symlink():
        return None
    try:
        lines = env_path.read_text(encoding='utf-8').splitlines()
    except OSError:
        return None
    prefix = name + '='
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or not line.startswith(prefix):
            continue
        value = line.split('=', 1)[1].strip().strip('"').strip("'")
        if value and value.lower() not in {'cheia_ta_aici', 'your_key_here', 'paste_key_here'}:
            return value
    return None


def find_ffmpeg() -> str:
    configured = os.environ.get('FFMPEG', '').strip()
    if configured and Path(configured).is_file():
        return configured
    found = shutil.which(configured or 'ffmpeg')
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise RuntimeError('Nu găsesc FFmpeg. Instalează dependențele din requirements.txt.') from exc


def _run_quiet(command: list[str], timeout: int, message: str) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(message) from exc
    if result.returncode != 0:
        raise RuntimeError(message)
    return result


def download_youtube_audio(url: str, folder: Path) -> Path:
    """Fetch only the best audio stream for a public, single YouTube video."""
    video_id = youtube_video_id(url)
    if not video_id:
        raise ValueError('Introdu linkul unui singur videoclip YouTube, nu un canal sau playlist.')
    output_template = str(folder / 'source.%(ext)s')
    command = [sys.executable, '-m', 'yt_dlp', '--no-playlist', '--no-progress',
               '--no-warnings', '--quiet', '--format', 'bestaudio',
               '--max-filesize', '2G', '--output', output_template, youtube_url(video_id)]
    _run_quiet(command, timeout=1800, message=(
        'Nu am putut lua pista audio. Video-ul poate fi privat, restricționat sau indisponibil.'))
    candidates = [p for p in folder.glob('source.*') if p.is_file() and not p.name.endswith(('.part', '.ytdl'))]
    if not candidates:
        raise RuntimeError('yt-dlp nu a creat pista audio.')
    return max(candidates, key=lambda p: p.stat().st_size)


def convert_to_wav(ffmpeg: str, source: Path, output: Path, sample_rate: int = 16000,
                   normalize: bool = False, seek: float | None = None,
                   duration: float | None = None) -> None:
    command = [ffmpeg, '-nostdin', '-hide_banner', '-loglevel', 'error', '-y']
    if seek is not None:
        command += ['-ss', f'{max(0.0, seek):.3f}']
    command += ['-i', str(source), '-map', '0:a:0', '-vn']
    if duration is not None:
        command += ['-t', f'{max(0.1, duration):.3f}']
    if normalize:
        # Lifts quiet passages for analysis; it cannot unmix music buried under speech.
        command += ['-af', 'loudnorm=I=-16:TP=-1.5:LRA=11']
    command += ['-ac', '1', '-ar', str(sample_rate), '-c:a', 'pcm_s16le', str(output)]
    _run_quiet(command, timeout=900, message=f'FFmpeg nu a putut extrage audio din {source.name}.')
    if not output.is_file() or output.stat().st_size <= 44:
        raise RuntimeError(f'Nu s-a putut crea segmentul audio {output.name}.')


def wav_duration(path: Path) -> float:
    try:
        with wave.open(str(path), 'rb') as stream:
            rate = stream.getframerate()
            frames = stream.getnframes()
    except (OSError, wave.Error) as exc:
        raise RuntimeError('Audio-ul extras nu este un WAV valid.') from exc
    if rate <= 0 or frames <= 0:
        raise RuntimeError('Pista audio este goală sau are durata invalidă.')
    return frames / rate


def make_windows(duration: float, window_seconds: float, stride_seconds: float,
                 maximum: int) -> list[tuple[float, float]]:
    """Create overlapping windows and distribute a cap across the whole video."""
    if not math.isfinite(duration) or duration <= 0:
        return []
    if window_seconds <= 0 or stride_seconds <= 0 or maximum <= 0:
        raise ValueError('Durata ferestrei, pasul și limita trebuie să fie pozitive.')
    # Keep a fixed stride and let the final window be shorter. Do not snap the
    # last window back to duration-window: that can create a redundant overlap.
    last_full_start = max(0.0, duration - window_seconds)
    count = max(1, int(math.ceil(last_full_start / stride_seconds)) + 1)
    starts = [round(i * stride_seconds, 3) for i in range(count)]
    if len(starts) > maximum:
        if maximum == 1:
            starts = [starts[0]]
        else:
            indexes = {round(i * (len(starts) - 1) / (maximum - 1)) for i in range(maximum)}
            starts = [starts[i] for i in sorted(indexes)]
    return [(start, min(window_seconds, duration - start)) for start in starts if duration - start > 0.05]


def coverage_fraction(windows: list[tuple[float, float]], duration: float) -> float:
    if duration <= 0 or not windows:
        return 0.0
    intervals = sorted((max(0.0, start), min(duration, start + length)) for start, length in windows)
    covered = 0.0
    left, right = intervals[0]
    for start, end in intervals[1:]:
        if start <= right:
            right = max(right, end)
        else:
            covered += max(0.0, right - left)
            left, right = start, end
    covered += max(0.0, right - left)
    return min(1.0, covered / duration)


def _finite_number(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def parse_audio_events(document: object, offset: float, duration: float) -> list[dict]:
    """Validate event timestamps from the model; never trust raw JSON as a report."""
    if not isinstance(document, dict) or not isinstance(document.get('events'), list):
        return []
    aliases = {
        'music': 'music', 'music_bed': 'music', 'song': 'music', 'background_music': 'music',
        'sfx': 'sfx', 'sound_effect': 'sfx', 'foley': 'sfx', 'meme': 'meme',
        'meme_sfx': 'meme', 'meme_sound': 'meme', 'ambience': 'ambience',
        'ambient': 'ambience', 'environment': 'ambience', 'other': 'other',
        'speech': 'speech', 'voice': 'speech', 'dialogue': 'speech',
    }
    result = []
    for item in document['events'][:100]:
        if not isinstance(item, dict):
            continue
        start = _finite_number(item.get('start_sec', item.get('start')))
        end = _finite_number(item.get('end_sec', item.get('end')))
        label = item.get('label') or item.get('name')
        if start is None or end is None or not isinstance(label, str):
            continue
        if end <= start or end < 0 or start > duration or len(label.strip()) < 2:
            continue
        start = min(duration, max(0.0, start))
        end = min(duration, max(start, end))
        if end <= start:
            continue
        raw_kind = str(item.get('type', item.get('kind', 'other'))).strip().lower().replace('-', '_').replace(' ', '_')
        kind = aliases.get(raw_kind, 'other')
        # Dialogue itself is not a sound effect inventory item.
        if kind == 'speech':
            continue
        confidence = _finite_number(item.get('confidence'))
        confidence = min(1.0, max(0.0, confidence if confidence is not None else 0.4))
        description = item.get('description', '')
        if not isinstance(description, str):
            description = ''
        result.append({
            'start_sec': round(offset + start, 2),
            'end_sec': round(offset + end, 2),
            'type': kind,
            'label': label.strip()[:120],
            'description': description.strip()[:400],
            'confidence': confidence,
            'background': item.get('background') is True,
            'local_matches': [],
        })
    return result


def _similar_labels(left: str, right: str) -> bool:
    import difflib
    a = re.sub(r'[^a-z0-9ăâîșț]+', ' ', left.lower()).strip()
    b = re.sub(r'[^a-z0-9ăâîșț]+', ' ', right.lower()).strip()
    return a == b or difflib.SequenceMatcher(None, a, b).ratio() >= 0.86


def merge_audio_events(events: list[dict]) -> list[dict]:
    """Collapse duplicate observations from overlapping AI windows, not repeated hits."""
    merged: list[dict] = []
    for event in sorted(events, key=lambda item: (item['start_sec'], item['end_sec'])):
        match = None
        for previous in reversed(merged[-20:]):
            if event['start_sec'] - previous['end_sec'] > 12:
                break
            if event['type'] != previous['type'] or not _similar_labels(event['label'], previous['label']):
                continue
            overlap = min(event['end_sec'], previous['end_sec']) - max(event['start_sec'], previous['start_sec'])
            shortest = min(event['end_sec'] - event['start_sec'], previous['end_sec'] - previous['start_sec'])
            if overlap >= min(0.25, shortest * 0.35):
                match = previous
                break
        if match is None:
            merged.append(dict(event))
        else:
            match['start_sec'] = round(min(match['start_sec'], event['start_sec']), 2)
            match['end_sec'] = round(max(match['end_sec'], event['end_sec']), 2)
            if event['confidence'] > match['confidence']:
                match['confidence'] = event['confidence']
            if event['description'] and len(event['description']) > len(match['description']):
                match['description'] = event['description']
            match['background'] = match['background'] or event['background']
    return merged


def _event_prompt(offset: float, duration: float) -> str:
    return (
        'Ascultă acest fragment audio cu mare atenție. Inventariază sunetele distincte: '
        'muzică inclusiv în fundal și la volum mic, melodii, efecte SFX, meme-uri audio, '
        'ambianță și schimbări relevante. Nu transcrie dialogul și nu inventa nume de melodii; '
        'recunoașterea exactă a pieselor se face separat. Nu confunda o voce cu un efect. '
        'Dacă un sunet este acoperit sau nesigur, descrie-l prudent și dă confidence mic. '
        'Timpii trebuie să fie secunde relative la începutul acestui fragment, între 0 și '
        f'{duration:.2f}; începutul fragmentului în video este {offset:.2f}s. '
        'Unește muzica de fundal continuă într-un singur eveniment pe fragment, dar păstrează '
        'efectele distincte și repetările lor ca evenimente separate. Returnează DOAR JSON: '
        '{"events":[{"start_sec":0.0,"end_sec":1.0,"type":"music|sfx|meme|ambience|other",'
        '"label":"descriere scurtă","description":"ce se aude","confidence":0.0,'
        '"background":true}]}. Max 40 evenimente pe fragment; fără alte chei sau text.'
    )


def _models_from_env() -> list[str]:
    configured = os.environ.get('GEMINI_AUDIO_MODEL') or os.environ.get('GEMINI_MODEL') or 'gemini-2.5-flash'
    return list(dict.fromkeys(part.strip() for part in configured.split(',') if part.strip()))


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*```$', '', text)
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        left, right = text.find('{'), text.rfind('}')
        if left < 0 or right <= left:
            raise ValueError('Gemini nu a returnat JSON valid')
        value = json.loads(text[left:right + 1])
    if not isinstance(value, dict):
        raise ValueError('Răspunsul AI nu este un obiect JSON')
    return value


def analyze_audio_with_gemini(api_key: str, models: list[str], segment: Path,
                              offset: float, duration: float) -> tuple[str, dict]:
    """Send only one short audio window (not the full video) to Gemini."""
    data = segment.read_bytes()
    if len(data) > 12 * 1024 * 1024:
        raise ValueError('Segmentul audio este prea mare pentru analiză inline.')
    parts = [
        {'inline_data': {'mime_type': 'audio/wav', 'data': base64.b64encode(data).decode('ascii')}},
        {'text': _event_prompt(offset, duration)},
    ]
    body = json.dumps({
        'contents': [{'role': 'user', 'parts': parts}],
        'generationConfig': {'responseMimeType': 'application/json', 'temperature': 0.1},
    }).encode('utf-8')
    last_error = None
    for model in models:
        for attempt in range(2):
            request = urllib.request.Request(
                GEMINI_URL.format(model=urllib.parse.quote(model, safe='-._')),
                data=body, method='POST',
                headers={'Content-Type': 'application/json', 'x-goog-api-key': api_key})
            try:
                with urllib.request.urlopen(request, timeout=240) as response:
                    payload = json.load(response)
                text = payload['candidates'][0]['content']['parts'][0]['text']
                return model, _parse_json_response(text)
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code in {429, 500, 503} and attempt == 0:
                    time.sleep(2)
                    continue
                # 400/404 often mean the selected model cannot process audio; try next.
                break
            except (urllib.error.URLError, TimeoutError, KeyError, IndexError,
                    TypeError, ValueError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt == 0 and isinstance(exc, (urllib.error.URLError, TimeoutError)):
                    time.sleep(1)
                    continue
                break
    raise RuntimeError('Gemini nu a putut analiza audio-ul') from last_error


def _multipart(fields: dict[str, str], file_data: bytes, filename: str) -> tuple[str, bytes]:
    boundary = '----AutoEditorAudio' + secrets.token_hex(16)
    chunks = []
    for name, value in fields.items():
        chunks.extend([
            f'--{boundary}\r\n'.encode(),
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
            str(value).encode('utf-8'), b'\r\n',
        ])
    safe_filename = Path(filename).name.replace('"', '_')
    chunks.extend([
        f'--{boundary}\r\n'.encode(),
        f'Content-Disposition: form-data; name="file"; filename="{safe_filename}"\r\n'.encode(),
        b'Content-Type: audio/wav\r\n\r\n', file_data, b'\r\n',
        f'--{boundary}--\r\n'.encode(),
    ])
    return boundary, b''.join(chunks)


def audd_identify(api_token: str, segment: Path) -> dict | None:
    """Identify a music recording in a 20-second clip; never log the API token."""
    file_data = segment.read_bytes()
    boundary, body = _multipart({'api_token': api_token, 'return': 'spotify,apple_music,deezer'},
                               file_data, 'audio-sample.wav')
    request = urllib.request.Request(
        AUDD_URL, data=body, method='POST',
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}',
                 'Content-Length': str(len(body))})
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        return {'_error': f'HTTP {exc.code}'}
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return {'_error': 'network_or_response_error'}
    if not isinstance(payload, dict):
        return {'_error': 'invalid_response'}
    status = str(payload.get('status') or '').lower()
    if status and status not in {'success', 'ok'}:
        return {'_error': 'provider_error'}
    result = payload.get('result')
    if not isinstance(result, dict) or not result.get('title'):
        return None
    title = str(result.get('title', '')).strip()[:180]
    artist = str(result.get('artist', '')).strip()[:180]
    if not title:
        return None
    # Keep only recognition fields. Provider URLs/IDs and credentials never enter the report.
    return {'title': title, 'artist': artist}


def recognize_music(ffmpeg: str, audio: Path, duration: float, api_token: str | None,
                    temp_dir: Path, maximum: int = 120) -> tuple[list[dict], list[tuple[float, float]], int]:
    """Scan overlapping audio samples with AudD and group repeated identifications."""
    windows = make_windows(duration, window_seconds=20, stride_seconds=15, maximum=maximum)
    if not api_token:
        return [], windows, 0
    hits = []
    errors = 0
    for index, (start, length) in enumerate(windows, 1):
        sample = temp_dir / f'music-{index:04d}.wav'
        try:
            convert_to_wav(ffmpeg, audio, sample, sample_rate=16000,
                           seek=start, duration=length)
            result = audd_identify(api_token, sample)
            if result and '_error' in result:
                errors += 1
                continue
            if result:
                hits.append({'start_sec': start, 'end_sec': start + length,
                             'title': result['title'], 'artist': result['artist']})
        except Exception:
            errors += 1
        if index < len(windows):
            time.sleep(0.15)
    return group_music_hits(hits), windows, errors


def _normalized_key(value: str) -> str:
    return re.sub(r'[^a-z0-9]+', ' ', value.lower()).strip()


def group_music_hits(hits: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for hit in hits:
        key = (_normalized_key(hit['artist']), _normalized_key(hit['title']))
        grouped[key].append(hit)
    result = []
    for rows in grouped.values():
        rows.sort(key=lambda item: item['start_sec'])
        title, artist = rows[0]['title'], rows[0]['artist']
        windows = []
        for row in rows:
            if windows and row['start_sec'] <= windows[-1][1]:
                windows[-1][1] = max(windows[-1][1], row['end_sec'])
            else:
                windows.append([row['start_sec'], row['end_sec']])
        result.append({'title': title, 'artist': artist,
                       'appearances': [{'start_sec': round(a, 2), 'end_sec': round(b, 2)}
                                       for a, b in windows]})
    return sorted(result, key=lambda item: item['appearances'][0]['start_sec'])


def local_audio_files(roots: list[Path]) -> list[tuple[Path, Path]]:
    files = []
    seen = set()
    for root in roots:
        if not root.exists() or not root.is_dir() or root.is_symlink():
            continue
        resolved_root = root.resolve()
        for path in sorted(root.rglob('*')):
            if (not path.is_file() or path.is_symlink() or path.suffix.lower() not in AUDIO_EXTENSIONS
                    or any(part.startswith('.') for part in path.relative_to(root).parts)):
                continue
            resolved = path.resolve()
            if not resolved.is_relative_to(resolved_root) or resolved in seen:
                continue
            seen.add(resolved)
            files.append((path, resolved_root))
    return files


def _read_pcm16_wav(path: Path):
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError('NumPy lipsește; compararea amprentelor audio este dezactivată.') from exc
    with wave.open(str(path), 'rb') as stream:
        if stream.getnchannels() != 1 or stream.getsampwidth() != 2:
            raise ValueError('Amprenta cere WAV mono PCM16.')
        rate = stream.getframerate()
        samples = np.frombuffer(stream.readframes(stream.getnframes()), dtype='<i2')
    return samples.astype(np.float32), rate


def audio_fingerprints(samples, sample_rate: int, frame_size: int = 512,
                       hop_size: int = 128) -> dict[tuple[int, int, int], list[int]]:
    """Small constellation fingerprint resilient to gain changes and light mixing."""
    import numpy as np
    values = np.asarray(samples, dtype=np.float32).reshape(-1)
    if values.size == 0 or sample_rate <= 0:
        return {}
    if values.size < frame_size:
        values = np.pad(values, (0, frame_size - values.size))
    frames = np.lib.stride_tricks.sliding_window_view(values, frame_size)[::hop_size]
    window = np.hanning(frame_size).astype(np.float32)
    spectra = np.abs(np.fft.rfft(frames * window, axis=1))
    low = max(1, int(120 * frame_size / sample_rate))
    high = min(spectra.shape[1] - 1, int(5000 * frame_size / sample_rate))
    if high <= low:
        return {}
    band = spectra[:, low:high]
    peaks_by_frame = []
    for row in band:
        candidates = np.argsort(row)[::-1]
        chosen = []
        for candidate in candidates:
            frequency_bin = int(candidate) + low
            if all(abs(frequency_bin - existing) >= 2 for existing in chosen):
                chosen.append(frequency_bin)
            if len(chosen) == 5:
                break
        peaks_by_frame.append(sorted(chosen))
    fingerprints: dict[tuple[int, int, int], list[int]] = defaultdict(list)
    for frame_index, peaks in enumerate(peaks_by_frame):
        for delta in (1, 2, 4, 6, 8):
            later = frame_index + delta
            if later >= len(peaks_by_frame):
                break
            for first in peaks:
                for second in peaks_by_frame[later]:
                    key = (first // 2, second // 2, delta)
                    # Cap repeated tonal hashes so they cannot dominate the match.
                    if len(fingerprints[key]) < 24:
                        fingerprints[key].append(frame_index)
    return dict(fingerprints)


def compare_fingerprints(reference: dict, target: dict, sample_rate: int,
                         hop_size: int = 128) -> dict | None:
    if not reference or not target:
        return None
    offsets = Counter()
    for fingerprint, reference_positions in reference.items():
        target_positions = target.get(fingerprint)
        if not target_positions:
            continue
        if len(reference_positions) * len(target_positions) > 200:
            continue
        for reference_frame in reference_positions:
            for target_frame in target_positions:
                # A 3-frame bin tolerates small encoder/timing differences.
                offset_bin = round((target_frame - reference_frame) / 3)
                offsets[offset_bin] += 1
    if not offsets:
        return None
    offset_bin, votes = offsets.most_common(1)[0]
    total = sum(len(positions) for positions in reference.values())
    score = min(1.0, votes / max(1, total))
    if votes < max(12, int(total * 0.06)) or score < 0.12:
        return None
    return {'score': round(score, 3), 'votes': int(votes),
            'offset_sec': round(offset_bin * 3 * hop_size / sample_rate, 2)}


def match_local_library(ffmpeg: str, audio: Path, duration: float, events: list[dict],
                        roots: list[Path], temp_dir: Path) -> tuple[int, str | None]:
    """Compare event neighbourhoods against local supplied sounds; originals stay untouched."""
    try:
        import numpy  # noqa: F401
    except ImportError:
        return 0, 'NumPy lipsește; potrivirea audio cu biblioteca locală a fost sărită.'
    files = local_audio_files(roots)
    if not files:
        return 0, 'Nu am găsit fișiere audio locale pentru comparație.'
    library = []
    for index, (path, root) in enumerate(files, 1):
        wav_path = temp_dir / f'library-{index:04d}.wav'
        try:
            convert_to_wav(ffmpeg, path, wav_path, sample_rate=11025)
            samples, rate = _read_pcm16_wav(wav_path)
            fingerprint = audio_fingerprints(samples, rate)
            if fingerprint:
                try:
                    display_path = path.relative_to(root).as_posix()
                except ValueError:
                    display_path = path.name
                library.append((display_path, fingerprint))
        except Exception:
            continue
    if not library:
        return 0, 'Fișierele bibliotecii nu au putut fi convertite pentru comparație.'
    checked = 0
    for event_index, event in enumerate(events, 1):
        if event['type'] not in {'sfx', 'meme'}:
            continue
        if event['confidence'] < 0.25:
            continue
        clip_start = max(0.0, event['start_sec'] - 1.5)
        clip_end = min(duration, max(event['end_sec'], event['start_sec'] + 0.25) + 1.5)
        if clip_end - clip_start > 9:
            clip_end = clip_start + 9
        segment = temp_dir / f'event-match-{event_index:04d}.wav'
        try:
            convert_to_wav(ffmpeg, audio, segment, sample_rate=11025,
                           seek=clip_start, duration=clip_end - clip_start)
            samples, rate = _read_pcm16_wav(segment)
            target_fingerprint = audio_fingerprints(samples, rate)
        except Exception:
            continue
        checked += 1
        matches = []
        for name, candidate in library:
            match = compare_fingerprints(candidate, target_fingerprint, rate)
            if match:
                matches.append({'name': name, **match,
                                'approx_sec': round(clip_start + max(0, match['offset_sec']), 2)})
        event['local_matches'] = sorted(matches, key=lambda item: item['score'], reverse=True)[:3]
    return checked, None


def _plain_text(value, maximum: int = 300) -> str:
    return re.sub(r'[\r\n\t]+', ' ', str(value)).strip()[:maximum]


def escape_markdown(value: str) -> str:
    text = _plain_text(value)
    for char in ('\\', '`', '*', '_', '{', '}', '[', ']', '<', '>', '|'):
        text = text.replace(char, '\\' + char)
    return text


def timestamp(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f'{hours}:{minutes:02d}:{seconds:02d}' if hours else f'{minutes}:{seconds:02d}'


def search_url(site: str, query: str) -> str:
    encoded = urllib.parse.quote_plus(query.strip())
    sites = {
        'YouTube': f'https://www.youtube.com/results?search_query={encoded}',
        'Freesound': f'https://freesound.org/search/?q={encoded}',
        'Pixabay': f'https://pixabay.com/sound-effects/search/{urllib.parse.quote(query.strip(), safe="")}/',
        'Spotify': f'https://open.spotify.com/search/{urllib.parse.quote(query.strip(), safe="")}',
        'Apple Music': f'https://music.apple.com/search?term={encoded}',
    }
    if site not in sites:
        raise ValueError('Sursă de căutare necunoscută')
    return sites[site]


def search_youtube(query: str, limit: int = 3) -> list[dict]:
    """Search YouTube titles only through yt-dlp; no audio/video is downloaded."""
    limit = min(5, max(1, int(limit)))
    safe_query = _plain_text(query, 120)
    if not safe_query:
        return []
    command = [sys.executable, '-m', 'yt_dlp', '--flat-playlist', '--dump-single-json',
               '--ignore-errors', '--no-warnings', '--no-progress', f'ytsearch{limit}:{safe_query}']
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=45, check=False)
        if result.returncode != 0 or not result.stdout.strip():
            return []
        payload = json.loads(result.stdout)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return []
    entries = payload.get('entries', []) if isinstance(payload, dict) else []
    found = []
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue
        video_id = entry.get('id')
        if not isinstance(video_id, str) or not VIDEO_ID_RE.fullmatch(video_id):
            continue
        found.append({'title': _plain_text(entry.get('title') or 'Titlu indisponibil', 180),
                      'channel': _plain_text(entry.get('channel') or entry.get('uploader') or '', 120),
                      'url': youtube_url(video_id)})
        if len(found) >= limit:
            break
    return found


def build_search_queries(events: list[dict], tracks: list[dict], maximum: int = 8) -> list[dict]:
    queries = []
    seen = set()
    for track in tracks:
        text = ' '.join(part for part in (track.get('artist', ''), track.get('title', ''), 'official audio') if part).strip()
        key = _normalized_key(text)
        if key and key not in seen:
            seen.add(key)
            queries.append({'kind': 'melodie identificată', 'query': text, 'music': True})
    priority = {'meme': 0, 'sfx': 1, 'ambience': 2, 'other': 3, 'music': 4}
    for event in sorted(events, key=lambda item: (priority.get(item['type'], 5), -item['confidence'])):
        if event['type'] not in {'sfx', 'meme', 'ambience'}:
            continue
        suffix = {'meme': 'meme sound effect', 'sfx': 'sound effect',
                  'ambience': 'ambient sound effect'}[event['type']]
        text = f"{event['label']} {suffix}".strip()
        key = _normalized_key(text)
        if key and key not in seen:
            seen.add(key)
            queries.append({'kind': event['type'], 'query': text, 'music': False})
        if len(queries) >= maximum:
            break
    return queries[:maximum]


def _track_markdown(track: dict) -> str:
    artist = escape_markdown(track.get('artist') or 'Artist necunoscut')
    title = escape_markdown(track.get('title') or 'Piesă necunoscută')
    times = ', '.join(f'{timestamp(span["start_sec"])}–{timestamp(span["end_sec"])} aprox.'
                      for span in track.get('appearances', [])) or 'timp necunoscut'
    query = f'{track.get("artist", "")} {track.get("title", "")}'.strip()
    links = ' · '.join(f'[{name}]({search_url(name, query)})'
                       for name in ('YouTube', 'Spotify', 'Apple Music'))
    return f'- **{times}** — {artist} — *{title}*. Recunoscut de serviciul de amprentare audio. {links}'


def render_report(source_display: str, video_url: str | None, duration: float,
                  events: list[dict], tracks: list[dict], search_data: list[dict],
                  ai_windows: list[tuple[float, float]], ai_successes: int,
                  music_windows: list[tuple[float, float]], music_errors: int,
                  gemini_enabled: bool, audd_enabled: bool, local_checked: int,
                  warnings: list[str]) -> str:
    location = f'[{escape_markdown(video_url)}]({video_url})' if video_url else f'`{escape_markdown(source_display)}`'
    ai_coverage = coverage_fraction(ai_windows, duration)
    music_coverage = coverage_fraction(music_windows, duration)
    lines = [
        '# Raport audio — videoclip de referință', '',
        f'- **Sursă:** {location}',
        f'- **Durată audio:** {timestamp(duration)}',
        f'- **Fragmente Gemini reușite:** {ai_successes}/{len(ai_windows)}',
        f'- **Acoperire AI planificată:** {ai_coverage:.0%} din video',
        (f'- **Probe AudD planificate:** {len(music_windows)} ({music_coverage:.0%} acoperire)' if audd_enabled
         else '- **Probe AudD efectuate:** 0 (lipsește tokenul opțional)'),
        f'- **Piese recunoscute:** {len(tracks)}',
        f'- **Evenimente audio descrise:** {len(events)}',
        f'- **Bibliotecă locală comparată:** {local_checked} fragmente SFX/meme', '',
        '> Identificările și timpii sunt automați. Muzica sub voce, sunetele foarte scurte sau editate pot fi ratate; '
        'ascultă fragmentele originale înainte de a le folosi.', '',
        '## Melodii identificate', '',
    ]
    if tracks:
        lines.extend(_track_markdown(track) for track in tracks)
    elif not audd_enabled:
        lines.append('Nu s-a putut căuta un titlu exact: lipsește `AUDD_API_TOKEN`. Gemini poate descrie muzica, dar nu confirmă singur numele piesei.')
    elif music_errors and not tracks:
        lines.append(f'Serviciul de recunoaștere nu a răspuns pentru {music_errors} probe; verifică tokenul/limita contului și încearcă din nou.')
    else:
        lines.append('Nicio piesă nu a fost identificată în probele audio. O melodie foarte încetă, remixată sau acoperită poate rămâne necunoscută.')
    lines.extend([
        '', '## Sunete, meme-uri și ambianță', '',
    ])
    if events:
        for event in events:
            kind = {'music': 'muzică', 'sfx': 'SFX', 'meme': 'meme',
                    'ambience': 'ambianță', 'other': 'alt sunet'}.get(event['type'], event['type'])
            background = ' · fundal' if event['background'] else ''
            confidence = f'{event["confidence"]:.0%} estimare AI'
            lines.append(f'- **{timestamp(event["start_sec"])}–{timestamp(event["end_sec"])}** · {kind}{background} · {confidence}: **{escape_markdown(event["label"])}**')
            if event['description']:
                lines.append(f'  - {escape_markdown(event["description"])}')
            for match in event.get('local_matches', []):
                lines.append(f'  - Posibilă potrivire în biblioteca ta: `{escape_markdown(match["name"])}` '
                             f'(scor amprentă {match["score"]:.0%}, aprox. {timestamp(match["approx_sec"])}). Ascultă și confirmă manual.')
    else:
        if gemini_enabled:
            lines.append('Gemini nu a returnat evenimente audio validate pentru fragmentele procesate; verifică avertizările și ascultă manual sursa.')
        else:
            lines.append('Nu sunt evenimente descrise de Gemini. Configurează `GEMINI_API_KEY` pentru analiza efectelor și a muzicii de fundal.')
    lines.extend(['', '## Căutări web și alternative de găsit', ''])
    if search_data:
        for item in search_data:
            query = item['query']
            lines.append(f'### {escape_markdown(item["kind"].title())}: {escape_markdown(query)}')
            if item.get('music'):
                lines.append(f"Căutări: [YouTube]({search_url('YouTube', query)}) · [Spotify]({search_url('Spotify', query)}) · [Apple Music]({search_url('Apple Music', query)})")
            else:
                lines.append(f"Căutări: [YouTube]({search_url('YouTube', query)}) · [Freesound]({search_url('Freesound', query)}) · [Pixabay]({search_url('Pixabay', query)})")
            results = item.get('results', [])
            if results:
                for result in results:
                    title = escape_markdown(result.get('title', 'Rezultat'))
                    channel = escape_markdown(result.get('channel') or 'canal necunoscut')
                    lines.append(f'- [{title}]({result["url"]}) — {channel}')
            else:
                lines.append('- Nu am primit rezultate automate de la YouTube; folosește linkurile de căutare de mai sus.')
            if not item.get('music'):
                lines.append('- Verifică licența și autorul pe pagina fiecărui efect înainte de descărcare sau publicare.')
            lines.append('')
    else:
        lines.append('Nu au fost generate căutări: nu s-au identificat etichete audio sau căutarea web a fost dezactivată.')
    lines.extend([
        '', '## Limite și confidențialitate', '',
        '- Pentru analiza Gemini sunt trimise fragmente audio, nu videoclipul complet. Pentru identificarea pieselor, fragmente de maximum 20 secunde sunt trimise către AudD doar dacă ai configurat `AUDD_API_TOKEN`.',
        '- AudD identifică doar piese prezente în catalogul său; nu garantează recunoașterea remixurilor, efectelor meme sau muzicii foarte joase.',
        '- Potrivirile din biblioteca locală sunt comparații acustice orientative, nu dovadă de identitate. Fără bibliotecă locală, efectele de pe internet nu pot fi potrivite exact doar după nume.',
        '- Linkurile și rezultatele YouTube/Freesound/Pixabay sunt piste de căutare, nu verificări de licență și nu fișiere descărcate.',
        '- Fișierele originale nu sunt modificate; audio temporar se șterge la finalul rulării.',
    ])
    if music_errors:
        lines.extend(['', f'**Notă tehnică:** {music_errors} probă/probe de recunoaștere muzicală au eșuat; conținutul răspunsurilor API nu a fost înregistrat.'])
    if warnings:
        lines.extend(['', '## Atenționări', ''])
        lines.extend(f'- {escape_markdown(warning)}' for warning in warnings)
    return '\n'.join(lines) + '\n'


def _default_output(video_id: str | None, local_path: Path | None) -> Path:
    label = video_id or re.sub(r'[^A-Za-z0-9_-]+', '_', local_path.stem if local_path else 'local')[:48]
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    return ROOT / 'episodes' / f'SUNETE_{label}_{stamp}.md'


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description='Identifică și caută melodiile, SFX-urile și meme-urile audio dintr-un videoclip.')
    parser.add_argument('source', help='link la un videoclip YouTube public sau cale către fișier video/audio local')
    parser.add_argument('--output', type=Path, help='raport Markdown (implicit: episodes/SUNETE_*.md)')
    parser.add_argument('--max-ai-chunks', type=int, default=180,
                        help='plafon de fragmente audio trimise la Gemini (implicit 180)')
    parser.add_argument('--max-music-checks', type=int, default=120,
                        help='plafon de probe trimise la AudD (implicit 120)')
    parser.add_argument('--search-results', type=int, default=3, choices=range(1, 6),
                        help='rezultate YouTube per căutare; nu descarcă fișiere')
    parser.add_argument('--max-search-queries', type=int, default=8,
                        help='număr maxim de căutări web automate')
    parser.add_argument('--no-web-search', action='store_true', help='nu interoga yt-dlp pentru rezultate; păstrează linkurile de căutare')
    parser.add_argument('--no-local-match', action='store_true', help='sari peste potrivirea cu sunetele locale')
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    source = args.source.strip()
    video_id = youtube_video_id(source)
    is_url = source.lower().startswith(('http://', 'https://'))
    if is_url and not video_id:
        print('Eroare: accept doar un link direct la un videoclip YouTube.', file=sys.stderr)
        return 2
    local_source = None if video_id else Path(source).expanduser().resolve()
    if local_source is not None and not local_source.is_file():
        print('Eroare: fișierul local nu a fost găsit.', file=sys.stderr)
        return 2
    display_source = youtube_url(video_id) if video_id else local_source.name
    source_url = youtube_url(video_id) if video_id else None
    ffmpeg = None
    try:
        ffmpeg = find_ffmpeg()
        with tempfile.TemporaryDirectory(prefix='autoeditor-sunete-') as temp_name:
            temp_dir = Path(temp_name)
            if video_id:
                print('1/5 Descarc numai pista audio YouTube în spațiu temporar...')
                audio_source = download_youtube_audio(source_url, temp_dir)
            else:
                audio_source = local_source
            normalized_audio = temp_dir / 'analysis.wav'
            convert_to_wav(ffmpeg, audio_source, normalized_audio, sample_rate=16000, normalize=True)
            duration = wav_duration(normalized_audio)
            print(f'   audio extras: {timestamp(duration)}')

            warnings = []
            gemini_key = read_secret('GEMINI_API_KEY')
            audd_token = read_secret('AUDD_API_TOKEN')
            models = _models_from_env()
            ai_windows = make_windows(duration, window_seconds=60, stride_seconds=50,
                                      maximum=args.max_ai_chunks)
            events_raw = []
            ai_successes = 0
            if gemini_key:
                print(f'2/5 Analizez fragmente audio cu Gemini ({len(ai_windows)} ferestre)...')
                for index, (start, length) in enumerate(ai_windows, 1):
                    segment = temp_dir / f'ai-{index:04d}.wav'
                    try:
                        convert_to_wav(ffmpeg, normalized_audio, segment, sample_rate=16000,
                                       seek=start, duration=length)
                        _, result = analyze_audio_with_gemini(gemini_key, models, segment, start, length)
                        events_raw.extend(parse_audio_events(result, start, length))
                        ai_successes += 1
                    except Exception as exc:
                        warnings.append(f'Gemini nu a analizat fragmentul {timestamp(start)} ({type(exc).__name__}).')
                    if index < len(ai_windows):
                        time.sleep(0.1)
            else:
                warnings.append('Lipsește GEMINI_API_KEY; nu s-a făcut etichetarea AI a efectelor audio.')
            events = merge_audio_events(events_raw)

            print('3/5 Caut melodii recunoscibile...')
            tracks, music_windows, music_errors = recognize_music(
                ffmpeg, normalized_audio, duration, audd_token, temp_dir,
                maximum=args.max_music_checks)
            if not audd_token:
                warnings.append('Lipsește AUDD_API_TOKEN; titlurile exacte ale melodiilor nu pot fi confirmate automat.')

            local_checked = 0
            if not args.no_local_match:
                roots = [ROOT / 'sunete_mele', ROOT / 'sunete_virale',
                         ROOT / 'assets' / 'efecte', ROOT / 'assets' / 'meme']
                local_checked, note = match_local_library(ffmpeg, normalized_audio, duration,
                                                          events, roots, temp_dir)
                if note:
                    warnings.append(note)
            else:
                warnings.append('Potrivirea audio cu biblioteca locală a fost dezactivată prin opțiune.')

            print('4/5 Caut surse și sunete similare pe web...')
            queries = build_search_queries(events, tracks, maximum=max(0, args.max_search_queries))
            search_data = []
            for index, item in enumerate(queries, 1):
                results = [] if args.no_web_search else search_youtube(item['query'], args.search_results)
                search_data.append({**item, 'results': results})
                if not args.no_web_search and index < len(queries):
                    time.sleep(0.15)

            report = render_report(
                display_source, source_url, duration, events, tracks, search_data,
                ai_windows, ai_successes, music_windows, music_errors,
                gemini_enabled=bool(gemini_key), audd_enabled=bool(audd_token),
                local_checked=local_checked, warnings=warnings)
            output = args.output.expanduser().resolve() if args.output else _default_output(video_id, local_source)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(report, encoding='utf-8')
            print(f'5/5 Raport salvat: {output}')
            print(f'   {len(tracks)} melodii identificate · {len(events)} evenimente · {len(search_data)} căutări')
            return 0
    except (RuntimeError, ValueError) as exc:
        # Never print provider response bodies or credential-bearing URLs.
        print(f'Eroare: {exc}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('Analiza a fost oprită; fișierele temporare vor fi șterse.', file=sys.stderr)
        return 130


if __name__ == '__main__':
    raise SystemExit(main())
