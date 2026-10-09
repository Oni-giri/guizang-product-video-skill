#!/usr/bin/env python3
"""Narration for a film plan: synthesize each line, level-match the voice, time it to the shots, assemble one stem.

    python3 narrate.py plan.json                 # synthesize missing/changed lines, measure, place, write assets/narration.wav
    python3 narrate.py plan.json --fit-shots     # also lengthen shots that are too short for their line (shifts later shots, cues, duration)
    python3 narrate.py plan.json --time-from-voice   # narrated shots take exactly lead + speech + tail (grow or shrink, never below minShot)
    python3 narrate.py plan.json --dry-run       # measure existing files and report fit; writes nothing, exit 1 when lines do not fit
    python3 narrate.py --engines                 # list engines and what they need

plan.narration:
  enabled       true
  language      BCP-47 tag; defaults to typography.language
  voice         {engine, id, speed, style, model, outputFormat, settings}  engines: edge | openai | elevenlabs | piper | say | file
  lead          seconds between the shot start and the first word (default 0.35)
  tail          seconds of air between the last word and the cut (default 0.6)
  gap           minimum silence between two lines in one shot (default 0.3)
  targetRms     dBFS RMS of the spoken part of every line before compression (default -20); intensity strong/soft moves it ±1.5 dB
  duck          {db, attack, release} music reduction under speech (default 9 dB, 0.15 s, 0.6 s)
  captions      true: the starter renders each line as a caption bar while it is spoken
  minShot       shortest a narrated shot may become with --time-from-voice (default 2.0 s)
  lines[]       {id, shotId, text, captionText?, lead?, pace?, intensity?, pauseAfter?, file?, mark?, sfx?, action?}
                narrate.py writes back: file, duration, speechStart, speechEnd, start, end, at, textSha256, engine

Marks pin picture to words: a line with "mark": "price" writes shot.marks.price = seconds after the shot start at which
that sentence begins; shot code reads it (markAt(id, 'price') in the starter) and lands the visual on the word.
A line with "sfx": "pop" (and an "action" description) adds a sound beat at that moment: an action on the shot and a
cue on assets/sfx/<sfx>.wav whose measured landmark lands on the first word.
`line.at` is the sentence onset relative to the shot start. `start` is where the source file would begin so that its
first word lands on time; it can be negative when the file has more pre-roll than `lead`. The stem is built from the
trimmed spoken part, so pre-roll never plays.

Timing rule (the one broadcast editors use): the voice starts a beat after the picture changes, and the picture stays
a beat after the voice stops. Lines never run into the next shot; --fit-shots stretches the shot instead.
After narrate.py changes the plan, rebuild the film (npm run build): plan.json is baked into the bundle.
Only needs FFmpeg plus the chosen engine.
"""
import argparse
import hashlib
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_delivery import spoken_words  # noqa: E402  (one pacing rule for narrate.py and check_delivery.py)
from sfx_landmarks import landmarks as sfx_landmarks  # noqa: E402  (sound beats land their measured landmark on the word)

RATE = 48000
WINDOW = 480                     # 10 ms analysis windows
MIN_VOICED = 6                   # a voiced run must last 60 ms to count as speech (clicks and pops do not)
DEFAULTS = {'lead': 0.35, 'tail': 0.6, 'gap': 0.3, 'targetRms': -20.0, 'minShot': 2.0}
PEAK_ALIGNED = {'whoosh', 'sweep', 'ding-dong', 'success', 'error', 'resolve'}   # these are heard at their peak; clicks at their onset
MARK = re.compile(r'^[A-Za-z][A-Za-z0-9_-]{0,31}$')
DUCK = {'db': 9.0, 'attack': 0.15, 'release': 0.6}
INTENSITY_DB = {'strong': 1.5, 'normal': 0.0, 'soft': -1.5}
EDGE_VOICES = {'en': 'en-US-AndrewMultilingualNeural', 'fr': 'fr-FR-DeniseNeural', 'de': 'de-DE-KatjaNeural', 'es': 'es-ES-ElviraNeural',
               'it': 'it-IT-ElsaNeural', 'pt': 'pt-BR-FranciscaNeural', 'ja': 'ja-JP-NanamiNeural', 'ko': 'ko-KR-SunHiNeural', 'zh': 'zh-CN-XiaoxiaoNeural', 'nl': 'nl-NL-ColetteNeural'}
