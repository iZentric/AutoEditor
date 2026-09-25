"""Strict editorial decisions. No network, media mutation or random choices here."""
import math
import json
from performance import file_digest
import re
from pathlib import Path

AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac', '.opus'}


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError('Expected a JSON number')
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('Expected a finite number')
    return value


def transcript_pages(transcript, budget=18000, overlap=2000):
    """Cover every utterance, including the end of a long VOD; overlap page edges."""
    text = '\n'.join(f'{float(a):.2f}-{float(b):.2f}s {t}' for a, b, t in transcript)
    if not 0 <= overlap < budget:
        raise ValueError('Invalid transcript page budget')
    start = 0
    while start < len(text):
        end = min(len(text), start + budget)
        yield text[start:end]
        if end == len(text):
            break
        start = end - overlap


def sound_catalogue(roots, classify):
    """Stable IDs; only files actually present. Never delete/split creator originals."""
    indexed = {}
    defaults = {'cadere': ['cadere', 'impact_personaj'], 'hit': ['lovitura_comica'],
                'speriat': ['sperietura'], 'fericit': ['victorie', 'descoperire']}
    for root in roots:
        root = Path(root).resolve()
        manifest_path = root / 'catalog.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8')).get('sounds', {}) if manifest_path.is_file() else {}
        if not isinstance(manifest, dict):
            raise ValueError('Invalid sound catalogue')
        for path in sorted(root.rglob('*')):
            if (not path.is_file() or path.is_symlink() or path.suffix.lower() not in AUDIO_EXTENSIONS
                    or any(part.startswith('.') for part in path.relative_to(root).parts)):
                continue
            resolved = path.resolve()
            if not resolved.is_relative_to(root):
                continue
            card = manifest.get(path.relative_to(root).as_posix(), {})
            category = card.get('category', classify(str(path)))
            events = card.get('events', defaults.get(category, []))
            if not isinstance(events, list) or any(not isinstance(e, str) for e in events):
                raise ValueError('Invalid sound event rules')
            indexed[resolved] = {
                'path': str(resolved), 'name': path.name, 'category': category,
                'events': events, 'description': card.get('description', 'Sens dedus numai din nume/categorie.'),
                'avoid': card.get('avoid', 'Omite daca sensul este ambiguu.'),
                'identity_source': card.get('identity_source', 'filename_hint'),
                'sha256': file_digest(resolved)}
    return {f'S{n:03d}': indexed[p] for n, p in enumerate(sorted(indexed), 1)}


def public_catalogue(catalogue):
    return {key: {k: v[k] for k in ('name', 'category', 'events', 'description', 'avoid',
                                    'identity_source', 'sha256') if k in v}
            for key, v in catalogue.items()}


def validate_review(review, duration):
    """Missing, ambiguous and weak verdicts must never become publishable episodes."""
    if not isinstance(review, dict):
        raise ValueError('Raspunsul verificarii nu este un obiect JSON')
    for field in ('ok', 'un_joc', 'poveste_completa', 'titlu_sustinut'):
        if review.get(field) is not True:
            raise ValueError(f'Neconfirmat: {field}')
    score = number(review.get('scor'))
    if not 7 <= score <= 10:
        raise ValueError('Scor editorial sub 7/10 sau invalid')
    title = review.get('titlu_corectat')
    if (not isinstance(title, str) or not 4 <= len(title.strip()) <= 70
            or '\n' in title or re.search(r'\bep\.?\s*\d+', title, re.I)):
        raise ValueError('Titlu lipsa sau invalid')
    hook = number(review.get('hook_sec'))
    if not 0 <= hook < duration:
        raise ValueError('Momentul principal nu este in clip')
    story = review.get('poveste')
    if not isinstance(story, dict):
        raise ValueError('Lipseste dovada povestii')
    for part in ('inceput', 'desfasurare', 'final'):
        if not isinstance(story.get(part), str) or not story[part].strip():
            raise ValueError(f'Lipseste: {part}')
    if not isinstance(review.get('ce_se_intampla'), str) or not review['ce_se_intampla'].strip():
        raise ValueError('Lipseste descrierea evenimentului vizibil')
    return score, title.strip(), hook


