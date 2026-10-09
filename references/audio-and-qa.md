# Audio and delivery checks

## Score and SFX

First complete the selection according to [score creation and SFX sourcing](audio-sourcing.md): music is code-original by default; for SFX, first look for recorded samples that match the product/action, and use built-in SFX only to fill whichever item is missing. Settle the music's character, beat and resolve position first, then place the actions. The original case used 120 BPM; other products choose tempo, melody and instrumentation from their actual storyboard. The same piece is not required.

Build `audio.cues` consistent with `plan.json`: `at / actionId / file / gain / role`. `at` is absolute seconds in the film; an action's `at` is seconds relative to the shot start, so the cue corresponds to `shot.start + action.at`. SFX land where the action happens, not mechanically at the start of every shot. Use a light click/pop for selection, a whoosh only for structural changes, a recognizable alert tone for notifications, and one resolve at the end.

Licensing distinguishes "usable in the final film" from "redistributable as original audio with the template". This skill does not bundle the original case's Pixabay recordings and carries no commercial fonts. When downloading audio into the current video project, record its source and license; do not treat the project license as a redistribution license for the skill.

## From "SFX written" to "actually audible"

For each core feature group, pick the state change with the strongest sense of feedback (select, open, complete, notify) and mark the corresponding action `soundRequired: true`. Not every text entrance gets a sound, but do not put one sound at the very end and skip every key action in between. Use a recognizable two-tone ding-dong or confirmation tone for completion/notification; do not use only whooshes.

The audio check has three steps: first listen to `sfx-stem.wav` alone to confirm key events have SFX; then listen to the master to confirm they are not drowned by the score; finally listen to the encoded MP4 to confirm the edit/export dropped nothing. Checking only that files exist or counting tracks is not enough. When you can audition, check action by action; when you cannot, state so precisely and do not pretend the listening check passed.

If no suitable SFX can be found, copy the missing click/click-alt, pop, toggle, typing, ding-dong, success, error, resolve, whoosh or sweep directly from the [built-in SFX directory](../assets/audio/sfx/). These are ready-made original WAVs; no generator needs to run first. Modify `make_sfx.py` only when the timbre needs adjusting, and output to a new directory.

**Set gain from measured levels.** Built-in SFX peak around −20 dBFS, recorded samples near 0 dBFS; at the same gain the former is covered by the score. Use `scripts/sfx_landmarks.py` to check each file's peak level and landmark. After mixing, compare, cue by cue, the SFX track's peak against the ducked music's peak at the moment the SFX appears: the SFX should not be noticeably below the music.

```sh
# Output the code-original score to assets/music.wav.
# Source SFX per audio-sourcing.md, copy built-in WAVs for gaps; then edit the plan's actions and cues.
python3 <skill-dir>/scripts/mix_audio.py plan.json
```

`mix_audio.py` outputs `assets/sfx-stem.wav`, `assets/music-ducked.wav`, `assets/master.wav` and `evidence/audio-mix.json`, and applies two-pass loudness processing to the mix. If the score is too loud, lower the music gain; if SFX are too quiet, adjust the corresponding cue. The existing HyperFrames/Remotion mixers can also be used, but keep equivalent assets, SFX events, mix provenance and final output evidence.

Config structure (illustrative; times should come from the actual shots):

```json
{
  "audioRequired": true,
  "sfxRequired": true,
  "audio": {
    "music": {"file": "assets/music.wav", "gain": 0.65},
    "cues": [{"at": 12.2, "actionId": "task-finished", "file": "assets/sfx/ding-dong.wav", "gain": 0.7, "role": "sfx"}]
  }
}
```

The corresponding action, for example: the shot starts at 12 seconds and `actions` contains `{"id":"task-finished","at":0.2,"action":"task-complete notification appears","soundRequired":true}`. The cue should align with that action; the audible landmark is normally kept within 1 frame of the action, with a check limit of 2 frames. If the user explicitly wants no SFX, record `sfxRequired:false` and `audioExceptionReason`; for full silence set `audioRequired:false`. These exceptions follow the user and are not decided by the model on its own.

## Make room when an SFX plays

`audio.ducking` is on by default. With only a fixed music gain, important alerts could still be covered; now the music is lowered ahead of each cue and smoothly restored after the SFX ends. The whole track is not uniformly quieter, and there is no sudden silence.

The table below is this skill's listening starting point, **not an official audio standard**; adjust for music density and SFX timbre:

| Sound role | Score reduction | Pre-onset attack / main hold / release |
| --- | --- | --- |
| Click, toggle, light pop | about 3–3.5 dB | 40ms / 100–120ms / 200–240ms |
| Typing detail | about 2.5 dB | 40ms / 350ms / 250ms |
| Transition | about 4 dB | 40ms / 160–200ms / 300–350ms |
| Completion, notification, important confirmation | about 5–6 dB | 40ms / 350–450ms / 350–400ms |
| Brand ending | about 5 dB | 40ms / 550ms / 450ms |

The mix script uses deterministic volume envelopes; when several SFX overlap it takes the deepest current reduction rather than multiplying attenuations layer on layer. Adjustable per item:

```json
{"audio":{"ducking":{"enabled":true}},"cueExample":{"kind":"ding-dong","duck":{"db":6,"attack":0.04,"hold":0.45,"release":0.4}}}
```

`cueExample` is a field illustration; in practice it lives in `audio.cues[]`. Global settings override the per-kind presets, and a cue's `duck` overrides the global; there is no reason to give every sound the same strength. If you hear the music pumping constantly, remove unnecessary cues, reduce the ducking or lengthen the release. If SFX are still masked, first check timbre conflicts and adjust the relative BGM-to-SFX level, then look at local ducking; do not just raise the final master level.

