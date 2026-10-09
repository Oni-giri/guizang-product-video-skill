# Narration: a voice-over that leads the cut

Narration is optional. Many product films work with music, SFX and captions alone. When the user wants a voice (a changelog read-out, a walkthrough, a launch film with a presenter), the voice becomes the spine of the edit: shots are timed to the lines, music sits under the words, and the caption bar shows what is being said. This page covers writing the script, generating the audio, placing it, mixing it and checking it. The tool is `scripts/narrate.py`; the plan block is `plan.narration`.

## When to narrate, when not to

- Narrate when the film explains a sequence of things that benefits from being told (a release with several changes, a workflow walkthrough), when the audience watches with sound on (YouTube, a launch page, a conference screen), or when the user asks for it.
- Do not narrate a 15–30 s social teaser that will autoplay muted, a film whose captions already carry the explanation at reading pace, or when no acceptable voice is available in the film language. A film with a weak synthetic voice is worse than the same film with captions.
- Narrated films still have captions by default (`narration.captions: true`): muted autoplay and accessibility both need them. The caption shows the line being spoken, one line at a time.

## Writing the script

Write it in `plan.narration.lines`, one entry per shot (occasionally two for a long workspace shot). Rules that make synthetic or recorded narration sound professional:

- **One idea per line, 8–20 words.** A line is what the viewer should take from that shot, in the plain-language form the copy rules already require (object, action, observable result). It is not the headline read aloud, and not the caption duplicated: the headline names it, the voice explains it.
- **Pace: 2.2–2.8 words per second** (CJK: about 5–6 characters per second). `narrate.py` reports words per second per line and warns above 3.3. If a line runs long, cut words before raising the speed.
- **Air.** The voice starts about 0.35 s after the shot changes (`lead`) and stops at least 0.6 s before the cut (`tail`). Voice should cover roughly 55–75 % of the film; above 85 % nothing can breathe. Opening and closing lines get more air than feature lines.
- **Intensity curve.** Mark the opening line `strong`, feature lines `normal`, the closing line `soft`. This nudges the level (±1.5 dB) and, for engines that take direction (OpenAI instructions, ElevenLabs stability/style), the delivery. Do not mark everything strong.
- **Write for the ear.** Contractions, short clauses, numbers spoken as words where natural, product names spelled the way they are pronounced (add a pronunciation hint in `text` if the engine mangles a name, and keep the caption text correct in `captionText`).
- **Match the language.** The script is in `typography.language` unless the user asks otherwise. Headline, caption and voice should agree; a French voice over an English caption is a user decision, not a default.
- **Do not narrate what the viewer can see.** "Here you can see the button" is filler. Say what it does and what happens.

## Generating the audio

`narration.voice.engine` selects how lines become audio. Run `python3 scripts/narrate.py --engines` for the list. None of them is bundled; the user picks one, and the choice is recorded in the plan and the evidence.

| Engine | What it is | Needs | Quality |
|---|---|---|---|
| `openai` | OpenAI speech API, `gpt-4o-mini-tts` by default; `line.intensity` / `voice.style` become the instructions prompt | `OPENAI_API_KEY` | Good, directable |
| `elevenlabs` | ElevenLabs API, `eleven_multilingual_v2`; intensity maps to stability/style | `ELEVENLABS_API_KEY`, `voice.id` | High |
| `edge` | Microsoft neural voices through the free `edge-tts` CLI | `pip install edge-tts`, network | Good for drafts and many languages |
| `piper` | Local Piper models, offline | `piper` CLI, a `.onnx` model as `voice.id` | Fair |
| `say` | macOS built-in | macOS | Draft only |
| `file` | Audio you supply per line: a recording, or any other TTS you ran yourself | `line.file` set | Whatever you bring |

Pick one voice per film and keep it. For a release film, a calm, clear, mid-register voice in the viewer's own language beats a dramatic one. Listen to one line before synthesizing the rest; change `voice.id` or `voice.speed` (0.9–1.1; ElevenLabs accepts 0.7–1.2 and the script clamps to that) if it sounds wrong. A line is re-synthesized only when its text, language, engine, voice, pace or intensity changes (`textSha256`); each synthesized line is saved to the plan immediately, so a run that then fails to fit does not re-bill the lines already made. `--engine X` on the command line is written back to `voice.engine`.

Engine specifics: OpenAI takes `voice.style` and the line's intensity as an instructions prompt (gpt-4o models only; `tts-1` ignores it) and the synthesized voice must be disclosed as AI-generated where OpenAI's usage policy requires it. ElevenLabs returns MP3 by default (`voice.outputFormat`, PCM formats need a paid tier); `voice.settings` overrides stability/style. edge-tts needs network access and no account.

`evidence/narration.json` records the engine, the voice block, and per line the engine details, measurements, placement and gain. Third-party voices come with their own terms; a cloned or licensed voice stays within its licence, and a real person's voice is never cloned without their consent.

