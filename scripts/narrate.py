#!/usr/bin/env python3
"""Narration for a film plan: synthesize each line, level-match the voice, time it to the shots, assemble one stem.

    python3 narrate.py plan.json                 # synthesize missing/changed lines, measure, place, write assets/narration.wav
    python3 narrate.py plan.json --fit-shots     # also lengthen shots that are too short for their line (shifts later shots, cues, duration)
    python3 narrate.py plan.json --dry-run       # measure and report only; no synthesis, no files written
    python3 narrate.py --engines                 # list engines and what they need

plan.narration:
  enabled       true
  language      BCP-47 tag; defaults to typography.language
  voice         {engine, id, speed, style}  engines: edge | openai | elevenlabs | piper | say | file
  lead          seconds between the shot start and the first word (default 0.35)
  tail          seconds of air between the last word and the cut (default 0.6)
  gap           minimum silence between two lines in one shot (default 0.3)
  targetRms     dBFS RMS of the spoken part of every line (default -20); intensity strong/soft moves it ±1.5 dB
  duck          {db, attack, release} music reduction under speech (default 9 dB, 0.15 s, 0.6 s)
  captions      true: the starter renders each line as a caption bar while it is spoken
  lines[]       {id, shotId, text, lead?, pace?, intensity?, pauseAfter?, file?}
                narrate.py writes back: file, duration, speechStart, speechEnd, start, end, textSha256

Timing rule (the same one broadcast editors use): the voice starts a beat after the picture changes, and the picture
stays a beat after the voice stops. Lines never run into the next shot; --fit-shots stretches the shot instead.
Only needs FFmpeg plus the chosen engine.
"""
import argparse
import hashlib
import json
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

RATE = 48000
WINDOW = 480                     # 10 ms analysis windows
DEFAULTS = {'lead': 0.35, 'tail': 0.6, 'gap': 0.3, 'targetRms': -20.0}
DUCK = {'db': 9.0, 'attack': 0.15, 'release': 0.6}
INTENSITY_DB = {'strong': 1.5, 'normal': 0.0, 'soft': -1.5}
EDGE_VOICES = {'en': 'en-US-AndrewMultilingualNeural', 'fr': 'fr-FR-DeniseNeural', 'de': 'de-DE-KatjaNeural', 'es': 'es-ES-ElviraNeural',
               'it': 'it-IT-ElsaNeural', 'pt': 'pt-BR-FranciscaNeural', 'ja': 'ja-JP-NanamiNeural', 'ko': 'ko-KR-SunHiNeural', 'zh': 'zh-CN-XiaoxiaoNeural', 'nl': 'nl-NL-ColetteNeural'}