def validate_sounds(proposals, catalogue, duration):
    """Reject unknown IDs, weak evidence, bad timing, repetition and crowded effects."""
    accepted, rejected = [], []
    if not isinstance(proposals, list):
        return [], ['Plan de sunete invalid; niciun efect adaugat']
    for proposal in proposals:
        try:
            if not isinstance(proposal, dict):
                raise ValueError('Efect invalid')
            sid = proposal.get('id')
            if sid not in catalogue:
                raise ValueError('Sunet inexistent')
            allowed = catalogue[sid].get('events')
            if allowed is not None and proposal.get('eveniment') not in allowed:
                raise ValueError('Sunet nepotrivit pentru tipul evenimentului')
            t = number(proposal.get('sec'))
            confidence = number(proposal.get('incredere'))
            reason = proposal.get('motiv')
            if not 0.85 <= confidence <= 1 or not isinstance(reason, str) or not reason.strip():
                raise ValueError('Eveniment insuficient confirmat')
            if not 1 <= t <= duration - 3:
                raise ValueError('Sunet in afara intervalului sigur')
            if len(accepted) >= 6 or any(abs(t - s['sec']) < 9 for s in accepted):
                raise ValueError('Prea multe efecte sau prea apropiate')   # creatorul vrea sunetele lui CAT MAI DES (25.09)
            if any(s['id'] == sid for s in accepted):
                raise ValueError('Acelasi efect repetat')
            if catalogue[sid]['category'] == 'hit' and any(
                    catalogue[s['id']]['category'] == 'hit' for s in accepted):
                raise ValueError('Maximum o lovitura comica pe episod')
            accepted.append({'id': sid, 'sec': t, 'motiv': reason.strip()[:400],
                             'path': catalogue[sid]['path'], 'incredere': confidence,
                             'eveniment': proposal.get('eveniment')})
        except (ValueError, TypeError) as ex:
            rejected.append(str(ex))
    return sorted(accepted, key=lambda s: s['sec']), rejected


def approved_episodes(ideas, verify, catalogue, live_len, maximum, transcript=None):
    """Verify exact continuous cuts. No fallback on API failure or an empty result."""
    approved, audit = [], []
    for idea in ideas:
        if len(approved) >= maximum:
            break
        entry = {'idee': idea}
        audit.append(entry)
        try:
            start, end = number(idea.get('inceput')), number(idea.get('sfarsit'))
            if not (0 <= start < end <= live_len and 150 <= end - start <= 170):
                raise ValueError('Interval invalid: episodul trebuie sa aiba 150-170s')
            if any(start < e['scene'][0][0] + e['scene'][0][1]
                   and end > e['scene'][0][0] for e in approved):
                raise ValueError('Se suprapune cu o poveste deja aprobata')
            review = verify(idea)
            entry['verificare'] = review
            score, title, hook = validate_review(review, end - start)
            sounds, skipped = validate_sounds(review.get('sunete', []), catalogue, end - start)
            entry.update(status='aprobat', sunete=sounds, sunete_respinse=skipped)
            approved.append({'varf': start + hook, 'scor': score, 'ai_scor': score,
                             'tip': 'clasic', 'scene': [(start, end - start)],
                             'ai_titlu': title, 'ai_de_ce': str(idea.get('de_ce', '')),
                             'ai_in_joc': review['ce_se_intampla'], 'ai_livrat': True,
                             'ai_verified': True, 'poveste': review['poveste'],
                             '_sound_plan': sounds,
                             '_pops': selected_pops(review.get('replici_pop', []),
                                                    quote_catalogue(transcript, start, end))})
        except ValueError as ex:
            entry.update(status='respins', motiv=str(ex))
        except Exception as ex:
            # Exception strings from HTTP clients can contain credentials/URLs.
            entry.update(status='neverificat', motiv=f'Verificare indisponibila: {type(ex).__name__}')
    return approved, audit


def sound_filter(index, timestamp, label):
    """Brief accents below speech, normalized before mixing (not raw asset volume)."""
    return (f'[{index}:a]atrim=duration=2,asetpts=PTS-STARTPTS,'
            'loudnorm=I=-24:TP=-6:LRA=7,aresample=48000,'
            f'afade=t=out:st=1.7:d=0.3,adelay={int(timestamp * 1000)}:all=1[{label}]')


def quote_catalogue(transcript, start, end):
    """Only short, verbatim transcript quotes can become on-screen POP captions."""
    quotes = {}
    for a, b, text in transcript or []:
        text = str(text).strip()
        relative = float(a) - start
        if (start <= a < b <= end and 2 <= relative <= end - start - 5
                and 8 <= len(text) <= 65 and len(text.split()) >= 2
                and not any(c in text for c in ('{', '}', '\\', '\n', '\r'))):
            quotes[f'R{len(quotes)+1:03d}'] = {'sec': relative, 'text': text}
    return quotes


def selected_pops(ids, quotes):
    selected = []
    if not isinstance(ids, list):
        return selected
    for key in ids:
        if not isinstance(key, str) or key not in quotes:
            continue
        quote = quotes[key]
        if len(selected) >= 6 or any(abs(quote['sec'] - t) < 18 for t, _ in selected):
            continue
        selected.append((quote['sec'], quote['text']))
    return sorted(selected)
