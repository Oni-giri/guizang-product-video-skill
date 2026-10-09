# Score and SFX: sources, arrangement and sync

## Where the music comes from (pick in this order)

1. **A track the user supplies**, or a library the user is licensed for: use it directly. Re-align the picture cuts to its actual beats and record the beats in `audio.beatGrid`.
2. **A music generation model that actually runs on this machine**: confirm the model weights are really local and the runtime (for example torch) is installed before using it. A cache that holds only config files does not count as "available". After generating, still check the sections against the storyboard; edit or layer impacts and risers where needed.
3. **Code-original synthesis** (the default fallback): write a synthesis script for this film, keep the source and a fixed random seed, so re-running yields the same piece.

Do not download a BGM of unknown origin, do not rip the music from a reference video, and do not rename an example track and call it a new score. If the user asks for silence, comply and record `audioExceptionReason`.

## Code-original: arrange first, then synthesize

**The arrangement comes from the storyboard**: open the shot list in `DIRECTION.md` and write down, section by section, what the music should do. Take the times directly from the shot boundaries in `plan.json`:

- Does the opening build up, hold suspense, or drop straight into the groove?
- Do the brand reveal, chapter changes and end card need impacts? Is there a beat of silence before the impact?
- Sections where the viewer reads text or watches UI operations need space: fewer instruments, melody steps back.
- Fast-cut sections get denser rhythm or a riser; the ending has a full harmonic resolve, with the tail left room according to the film length.

**The timbre comes from the product character**: the "sound" axis in the [film direction](direction.md) sets the genre first, then pick instrumentation. Do not default to electronic music every time:

| Character | Instrumentation and devices to consider |
|---|---|
| Calm, high-end, technical | Wide supersaw pad, pluck arpeggio, sidechain-compressed kick, sub impact |
| Light, friendly | Bright keyboard chords, short-note melody, light claps, marimba-like timbres |
| Warm, human | Piano or plucked strings leading, slow tempo, long reverb, little percussion |
| Powerful, tight | Percussion-led, bass pulses, dense risers, syncopated rhythm |
| Quiet, focused | Ambient pad, sparse bell tones, almost no drums |

**Two examples**, for the synthesis techniques; do not copy the pieces:

- `assets/audio/score-example-keys.py`: D major, keyboard chords, short-note melody, light drums; needs only the standard library + FFmpeg.
- `assets/audio/score-example-cinematic.py`: F minor, supersaw pad (with filter sweep), pluck made from decaying harmonics, pitch-sliding kick, noise-based claps and hi-hats, sidechain compression, dotted-eighth delay, noise-sweep riser, sub impact, convolution reverb. Needs numpy/scipy/soundfile; put them in the project's own venv.

**Synthesis essentials**:

- Synthesize per bus (drums, bass, pad, arpeggio, FX) and mix at the end. Each bus's envelope, panning and level must be adjustable on its own.
- Express all times in beats and bars. When the film length or tempo changes, all section times change together; check that the tail does not run past the end.
- Do not write the clicks and alert tones of on-screen actions into the score. Those are separate SFX, synced and ducked individually later.
- After export, look at the spectrogram and per-second loudness (see [review](review.md)) to confirm the section structure and the amount of low end. Too much low end is the most common problem with synthesized scores.

## SFX: find recorded samples first, fill gaps with built-ins

1. **A sample library the user already has, with a clear source.**
2. **A recorded sample library installed on this machine**: for example the Pixabay SFX bundled with the media-use skill (click, keypress, typing, pop, notification, ding, whoosh, glitch, sub impact, etc.). Read the license notes in its own `CREDITS.md` and record them in the project.
3. **Sample site search**: for example the [Pixabay sound effects library](https://pixabay.com/sound-effects/). Download links must come from a real download action; do not invent CDN addresses. If the sample site requires an interactive download and the current tools cannot get the file, record that honestly and move on to the next item.
4. **Built-in SFX of the skill** (`assets/audio/sfx/`, 11 original WAVs): fill only the missing category. Built-in SFX are fairly quiet (peak around −20 dBFS); set gain from the measured peak.

| On-screen action | Suitable sound | What to look for |
|---|---|---|
| Click, select | Short, clear UI click | Not harsh, clean onset |
| Pop, appear | pop, light toggle | Light, gives state feedback |
| Typing | Short keyboard bursts | Matches the on-screen typing rhythm |
| Notification, completion | Two-tone alert, confirmation chime | Recognizable, tail not too long |
| Structural change | whoosh, glitch | Only for real section changes, not for every element |
| Impact, end card | Sub impact | Layer with or choose between it and the score's impact; do not let them fight |

## Sync: land the sound on the action

Use `scripts/sfx_landmarks.py` to measure each file's onset, peak time and peak level:

```sh
python3 <skill-dir>/scripts/sfx_landmarks.py assets/sfx/*
```

- Click, keypress, pop: align the **onset** to the on-screen action.
- whoosh, impact, riser: align the **peak** to the cut or the hit frame; the sound must start before the picture.
- Write into the plan: `syncOffset` = the landmark used, `at` = action time − `syncOffset`.
- Gain: the SFX peak at the moment it appears must not be lower than the ducked score's peak. Recorded samples sit near 0 dBFS, built-in SFX around −20 dBFS; the same gain sounds very different.

## Keep the sources

Record in `evidence/audio-selection.json`:

- `music`: source (user-provided / generation model + model name / `code-original` + script path), duration, BPM, key, section times.
- `sfx[]`: each file's role, source (library name, detail page or author), license, local path. When falling back to built-in SFX, state the actual reason, for example "sample site requires interactive download; current tools cannot fetch the file". If unknown, write unknown; do not fabricate a search history.

Downloading samples for use in the final film is not the same as repackaging the original recordings as a redistributable sample library. This skill does not bundle third-party recordings; samples used in the project are used under their current license.

Finally, mix according to [audio and delivery checks](audio-and-qa.md).