STYLE_HINTS = {
    'strong': 'Confident, energetic, slightly faster, clear emphasis on the key word.',
    'normal': 'Warm, clear, conversational product narration; even pace; no sales voice.',
    'soft': 'Calm, quieter, unhurried; a reflective closing line.',
}


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def text_sha(text, voice): return hashlib.sha256(json.dumps([text, voice], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
def finite(x): return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
def run(args, **kw): return subprocess.run(args, check=True, capture_output=True, text=True, **kw)
def ffmpeg(*args): return run(['ffmpeg', '-v', 'error', '-y', *args])


# ---------------------------------------------------------------- engines
def engine_edge(text, out, voice, language):
    exe = shutil.which('edge-tts') or shutil.which('edge-tts.exe')
    if not exe: raise ValueError('edge engine: install with `pip install edge-tts` (free Microsoft neural voices, needs network)')
    voice_id = voice.get('id') or EDGE_VOICES.get(language.split('-')[0].lower())
    if not voice_id: raise ValueError(f'edge engine: no default voice for language {language}; set narration.voice.id (see `edge-tts --list-voices`)')
    rate = round((float(voice.get('speed', 1.0)) - 1) * 100)
    tmp = out.with_suffix('.mp3')
    run([exe, '--voice', voice_id, '--rate', f'{rate:+d}%', '--text', text, '--write-media', str(tmp)])
    ffmpeg('-i', str(tmp), '-ac', '1', '-ar', str(RATE), '-c:a', 'pcm_s16le', str(out)); tmp.unlink()
    return {'voice': voice_id, 'rate': f'{rate:+d}%'}


def engine_openai(text, out, voice, language, intensity='normal'):
    key = os.environ.get('OPENAI_API_KEY')
    if not key: raise ValueError('openai engine: set OPENAI_API_KEY')
    body = {'model': voice.get('model', 'gpt-4o-mini-tts'), 'voice': voice.get('id') or 'alloy', 'input': text,
            'response_format': 'wav', 'speed': float(voice.get('speed', 1.0))}
    hint = voice.get('style') or STYLE_HINTS.get(intensity)
    if hint: body['instructions'] = f'Narration for a software product video in {language}. {hint}'
    req = urllib.request.Request('https://api.openai.com/v1/audio/speech', data=json.dumps(body).encode(),
                                 headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r: data = r.read()
    tmp = out.with_suffix('.raw.wav'); tmp.write_bytes(data)
    ffmpeg('-i', str(tmp), '-ac', '1', '-ar', str(RATE), '-c:a', 'pcm_s16le', str(out)); tmp.unlink()
    return {'voice': body['voice'], 'model': body['model'], 'instructions': body.get('instructions')}


def engine_elevenlabs(text, out, voice, language, intensity='normal'):
    key = os.environ.get('ELEVENLABS_API_KEY')
    if not key: raise ValueError('elevenlabs engine: set ELEVENLABS_API_KEY')
    if not voice.get('id'): raise ValueError('elevenlabs engine: narration.voice.id must be a voice id from your ElevenLabs library')
    settings = {'stability': 0.55 if intensity == 'normal' else (0.4 if intensity == 'strong' else 0.7), 'similarity_boost': 0.8,
                'style': 0.35 if intensity == 'strong' else 0.15, 'speed': float(voice.get('speed', 1.0))}
    settings.update(voice.get('settings', {}))
    body = {'text': text, 'model_id': voice.get('model', 'eleven_multilingual_v2'), 'voice_settings': settings}
    req = urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{voice["id"]}?output_format=pcm_44100',
                                 data=json.dumps(body).encode(), headers={'xi-api-key': key, 'Content-Type': 'application/json', 'Accept': 'audio/pcm'})
    with urllib.request.urlopen(req, timeout=120) as r: data = r.read()
    tmp = out.with_suffix('.pcm'); tmp.write_bytes(data)
    ffmpeg('-f', 's16le', '-ar', '44100', '-ac', '1', '-i', str(tmp), '-ar', str(RATE), '-c:a', 'pcm_s16le', str(out)); tmp.unlink()
    return {'voice': voice['id'], 'model': body['model_id'], 'settings': settings}


def engine_piper(text, out, voice, language):
    exe = shutil.which('piper')
    if not exe: raise ValueError('piper engine: install the piper CLI and a voice model (https://github.com/rhasspy/piper)')
    if not voice.get('id'): raise ValueError('piper engine: narration.voice.id must be the path to a .onnx voice model')
    tmp = out.with_suffix('.piper.wav')
    run([exe, '--model', voice['id'], '--length_scale', str(round(1 / float(voice.get('speed', 1.0)), 3)), '--output_file', str(tmp)], input=text)
    ffmpeg('-i', str(tmp), '-ac', '1', '-ar', str(RATE), '-c:a', 'pcm_s16le', str(out)); tmp.unlink()
    return {'voice': voice['id']}


def engine_say(text, out, voice, language):
    exe = shutil.which('say')
    if not exe: raise ValueError('say engine: only available on macOS')
    tmp = out.with_suffix('.aiff')
    args = [exe, '-o', str(tmp), '-r', str(round(175 * float(voice.get('speed', 1.0))))]
    if voice.get('id'): args += ['-v', voice['id']]
    run([*args, text])
    ffmpeg('-i', str(tmp), '-ac', '1', '-ar', str(RATE), '-c:a', 'pcm_s16le', str(out)); tmp.unlink()
    return {'voice': voice.get('id') or 'system default'}


def engine_file(text, out, voice, language):
    raise ValueError('file engine: record or generate the audio yourself and set line.file; narrate.py only measures and places it')


ENGINES = {
    'edge': (engine_edge, 'free Microsoft neural voices through the edge-tts CLI (pip install edge-tts); needs network'),
    'openai': (engine_openai, 'OpenAI speech API (OPENAI_API_KEY); voice.style or line.intensity become the instructions prompt'),
    'elevenlabs': (engine_elevenlabs, 'ElevenLabs API (ELEVENLABS_API_KEY, voice.id required); intensity maps to stability/style'),
    'piper': (engine_piper, 'local Piper CLI with an .onnx voice model (voice.id = model path); offline'),
    'say': (engine_say, 'macOS built-in `say`; quick drafts, not release quality'),
    'file': (engine_file, 'you supply the audio per line (a recording or any other TTS); narrate.py measures, level-matches and places it'),
}


# ---------------------------------------------------------------- measurement
def samples(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '1', '-ar', str(RATE), '-f', 's16le', '-'], capture_output=True, check=True).stdout
    return struct.unpack('<%dh' % (len(raw) // 2), raw)


def measure(path):
    """Duration, where speech actually starts/ends, RMS level of the spoken part, peak."""
    x = samples(path)
    if len(x) < WINDOW: raise ValueError(f'{path}: too short or silent')
    rms = []
    for i in range(0, len(x) - WINDOW + 1, WINDOW):
        block = x[i:i + WINDOW]
        rms.append(math.sqrt(sum(v * v for v in block) / WINDOW) / 32768)
    peak = max(abs(v) for v in x) / 32768
    loudest = max(rms)
    if loudest <= 0: raise ValueError(f'{path}: silent file')
    gate = max(loudest * 0.08, 10 ** (-45 / 20))            # 22 dB under the loudest window, never below -45 dBFS
    voiced = [i for i, v in enumerate(rms) if v >= gate]
    first, last = voiced[0], voiced[-1]
    speech = rms[first:last + 1]
    level = math.sqrt(sum(v * v for v in speech) / len(speech))
    return {'duration': round(len(x) / RATE, 3), 'speechStart': round(first * WINDOW / RATE, 3), 'speechEnd': round((last + 1) * WINDOW / RATE, 3),
            'rmsDbfs': round(20 * math.log10(level), 1), 'peakDbfs': round(20 * math.log10(peak), 1) if peak > 0 else None}


def words(text):
    stripped = ''.join(text.split())
    cjk = sum(1 for ch in stripped if '぀' <= ch <= 'ヿ' or '㐀' <= ch <= '鿿' or '가' <= ch <= '힯')
    return cjk / 2.2 + len([w for w in text.split() if any(ch.isalnum() for ch in w) and not all('㐀' <= ch <= '鿿' for ch in w)])


# ---------------------------------------------------------------- planning
def settings(narration):
    s = dict(DEFAULTS)
    for k in s:
        if k in narration:
            if not finite(narration[k]): raise ValueError(f'narration.{k} must be a number')
            s[k] = narration[k]
    duck = dict(DUCK); duck.update(narration.get('duck', {}) or {})
    for k in duck:
        if not finite(duck[k]): raise ValueError(f'narration.duck.{k} must be a number')
    if not 0 <= duck['db'] <= 18 or not 0.02 <= duck['attack'] <= 1 or not 0.05 <= duck['release'] <= 3: raise ValueError('narration.duck outside useful bounds')
    s['duck'] = duck
    return s


def place(plan, narration, measured, conf, fit):
    """Place every line so speech begins lead seconds into its shot and ends tail seconds before the cut.
    With fit=True, shots that are too short grow (later shots, cues and the duration shift). Returns (placements, shifts, problems)."""
    shots = plan['shots']; by_id = {s['id']: s for s in shots}
    problems = []; placements = {}
    per_shot = {}
    for line in narration['lines']: per_shot.setdefault(line['shotId'], []).append(line)
    shift = 0.0; shifts = {}
    for shot in shots:
        original_start, original_end = shot['start'], shot['end']
        shot['start'] = round(original_start + shift, 3); shot['end'] = round(original_end + shift, 3)
        cursor = shot['start']
        for line in per_shot.get(shot['id'], []):
            m = measured[line['id']]
            lead = line.get('lead', conf['lead'])
            onset = max(shot['start'] + lead, cursor)
            speech_len = m['speechEnd'] - m['speechStart']
            end_of_speech = onset + speech_len
            needed_end = end_of_speech + conf['tail']
            if needed_end > shot['end'] + 1e-6:
                if fit:
                    grow = round(needed_end - shot['end'], 3)
                    shot['end'] = round(shot['end'] + grow, 3); shift += grow
                else:
                    problems.append(f"{line['id']}: speech ends {end_of_speech - shot['end'] + conf['tail']:.2f}s too late for shot {shot['id']} "
                                    f"(needs end >= {needed_end:.2f}s, has {shot['end']:.2f}s); shorten the line or run --fit-shots")
            file_start = round(onset - m['speechStart'], 3)
            placements[line['id']] = {'start': file_start, 'end': round(file_start + m['duration'], 3), 'speechOnset': round(onset, 3), 'speechEnd': round(end_of_speech, 3)}
            cursor = end_of_speech + line.get('pauseAfter', conf['gap'])
        shifts[shot['id']] = round(shot['start'] - original_start, 3)
    if fit and shift:
        plan['duration'] = round(plan['duration'] + shift, 3)
        audio = plan.get('audio', {}); actions = {}
        for s in shots:
            for a in s.get('actions', []): actions[a.get('id')] = s['id']
        for cue in audio.get('cues', []) if isinstance(audio, dict) else []:
            sid = actions.get(cue.get('actionId'))
            if sid in shifts and finite(cue.get('at')): cue['at'] = round(cue['at'] + shifts[sid], 3)
    return placements, shifts, problems


def assemble(base, narration, measured, placements, conf, duration, out):
    """One stereo float stem: each line gained to the target RMS, placed at its start, lightly compressed and limited."""
    inputs = []; filters = []
    for i, line in enumerate(narration['lines']):
        m = measured[line['id']]; p = placements[line['id']]
        target = conf['targetRms'] + INTENSITY_DB.get(line.get('intensity', 'normal'), 0)
        gain_db = max(-24, min(24, target - m['rmsDbfs']))
        inputs += ['-i', str((base / line['file']).resolve())]
        filters.append(f'[{i}:a]aresample={RATE},aformat=channel_layouts=mono,highpass=f=80,volume={gain_db:.2f}dB,adelay={max(0, round(p["start"] * 1000))}:all=1[n{i}]')
        measured[line['id']]['gainDb'] = round(gain_db, 2)
    n = len(narration['lines'])
    chain = ''.join(f'[n{i}]' for i in range(n)) + f'amix=inputs={n}:normalize=0,apad,atrim=duration={duration},'
    chain += 'acompressor=threshold=-18dB:ratio=2.5:attack=8:release=140:makeup=1,alimiter=limit=0.89:attack=3:release=60:level=false,aformat=channel_layouts=stereo[voice]'
    filters.append(chain)
    ffmpeg(*inputs, '-filter_complex', ';'.join(filters), '-map', '[voice]', '-t', f'{duration:.3f}', '-ar', str(RATE), '-c:a', 'pcm_f32le', str(out))


def narrate(plan_path, fit=False, dry=False, engine_override=None):
    plan_path = Path(plan_path).resolve(); base = plan_path.parent
    plan = json.loads(plan_path.read_text())
    narration = plan.get('narration')
    if not isinstance(narration, dict) or narration.get('enabled') is False: raise ValueError('plan.narration is missing or disabled')
    lines = narration.get('lines')
    if not isinstance(lines, list) or not lines: raise ValueError('narration.lines must list at least one line')
    conf = settings(narration)
    language = narration.get('language') or (plan.get('typography') or {}).get('language') or 'en'
    voice = dict(narration.get('voice') or {})
    if engine_override: voice['engine'] = engine_override
    engine = voice.get('engine', 'file')
    if engine not in ENGINES: raise ValueError(f'unknown engine {engine}; one of {", ".join(ENGINES)}')
    shot_ids = {s['id'] for s in plan['shots']}
    seen = set()
    for line in lines:
        for key in ['id', 'shotId', 'text']:
            if not isinstance(line.get(key), str) or not line[key].strip(): raise ValueError(f'every narration line needs a non-empty {key}')
        if line['id'] in seen: raise ValueError(f'duplicate narration line id {line["id"]}')
        seen.add(line['id'])
        if line['shotId'] not in shot_ids: raise ValueError(f'line {line["id"]} refers to unknown shot {line["shotId"]}')
        if line.get('intensity', 'normal') not in INTENSITY_DB: raise ValueError(f'line {line["id"]}: intensity must be strong, normal or soft')
    voice_dir = base / 'assets' / 'narration'; synthesized = []
    for line in lines:
        signature = text_sha(line['text'], {**voice, 'pace': line.get('pace', 1.0), 'intensity': line.get('intensity', 'normal')})
        file = (base / line['file']).resolve() if isinstance(line.get('file'), str) and line['file'] else None
        fresh = file is not None and file.is_file() and (line.get('textSha256') == signature or engine == 'file')
        if not fresh:
            if dry: raise ValueError(f'line {line["id"]} has no up-to-date audio; run without --dry-run to synthesize')
            if engine == 'file': raise ValueError(f'line {line["id"]}: engine "file" needs an existing line.file')
            voice_dir.mkdir(parents=True, exist_ok=True)
            out = voice_dir / f'{line["id"]}.wav'
            line_voice = dict(voice); line_voice['speed'] = float(voice.get('speed', 1.0)) * float(line.get('pace', 1.0))
            fn = ENGINES[engine][0]
            info = fn(line['text'], out, line_voice, language, line.get('intensity', 'normal')) if engine in ('openai', 'elevenlabs') else fn(line['text'], out, line_voice, language)
            line['file'] = os.path.relpath(out, base); line['textSha256'] = signature; line['engine'] = {'name': engine, **info}
            synthesized.append(line['id'])
    measured = {line['id']: measure((base / line['file']).resolve()) for line in lines}
    for line in lines:
        m = measured[line['id']]; spoken = m['speechEnd'] - m['speechStart']
        m['words'] = round(words(line['text']), 1); m['wordsPerSecond'] = round(m['words'] / spoken, 2) if spoken > 0 else None
    placements, shifts, problems = place(plan, narration, measured, conf, fit)
    warnings = []
    for line in lines:
        wps = measured[line['id']]['wordsPerSecond']
        if wps and wps > 3.3: warnings.append(f'{line["id"]}: {wps} words/s is rushed for narration; shorten the text or lower pace')
        if wps and wps < 1.4: warnings.append(f'{line["id"]}: {wps} words/s drags; check the engine output for long pauses')
    spoken_total = sum(measured[l['id']]['speechEnd'] - measured[l['id']]['speechStart'] for l in lines)
    coverage = spoken_total / plan['duration'] if plan['duration'] else 0
    if coverage > 0.85: warnings.append(f'voice covers {coverage:.0%} of the film: no air between lines; cut words or let shots breathe')
    for line in lines:
        line.update({k: measured[line['id']][k] for k in ['duration', 'speechStart', 'speechEnd']})
        line['start'] = placements[line['id']]['start']; line['end'] = placements[line['id']]['end']
    report = {'engine': engine, 'language': language, 'settings': conf, 'synthesized': synthesized, 'fitShots': fit, 'shotShifts': {k: v for k, v in shifts.items() if v},
              'lines': [{'id': l['id'], 'shotId': l['shotId'], 'text': l['text'], 'file': l['file'], **measured[l['id']], **placements[l['id']]} for l in lines],
              'coverage': round(coverage, 3), 'problems': problems, 'warnings': warnings,
              'listeningStatus': 'Not auditioned by script; listen to assets/narration.wav for pronunciation, emphasis and pace.'}
    if problems and not dry:
        print('\n'.join(problems), file=sys.stderr)
        raise ValueError('narration does not fit its shots (see above)')
    if dry:
        print(json.dumps(report, ensure_ascii=False, indent=2)); return report
    out = base / 'assets' / 'narration.wav'
    assemble(base, narration, measured, placements, conf, plan['duration'], out)
    narration['file'] = 'assets/narration.wav'; narration.setdefault('gain', 1.0); narration.setdefault('captions', True)
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
    report['planSha256'] = sha(plan_path); report['stem'] = {'file': 'assets/narration.wav', 'sha256': sha(out)}
    report['lines'] = [{**row, 'gainDb': measured[row['id']].get('gainDb')} for row in report['lines']]
    evidence = base / 'evidence'; evidence.mkdir(exist_ok=True)
    (evidence / 'narration.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f'Narration: {len(lines)} lines ({len(synthesized)} synthesized with {engine}), voice covers {coverage:.0%} of {plan["duration"]}s. '
          f'Stem assets/narration.wav; report evidence/narration.json.' + (' Shots were lengthened: ' + ', '.join(f'{k} +{v}s' for k, v in shifts.items() if v) if fit and any(shifts.values()) else ''))
    for w in warnings: print('Warning: ' + w, file=sys.stderr)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('plan', nargs='?', type=Path)
    p.add_argument('--fit-shots', action='store_true', help='lengthen shots that cannot hold their line; later shots, cues and duration shift')
    p.add_argument('--dry-run', action='store_true', help='measure and report only')
    p.add_argument('--engine', choices=list(ENGINES), help='override narration.voice.engine for this run')
    p.add_argument('--engines', action='store_true', help='list engines')
    a = p.parse_args()
    if a.engines:
        for name, (_, doc) in ENGINES.items(): print(f'{name:11s} {doc}')
        return
    if not a.plan: p.error('plan.json is required')
    try: narrate(a.plan, fit=a.fit_shots, dry=a.dry_run, engine_override=a.engine)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as e:
        p.exit(1, (e.stderr if isinstance(e, subprocess.CalledProcessError) and e.stderr else str(e)) + '\n')


if __name__ == '__main__':
    main()