If switching to real-time sidechain, FFmpeg `sidechaincompress` uses a second signal to control compression of the first and needs threshold/ratio/attack/release tuning; this tool chooses volume automation from known cues, which is easier to duck ahead of time and verify repeatably. Filter syntax follows [FFmpeg volume](https://ffmpeg.org/ffmpeg-filters.html#volume) and [sidechaincompress](https://ffmpeg.org/ffmpeg-filters.html#sidechaincompress); delay follows [adelay](https://ffmpeg.org/ffmpeg-filters.html#adelay).

## Beat sync and sound variation

1. Listen to/analyze the actual music to determine the BPM and the time of the first beat; when the rhythm is not fixed, note the actual beats instead of inventing a 120 BPM. Main transitions may land on downbeats; light operations need not all land on downbeats.
2. Adjust picture and sound timing together. `cue.at` is the file start and `syncOffset` is the audible landmark inside the file, so `cue.at + syncOffset = shot.start + action.at`. Measure landmarks with `scripts/sfx_landmarks.py`: clicks use the onset, whooshes/impacts use the peak (they must start before the picture).
3. When using a beat grid, fill in `audio.beatGrid:{bpm,offset}`; mark cues that need beat alignment `onBeat:true`, and use `beatDivision:1|2|4` for quarter/eighth/sixteenth notes. The mix report states how many frames each cue is off from the action and from the nearest beat; it only reports, it never silently moves SFX and causes audio-picture misalignment.
4. A 30–60 second film usually uses 4–6 roles: select/confirm, pop/toggle, typing, spatial transition, completion/notification, ending. Categories serve the picture; do not invent errors or notifications to fill a quota. Shorter films can use fewer.
5. Consecutive clicks can alternate click/click-alt for slight timbre variation; typing sounds are rhythmic short bursts; transition sounds are reserved for structural changes in the picture; ding-dong is reserved for states worth attention. Do not "ding" every time text appears.
6. Finally listen separately to the music track, the SFX track, the full mix and the final MP4; check whether the first hit of an alert is covered, whether tails are cut off, and whether the rhythm is crowded.

## Mix

Music should be audible but not fatiguing; for a short film without voice-over, a final mix around -16 LUFS with true peak no higher than -1 to -1.5 dBTP is a starting point, adjusted to platform requirements and listening. Different platforms/genres do not share one mandatory value. With voice-over, leave room for the voice and duck by ear.

When normalization is needed, use FFmpeg loudnorm two-pass: measure first, read measured_I/TP/LRA/thresh/offset, then feed the measurements into the second pass; do not judge loudness by peak normalization alone. Re-measure true peak after the final AAC encode, since encoding can create new peaks. The report's `normalization.normalization_type` stores the linear/dynamic mode the second loudnorm pass actually used. If the music exceeds the film length by more than 1 second, the script prints a warning and writes it into the report; after automatic truncation and fade-out, confirm the ending and re-arrange if necessary.

Verify that music and picture have the same length, the opening does not blast, the ending finishes naturally, SFX do not clip and there is no sudden silence. Audition the final file in a player; if the environment can only measure, state clearly that auditioning was not done and do not claim it was "already heard".

## Automated checks

```sh
python3 <skill-dir>/scripts/check_delivery.py plan.json --video renders/final.mp4 --mix-report evidence/audio-mix.json > evidence/delivery-check.json
ffmpeg -i renders/final.mp4 -af loudnorm=I=-16:TP=-1.5:LRA=8:print_format=json -f null -
```

In production mode (`demo:false`), the script also rejects generic or missing headlines (`headlineEn` in bilingual mode), a `typography` block without language, mode and fonts, key actions without a cue, BGM only, a stale mix report or changed asset hashes. The script cannot automatically separate SFX from the MP4 and judge how they sound; the built-in exporter verifies the hash of the passed-in master against the mix report, while other exporters must verify their track wiring themselves.

The script fails on timing gaps/overlaps, wrong specs, missing audio tracks, or selling points without a source; it warns on reading time and on roles that are too uniform. It cannot be used to declare that selling points are true, that visuals are uncropped or that the music sounds good.

`--video` also outputs `pacing` (static frame ratio, longest static run, hard cut count), used only to locate segments worth re-watching. Large flat-color backgrounds and small-area motion are easily counted as static; do not add meaningless animation to improve the number. For the visual review method see [review](review.md).

## Final manual check

| What to check | What to look at |
| --- | --- |
| Narrative | On first viewing you can say what the updates are and what they do for you |
| Reading | Captions, read on their own in the film language, still tell you the object, action and result; no vague slogans; explanations appear early enough |
| Headlines | The headline (the English headline in bilingual mode) carries real meaning and sits at headline level; CJK text is uniformly sans-serif; the headline and caption fonts actually load |
| Picture | First/middle/last frame, before and after every transition; no accidental blank screens, cropping, jumps or broken images |
| Brand | Correct product name, official complete logo, visual identity consistent with the repository |
| Facts | Feature status has evidence; examples do not pose as customer results or benchmarks |
| Components | Original feature components and their styles actually appear on screen; build graph, state driving and source manifest match the stills; no basic controls or token replicas passed off as reuse of the whole feature |
| Audio | Both BGM and key-action SFX are audible; completion/notification feedback is clear; actions are aligned; no harshness, no clipping, complete ending |
| Links | URL/CTA hidden as the user requested; masking does not leak during zoom and movement |
| Consistency | Check both the preview and the MP4; the final changes actually made it into the exported file |

Extract key frames from the final MP4, not just reused pre-export screenshots. On delivery, attach the correct file paths and a clear status of the final film; do not mistake a technical sample, an unmixed version or an early version for the final.