STYLE_HINTS = {
    'strong': 'Confident, energetic, slightly faster, clear emphasis on the key word.',
    'normal': 'Warm, clear, conversational product narration; even pace; no sales voice.',
    'soft': 'Calm, quieter, unhurried; a reflective closing line.',
}
LINE_ID = re.compile(r'^[A-Za-z0-9_-]{1,64}$')


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def finite(x): return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
def run(args, **kw): return subprocess.run(args, check=True, capture_output=True, text=True, encoding='utf-8', **kw)
def ffmpeg(*args): return run(['ffmpeg', '-v', 'error', '-y', *args])
def posix(path, base): return Path(os.path.relpath(path, base)).as_posix()


def write_json(path, data):
    """Atomic UTF-8 write: a failure half-way never leaves a truncated plan."""
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, path)


def http_post(url, body, headers, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers={'Content-Type': 'application/json', **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.read()
    except urllib.error.HTTPError as e:
        detail = e.read(500).decode('utf-8', 'replace') if hasattr(e, 'read') else ''
        raise ValueError(f'{url}: HTTP {e.code} {e.reason}: {detail}')


def to_wav(src, out):
    """Any decodable audio → 48 kHz mono 16-bit WAV; the source is removed afterwards."""
    try: ffmpeg('-i', str(src), '-ac', '1', '-ar', str(RATE), '-c:a', 'pcm_s16le', str(out))
    finally: Path(src).unlink(missing_ok=True)


# ---------------------------------------------------------------- engines
def engine_edge(text, out, voice, language, intensity='normal'):
    exe = shutil.which('edge-tts') or shutil.which('edge-tts.exe')
    if not exe: raise ValueError('edge engine: install with `pip install edge-tts` (free Microsoft neural voices, needs network)')
    voice_id = voice.get('id') or EDGE_VOICES.get(language.split('-')[0].lower())
    if not voice_id: raise ValueError(f'edge engine: no default voice for language {language}; set narration.voice.id (see `edge-tts --list-voices`)')
    rate = round((float(voice.get('speed', 1.0)) - 1) * 100)
    tmp = out.with_suffix('.dl')
    with tempfile.NamedTemporaryFile('w', suffix='.txt', encoding='utf-8', delete=False) as f: f.write(text); script = f.name
    try: run([exe, f'--voice={voice_id}', f'--rate={rate:+d}%', f'--file={script}', f'--write-media={tmp}'])   # `=` form: a negative rate is not an option
    finally: Path(script).unlink(missing_ok=True)
    to_wav(tmp, out)
    return {'voice': voice_id, 'rate': f'{rate:+d}%'}


def engine_openai(text, out, voice, language, intensity='normal'):
    key = os.environ.get('OPENAI_API_KEY')
    if not key: raise ValueError('openai engine: set OPENAI_API_KEY')
    model = voice.get('model', 'gpt-4o-mini-tts')
    body = {'model': model, 'voice': voice.get('id') or 'alloy', 'input': text, 'response_format': 'wav', 'speed': float(voice.get('speed', 1.0))}
    if model.startswith('gpt-4o'):   # tts-1 / tts-1-hd do not take instructions
        hints = [voice.get('style'), STYLE_HINTS.get(intensity)]
        body['instructions'] = f'Narration for a software product video in {language}. ' + ' '.join(h for h in hints if h)
    data = http_post('https://api.openai.com/v1/audio/speech', body, {'Authorization': 'Bearer ' + key})
    tmp = out.with_suffix('.dl'); tmp.write_bytes(data)
    to_wav(tmp, out)
    return {'voice': body['voice'], 'model': model, 'instructions': body.get('instructions')}


def engine_elevenlabs(text, out, voice, language, intensity='normal'):
    key = os.environ.get('ELEVENLABS_API_KEY')
    if not key: raise ValueError('elevenlabs engine: set ELEVENLABS_API_KEY')
    if not voice.get('id'): raise ValueError('elevenlabs engine: narration.voice.id must be a voice id from your ElevenLabs library')
    speed = min(1.2, max(0.7, float(voice.get('speed', 1.0))))   # the API accepts 0.7–1.2
    settings = {'stability': {'strong': 0.4, 'normal': 0.55, 'soft': 0.7}[intensity], 'similarity_boost': 0.8,
                'style': 0.35 if intensity == 'strong' else 0.15, 'speed': speed}
    settings.update(voice.get('settings', {}))
    fmt = voice.get('outputFormat', 'mp3_44100_128')   # available on every tier; pcm_* needs a paid plan
    body = {'text': text, 'model_id': voice.get('model', 'eleven_multilingual_v2'), 'voice_settings': settings}
    data = http_post(f'https://api.elevenlabs.io/v1/text-to-speech/{voice["id"]}?output_format={fmt}', body, {'xi-api-key': key, 'Accept': '*/*'})
    tmp = out.with_suffix('.dl'); tmp.write_bytes(data)
    if fmt.startswith('pcm_'):
        try: ffmpeg('-f', 's16le', '-ar', fmt.split('_')[1], '-ac', '1', '-i', str(tmp), '-ar', str(RATE), '-c:a', 'pcm_s16le', str(out))
        finally: tmp.unlink(missing_ok=True)
    else: to_wav(tmp, out)
    return {'voice': voice['id'], 'model': body['model_id'], 'settings': settings, 'outputFormat': fmt}


def engine_piper(text, out, voice, language, intensity='normal'):
    exe = shutil.which('piper')
    if not exe: raise ValueError('piper engine: install the piper CLI and a voice model (https://github.com/rhasspy/piper)')
    if not voice.get('id'): raise ValueError('piper engine: narration.voice.id must be the path to a .onnx voice model')
    tmp = out.with_suffix('.dl')
    run([exe, '--model', str(voice['id']), '--length_scale', str(round(1 / float(voice.get('speed', 1.0)), 3)), '--output_file', str(tmp)], input=text)
    to_wav(tmp, out)
    return {'voice': voice['id']}


def engine_say(text, out, voice, language, intensity='normal'):
    exe = shutil.which('say')
    if not exe: raise ValueError('say engine: only available on macOS')
    tmp = out.with_suffix('.aiff')
    args = [exe, '-o', str(tmp), '-r', str(round(175 * float(voice.get('speed', 1.0))))]
    if voice.get('id'): args += ['-v', str(voice['id'])]
    run([*args, '--', text])
    to_wav(tmp, out)
    return {'voice': voice.get('id') or 'system default'}


def engine_file(text, out, voice, language, intensity='normal'):
    raise ValueError('file engine: record or generate the audio yourself and set line.file; narrate.py only measures and places it')


ENGINES = {
    'edge': (engine_edge, 'free Microsoft neural voices through the edge-tts CLI (pip install edge-tts); needs network'),
    'openai': (engine_openai, 'OpenAI speech API (OPENAI_API_KEY); voice.style plus line.intensity become the instructions prompt (gpt-4o models)'),
    'elevenlabs': (engine_elevenlabs, 'ElevenLabs API (ELEVENLABS_API_KEY, voice.id required); intensity maps to stability/style; mp3 output by default'),
    'piper': (engine_piper, 'local Piper CLI with an .onnx voice model (voice.id = model path); offline'),
    'say': (engine_say, 'macOS built-in `say`; quick drafts, not release quality'),
    'file': (engine_file, 'you supply the audio per line (a recording or any other TTS); narrate.py measures, level-matches and places it'),
}


# ---------------------------------------------------------------- measurement
def samples(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '1', '-ar', str(RATE), '-f', 's16le', '-'], capture_output=True, check=True).stdout
    return struct.unpack('<%dh' % (len(raw) // 2), raw)


def measure(path):
    """Duration, where speech actually starts/ends (a voiced run of at least 60 ms; isolated clicks do not count),
    RMS level of the voiced windows, peak."""
    x = samples(path)
    if len(x) < WINDOW * MIN_VOICED: raise ValueError(f'{path}: too short to contain speech')
    rms = [math.sqrt(sum(v * v for v in x[i:i + WINDOW]) / WINDOW) / 32768 for i in range(0, len(x) - WINDOW + 1, WINDOW)]
    peak = max(abs(v) for v in x) / 32768
    loudest = max(rms)
    if loudest < 10 ** (-45 / 20): raise ValueError(f'{path}: too quiet to be narration (loudest 10 ms window below -45 dBFS)')
    gate = max(loudest * 0.08, 10 ** (-45 / 20))            # 22 dB under the loudest window, never below -45 dBFS
    voiced = [v >= gate for v in rms]
    runs = [i for i in range(len(voiced) - MIN_VOICED + 1) if all(voiced[i:i + MIN_VOICED])]
    if not runs: raise ValueError(f'{path}: no sustained speech found (only clicks or noise)')
    first, last = runs[0], runs[-1] + MIN_VOICED - 1
    level = math.sqrt(sum(v * v for v, on in zip(rms[first:last + 1], voiced[first:last + 1]) if on) / max(1, sum(voiced[first:last + 1])))
    return {'duration': round(len(x) / RATE, 3), 'speechStart': round(first * WINDOW / RATE, 3), 'speechEnd': round((last + 1) * WINDOW / RATE, 3),
            'rmsDbfs': round(20 * math.log10(level), 1), 'peakDbfs': round(20 * math.log10(peak), 1) if peak > 0 else None}


# ---------------------------------------------------------------- planning
def settings(narration):
    s = dict(DEFAULTS)
    for k in s:
        if k in narration:
            if not finite(narration[k]): raise ValueError(f'narration.{k} must be a number')
            s[k] = narration[k]
    if s['lead'] < 0 or s['tail'] < 0 or s['gap'] < 0 or s['minShot'] < 0: raise ValueError('narration.lead/tail/gap/minShot must be >= 0')
    if not -30 <= s['targetRms'] <= -10: raise ValueError('narration.targetRms must be between -30 and -10 dBFS')
    override = narration.get('duck', {})
    if override is None: override = {}
    if not isinstance(override, dict): raise ValueError('narration.duck must be an object')
    duck = dict(DUCK); duck.update(override)
    for k in duck:
        if not finite(duck[k]): raise ValueError(f'narration.duck.{k} must be a number')
    if not 0 <= duck['db'] <= 18 or not 0.02 <= duck['attack'] <= 1 or not 0.05 <= duck['release'] <= 3: raise ValueError('narration.duck outside useful bounds')
    s['duck'] = duck
    return s


def validate_lines(lines, shot_ids):
    seen = set()
    for line in lines:
        if not isinstance(line, dict): raise ValueError('every narration line must be an object')
        for key in ['id', 'shotId', 'text']:
            if not isinstance(line.get(key), str) or not line[key].strip(): raise ValueError(f'every narration line needs a non-empty {key}')
        if not LINE_ID.match(line['id']): raise ValueError(f'line id {line["id"]!r} must be letters, digits, - or _ (it names a file)')
        if line['id'] in seen: raise ValueError(f'duplicate narration line id {line["id"]}')
        seen.add(line['id'])
        if line['shotId'] not in shot_ids: raise ValueError(f'line {line["id"]} refers to unknown shot {line["shotId"]}')
        if line.get('intensity', 'normal') not in INTENSITY_DB: raise ValueError(f'line {line["id"]}: intensity must be strong, normal or soft')
        for key, lo, hi in [('lead', 0, 10), ('pauseAfter', 0, 10), ('pace', 0.5, 2)]:
            if key in line and (not finite(line[key]) or not lo <= line[key] <= hi): raise ValueError(f'line {line["id"]}: {key} must be a number in [{lo}, {hi}]')
        if 'mark' in line and (not isinstance(line['mark'], str) or not MARK.match(line['mark'])): raise ValueError(f'line {line["id"]}: mark must be a short identifier (letters, digits, - or _)')
        if 'sfx' in line and (not isinstance(line['sfx'], str) or not LINE_ID.match(line['sfx'])): raise ValueError(f'line {line["id"]}: sfx must name a file in assets/sfx/ (without .wav)')
    marks = {}
    for line in lines:
        if line.get('mark'):
            key = (line['shotId'], line['mark'])
            if key in marks: raise ValueError(f'mark {line["mark"]} is used twice in shot {line["shotId"]} ({marks[key]} and {line["id"]})')
            marks[key] = line['id']


def place(plan, narration, measured, conf, fit, from_voice=False):
    """Place every line so speech begins lead seconds into its shot and ends tail seconds before the cut.
    fit=True: shots that are too short grow. from_voice=True: every narrated shot becomes exactly lead + speech + tail
    (never shorter than minShot); un-narrated shots keep their length. Later shots, cues and the duration shift either
    way. Shot boundaries snap to whole frames. Writes shot.marks from lines that carry a mark. Returns (placements, shifts, problems)."""
    shots = plan['shots']; fps = plan.get('fps') or 30
    snap_up = lambda t: round(math.ceil(t * fps - 1e-6) / fps, 4)   # a cut lands on a whole frame, never before the air the voice needs
    problems = []; placements = {}
    per_shot = {}
    for line in narration['lines']: per_shot.setdefault(line['shotId'], []).append(line)
    shift = 0.0; shifts = {}
    for shot in shots:
        original_start, original_end = shot['start'], shot['end']
        shot['start'] = round(original_start + shift, 4); shot['end'] = round(original_end + shift, 4)
        lines = per_shot.get(shot['id'], [])
        cursor = shot['start']; needed = shot['start']; marks = {}
        for line in lines:
            m = measured[line['id']]
            onset = max(shot['start'] + line.get('lead', conf['lead']), cursor)
            end_of_speech = onset + (m['speechEnd'] - m['speechStart'])
            needed = max(needed, end_of_speech + conf['tail'])
            file_start = round(onset - m['speechStart'], 3)
            placements[line['id']] = {'start': file_start, 'end': round(file_start + m['duration'], 3), 'speechOnset': round(onset, 3), 'speechOff': round(end_of_speech, 3),
                                      'at': round(onset - shot['start'], 3)}
            if line.get('mark'): marks[line['mark']] = round(onset - shot['start'], 3)
            cursor = end_of_speech + line.get('pauseAfter', conf['gap'])
        if lines:
            if from_voice:
                new_end = snap_up(max(needed, shot['start'] + conf['minShot']))
                shift += new_end - shot['end']; shot['end'] = new_end
            elif needed > shot['end'] + 1e-6:
                if fit:
                    new_end = snap_up(needed); shift += new_end - shot['end']; shot['end'] = new_end
                else:
                    late = [l['id'] for l in lines if placements[l['id']]['speechOff'] + conf['tail'] > shot['end'] + 1e-6]
                    problems.append(f"{', '.join(late)}: speech ends {needed - shot['end']:.2f}s too late for shot {shot['id']} "
                                    f"(needs end >= {needed:.2f}s, has {shot['end']:.2f}s); shorten the line or run --fit-shots / --time-from-voice")
            shot['marks'] = marks            # owned by narrate.py: picture beats pinned to sentence onsets
        shift = round(shift, 4)
        shifts[shot['id']] = round(shot['start'] - original_start, 4)
    if shift:
        plan['duration'] = round(plan['duration'] + shift, 4)
        audio = plan.get('audio', {}); actions = {}
        for s in shots:
            for a in s.get('actions', []): actions[a.get('id')] = s['id']
        for cue in audio.get('cues', []) if isinstance(audio, dict) else []:
            sid = actions.get(cue.get('actionId'))
            if sid in shifts and finite(cue.get('at')): cue['at'] = round(cue['at'] + shifts[sid], 4)
    return placements, shifts, problems


def sound_beats(plan, narration, placements, base):
    """Lines with "sfx" become an action on their shot and a cue whose measured landmark lands on the first word.
    Re-runs replace the beats they created earlier (ids end in -sfx)."""
    audio = plan.setdefault('audio', {}); cues = audio.setdefault('cues', [])
    by_shot = {s['id']: s for s in plan['shots']}
    created = []
    for line in narration['lines']:
        kind = line.get('sfx')
        if not kind: continue
        shot = by_shot[line['shotId']]; aid = f'{line["id"]}-sfx'
        file = Path('assets/sfx') / f'{kind}.wav'
        if not (base / file).is_file(): raise ValueError(f'line {line["id"]}: sfx "{kind}" needs {file.as_posix()} in the project (copy it from the skill\'s assets/audio/sfx or your sample library)')
        lm = sfx_landmarks(base / file)
        offset = lm['peak'] if kind.split('-')[0] in PEAK_ALIGNED or kind in PEAK_ALIGNED else lm['onset']
        at = placements[line['id']]['at']
        actions = [a for a in shot.get('actions', []) if a.get('id') != aid]
        actions.append({'id': aid, 'at': at, 'action': line.get('action') or f'picture changes on "{line["text"][:40]}"', 'soundRequired': True})
        shot['actions'] = sorted(actions, key=lambda a: a.get('at', 0))
        cue_at = round(shot['start'] + at - offset, 3)
        if cue_at < 0: raise ValueError(f'line {line["id"]}: the {kind} landmark ({offset}s) starts before the film; give the first line more lead')
        cues[:] = [c for c in cues if c.get('actionId') != aid]
        cues.append({'at': cue_at, 'syncOffset': offset, 'actionId': aid, 'file': file.as_posix(), 'gain': line.get('sfxGain', 1.0), 'role': 'sfx', 'kind': kind})
        created.append(aid)
    cues.sort(key=lambda c: c.get('at', 0))
    return created


def assemble(base, narration, measured, placements, conf, duration, out):
    """One stereo float stem: only the spoken part of each file (plus a short margin), gained to the target RMS,
    placed so the first word lands at its onset, lightly compressed and limited. Pre-roll and tail room tone never play."""
    inputs = []; filters = []
    for i, line in enumerate(narration['lines']):
        m = measured[line['id']]; p = placements[line['id']]
        target = conf['targetRms'] + INTENSITY_DB.get(line.get('intensity', 'normal'), 0)
        gain_db = max(-24, min(24, target - m['rmsDbfs']))
        cut_in = max(0.0, m['speechStart'] - 0.05); cut_out = min(m['duration'], m['speechEnd'] + 0.2)
        delay = max(0.0, p['speechOnset'] - (m['speechStart'] - cut_in))
        inputs += ['-i', str((base / line['file']).resolve())]
        filters.append(f'[{i}:a]aresample={RATE},aformat=channel_layouts=mono,atrim=start={cut_in:.3f}:end={cut_out:.3f},asetpts=PTS-STARTPTS,'
                       f'afade=t=in:d=0.02,afade=t=out:st={max(0.0, cut_out - cut_in - 0.08):.3f}:d=0.08,highpass=f=80,volume={gain_db:.2f}dB,'
                       f'adelay={round(delay * 1000)}:all=1[n{i}]')
        measured[line['id']]['gainDb'] = round(gain_db, 2)
    n = len(narration['lines'])
    # asetpts after amix: trimmed, re-stamped and delayed inputs make amix emit frames without timestamps, and atrim would then drop everything.
    chain = ''.join(f'[n{i}]' for i in range(n)) + f'amix=inputs={n}:normalize=0,asetpts=N/SR/TB,apad,atrim=duration={duration},'
    chain += 'acompressor=threshold=-18dB:ratio=2.5:attack=8:release=140:makeup=1,alimiter=limit=0.89:attack=3:release=60:level=false,pan=stereo|c0=c0|c1=c0[voice]'
    filters.append(chain)
    ffmpeg(*inputs, '-filter_complex', ';'.join(filters), '-map', '[voice]', '-t', f'{duration:.3f}', '-ar', str(RATE), '-c:a', 'pcm_f32le', str(out))


def narrate(plan_path, fit=False, dry=False, engine_override=None, from_voice=False):
    plan_path = Path(plan_path).resolve(); base = plan_path.parent
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    narration = plan.get('narration')
    if not isinstance(narration, dict) or narration.get('enabled') is False: raise ValueError('plan.narration is missing or disabled')
    lines = narration.get('lines')
    if not isinstance(lines, list) or not lines: raise ValueError('narration.lines must list at least one line')
    conf = settings(narration)
    language = narration.get('language') or (plan.get('typography') or {}).get('language') or 'en'
    voice = narration.get('voice') or {}
    if not isinstance(voice, dict): raise ValueError('narration.voice must be an object')
    if engine_override:
        voice['engine'] = engine_override; narration['voice'] = voice   # recorded, so the next run does not flip back
    engine = voice.get('engine', 'file')
    if engine not in ENGINES: raise ValueError(f'unknown engine {engine}; one of {", ".join(ENGINES)}')
    validate_lines(lines, {s['id'] for s in plan['shots']})
    voice_dir = base / 'assets' / 'narration'; synthesized = []; warnings = []
    for line in lines:
        signature = hashlib.sha256(json.dumps([line['text'], language, engine, voice, line.get('pace', 1.0), line.get('intensity', 'normal')],
                                              ensure_ascii=False, sort_keys=True, default=str).encode('utf-8')).hexdigest()
        file = (base / line['file']).resolve() if isinstance(line.get('file'), str) and line['file'] else None
        exists = file is not None and file.is_file()
        if dry:
            if not exists: raise ValueError(f'line {line["id"]} has no audio file; run without --dry-run to synthesize')
            if engine != 'file' and line.get('textSha256') != signature: warnings.append(f'{line["id"]}: audio predates the current text/voice; a real run will re-synthesize it')
            continue
        if exists and (engine == 'file' or line.get('textSha256') == signature): continue
        if engine == 'file': raise ValueError(f'line {line["id"]}: engine "file" needs an existing line.file')
        voice_dir.mkdir(parents=True, exist_ok=True)
        out = voice_dir / f'{line["id"]}.wav'
        line_voice = dict(voice); line_voice['speed'] = float(voice.get('speed', 1.0)) * float(line.get('pace', 1.0))
        info = ENGINES[engine][0](line['text'], out, line_voice, language, line.get('intensity', 'normal'))
        line['file'] = posix(out, base); line['textSha256'] = signature; line['engine'] = {'name': engine, **info}
        synthesized.append(line['id'])
        write_json(plan_path, plan)   # persist each synthesized line at once: a later failure must not re-bill it
    measured = {line['id']: measure((base / line['file']).resolve()) for line in lines}
    for line in lines:
        m = measured[line['id']]; spoken = m['speechEnd'] - m['speechStart']
        m['words'] = round(spoken_words(line['text']), 1); m['wordsPerSecond'] = round(m['words'] / spoken, 2) if spoken > 0 else None
    placements, shifts, problems = place(plan, narration, measured, conf, fit, from_voice)
    for line in lines:
        wps = measured[line['id']]['wordsPerSecond']
        if wps and wps > 3.3: warnings.append(f'{line["id"]}: {wps} words/s is rushed for narration; shorten the text or lower pace')
        if wps and wps < 1.4: warnings.append(f'{line["id"]}: {wps} words/s drags; check the engine output for long pauses')
    spoken_total = sum(measured[l['id']]['speechEnd'] - measured[l['id']]['speechStart'] for l in lines)
    coverage = spoken_total / plan['duration'] if plan['duration'] else 0
    if coverage > 0.85: warnings.append(f'voice covers {coverage:.0%} of the film: no air between lines; cut words or let shots breathe')
    report = {'engine': engine, 'language': language, 'voice': {k: v for k, v in voice.items() if k != 'settings' or isinstance(v, dict)},
              'settings': conf, 'synthesized': synthesized, 'fitShots': fit, 'timeFromVoice': from_voice, 'shotShifts': {k: v for k, v in shifts.items() if v},
              'marks': {s['id']: s['marks'] for s in plan['shots'] if s.get('marks')},
              'lines': [{'id': l['id'], 'shotId': l['shotId'], 'text': l['text'], 'file': l['file'], 'engine': l.get('engine'), 'intensity': l.get('intensity', 'normal'),
                         **measured[l['id']], **placements[l['id']]} for l in lines],
              'coverage': round(coverage, 3), 'problems': problems, 'warnings': warnings,
              'listeningStatus': 'Not auditioned by script; listen to assets/narration.wav for pronunciation, emphasis and pace.'}
    if dry:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if problems: raise ValueError('narration does not fit its shots (see problems)')
        return report
    if problems:
        print('\n'.join(problems), file=sys.stderr)
        raise ValueError('narration does not fit its shots (see above)')
    for line in lines:
        line.update({k: measured[line['id']][k] for k in ['duration', 'speechStart', 'speechEnd']})
        line['start'] = placements[line['id']]['start']; line['end'] = placements[line['id']]['end']; line['at'] = placements[line['id']]['at']
    beats = sound_beats(plan, narration, placements, base)
    report['soundBeats'] = beats
    out = base / 'assets' / 'narration.wav'; out.parent.mkdir(exist_ok=True)
    assemble(base, narration, measured, placements, conf, plan['duration'], out)
    narration['file'] = 'assets/narration.wav'; narration.setdefault('gain', 1.0); narration.setdefault('captions', True)
    write_json(plan_path, plan)
    report['planSha256'] = sha(plan_path); report['stem'] = {'file': 'assets/narration.wav', 'sha256': sha(out)}
    report['lines'] = [{**row, 'gainDb': measured[row['id']].get('gainDb')} for row in report['lines']]
    evidence = base / 'evidence'; evidence.mkdir(exist_ok=True)
    write_json(evidence / 'narration.json', report)
    moved = {s['id']: s for s in plan['shots']}
    print(f'Narration: {len(lines)} lines ({len(synthesized)} synthesized with {engine}), voice covers {coverage:.0%} of {plan["duration"]}s. '
          f'Stem assets/narration.wav; report evidence/narration.json. Rebuild the film (npm run build) before rendering.'
          + (' Shot timeline now follows the voice: ' + ', '.join(f'{s["id"]} {s["start"]}–{s["end"]}s' for s in plan['shots']) if from_voice else
             (' Shots were lengthened: ' + ', '.join(f'{k} +{v}s' for k, v in shifts.items() if v) if fit and any(shifts.values()) else ''))
          + (f' Marks: ' + ', '.join(f'{sid}.{m}={t}s' for sid, s in moved.items() for m, t in (s.get('marks') or {}).items()) if report['marks'] else '')
          + (f' Sound beats: {", ".join(beats)}.' if beats else ''))
    for w in warnings: print('Warning: ' + w, file=sys.stderr)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('plan', nargs='?', type=Path)
    p.add_argument('--fit-shots', action='store_true', help='lengthen shots that cannot hold their line; later shots, cues and duration shift')
    p.add_argument('--time-from-voice', action='store_true', help='narrated shots take exactly lead + speech + tail (grow or shrink, never below narration.minShot)')
    p.add_argument('--dry-run', action='store_true', help='measure and report only; exit 1 when lines do not fit')
    p.add_argument('--engine', choices=list(ENGINES), help='set narration.voice.engine for this and later runs')
    p.add_argument('--engines', action='store_true', help='list engines')
    a = p.parse_args()
    if a.engines:
        for name, (_, doc) in ENGINES.items(): print(f'{name:11s} {doc}')
        return
    if not a.plan: p.error('plan.json is required')
    try: narrate(a.plan, fit=a.fit_shots, dry=a.dry_run, engine_override=a.engine, from_voice=a.time_from_voice)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as e:
        if isinstance(e, subprocess.CalledProcessError): message = (e.stderr or '').strip() or f'{e.cmd[0]} exited {e.returncode}'
        elif isinstance(e, KeyError): message = f'plan is missing {e}'
        else: message = str(e)
        p.exit(1, message + '\n')


if __name__ == '__main__':
    main()