## Placing the voice: the picture follows the words

```sh
python3 <skill-dir>/scripts/narrate.py plan.json --dry-run      # measure existing files, report fit, change nothing
python3 <skill-dir>/scripts/narrate.py plan.json                # synthesize missing lines, measure, place, write the stem
python3 <skill-dir>/scripts/narrate.py plan.json --fit-shots    # also lengthen shots that cannot hold their line
```

What the script does to each line:

1. Measures the file: where speech actually starts and ends (silence trimmed), spoken RMS level, peak, words per second.
2. Places it so the first word lands `lead` seconds after the shot starts (per-line `lead` overrides), and checks that the last word ends `tail` seconds before the cut. A second line in the same shot starts after the first plus `gap` (or the first line's `pauseAfter`).
3. If a shot is too short: without `--fit-shots` the run fails and prints the needed length; with `--fit-shots` the shot grows, every later shot moves, SFX cues move with their actions, and `plan.duration` grows. Shots never shrink automatically: cutting is a creative decision, so shorten lines or shots by hand.
4. Writes back `file, duration, speechStart, speechEnd, start, end` per line, assembles `assets/narration.wav` from the spoken part of each file only (pre-roll and tail room tone never play; `start` can be negative when a file has more pre-roll than `lead`) and writes `evidence/narration.json`.

After `--fit-shots`, the shot list in `DIRECTION.md` and any music arranged on shot boundaries are out of date: update them, re-arrange or re-render the score for the new length, then mix. **Rebuild the film (`npm run build`) after every `narrate.py` run**: `plan.json` is baked into the bundle, and `stills.mjs` / `render.mjs` refuse to run against a plan that changed since the last build. Run `narrate.py` again whenever shots move, the script changes, or the voice changes; `check_delivery.py` warns when the narration report is older than the plan.

## Level and dynamics

Professional narration is consistent: the listener never reaches for the volume. The stem is built so that:

- every line is gained to the same spoken RMS (`targetRms`, default −20 dBFS measured on the voiced part before compression; `intensity` moves it ±1.5 dB), so a quiet line and a loud line from the engine come out even; the finished stem measures a little lower because of the compressor;
- an 80 Hz high-pass removes rumble and plosive thumps;
- a gentle compressor (2.5:1 above −18 dB) evens out syllables, and a limiter keeps peaks under −1 dBFS;
- in the mix, music ducks under speech by `narration.duck.db` (default 9 dB) with a 150 ms attack before the first word and a 600 ms release after the last; SFX keep their level, so clicks stay audible under the voice.

If the voice still fights the music, lower `audio.music.gain` rather than pushing the voice gain up; if the voice sounds thin, the engine or voice is the problem, not the mix. The final master is still loudness-normalized (−16 LUFS, −1.5 dBTP); speech-led mixes often measure a lower LRA, which is expected.

## Sound effects with a voice

- Keep the action SFX: they are what makes the UI feel real. The mix does not duck them.
- Notification chimes (`ding-dong`, `success`, `error`, `resolve`) should land in a gap between lines, not on a word. `check_delivery.py` warns when one does; move the action or shorten the line.
- Whooshes on cuts are fine under the voice's tail, since the voice has stopped `tail` seconds before the cut.
- No music stings on top of speech; put impacts at line boundaries.

## Captions for narrated films

`src/kit/captions.jsx` renders the line being spoken from just before the first word to shortly after the last. It reads timings from the plan, so it is a pure function of film time and stays seek-safe. Restyle `.caption-bar` in `film.css` for the film: position inside the bottom safe area, the caption font from `typography.captionFont`, no backing on light films, at least 36 px, readable at phone width. When the engine needs a pronunciation hint in `text`, put the correctly spelled sentence in `captionText` and the caption uses that.

The caption bar sits at `z-index: 900`. The poster frame overlay (see [starter project](starter.md)) must sit above it (`z-index: 1000`), and its still is captured with `node stills.mjs public/poster <t> --hide-captions` so no caption is baked into the thumbnail.

Shot `description` fields still exist and the caption bar does not replace a headline. In a narrated film the per-shot description can be shorter, since the voice carries the explanation, but claim shots still need one (the delivery check requires it) and `plainExplanation` still records the fact in writing.

## Checks and listening

`check_delivery.py` with narration present verifies: every line is timed inside its shot with a beat of lead-in and air before the cut, lines do not overlap, pace is not rushed, chimes avoid speech, the narration report matches the plan, and the mix report carries the voice stem with a matching hash. These are structural.

Listen, in this order: `assets/narration.wav` alone (pronunciation, emphasis, pace, no clipped words at line starts), then `assets/master.wav` (voice above the music, SFX still audible, no pumping), then the encoded MP4. A mispronounced product name or a wrong stress is a content error; fix the text (or the pronunciation hint) and re-run, do not ship it. If you cannot listen, say so in the delivery notes; the scripts do not judge how a voice sounds.
