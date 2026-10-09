# Review: look as you build, then look at the final film

Automated checks only prove the structure and files are right. Whether it looks good is judged by looking at the frames. This page covers how to look efficiently, and the problems that keep coming back in real productions.

## Three checkpoints

1. **After building each shot**: `node stills.mjs evidence/stills <3–4 moments inside this shot>`, then compare the stills with the shot list in `DIRECTION.md`: is the focal element obvious at a glance? Is the type large enough? Does anything collide? `stills.mjs` also prints page errors and the API paths the components actually requested, so missing fixtures show up here.
2. **After the first full export**:
   - A 2 fps contact sheet for pacing and composition: `ffmpeg -i final.mp4 -vf "fps=2,scale=384:-1,tile=6x9" -frames:v 1 sheet.png` (one sheet for each half).
   - A 10 fps strip for every transition: `ffmpeg -ss <0.4 s before the cut> -t 1 -i final.mp4 -vf "fps=10,scale=320:-1,tile=10x1" -frames:v 1 cut.png`.
   - Capture full-size frames of information-dense shots to confirm the UI text is legible.
3. **After changes**: re-check only the changed shots and the transitions before and after them, then run through the whole film once more at the end.

## Common problems

| Symptom | Usual cause | Fix |
|---|---|---|
| Title collides with the UI, text crammed into a corner | No type scale and safe area, or the title column is too narrow | Go back to the frame system; give the title column a fixed width and type size; shorten the copy, do not shrink the type |
| The last character or punctuation mark of a (Chinese) caption wraps alone onto the next line | The text is just slightly wider than the column | Cut one or two characters or nudge the column width; do not rely on `nowrap` to let the text overflow |
| UI text is tiny on screen, panels have large empty areas | The product went on screen at desktop size; panel heights set for full screen | Scale up the product root node; fit panel heights to content; tighten the empty areas |
| The push-in lands off target | The landing point was hand-computed under 3D tilt/perspective | Use `screenCenterAt` to measure the real screen position at that moment |
| The camera targets the wrong row, or the top of the frame | Text matching found an earlier similar row, or looked for the row before it finished typing | Query only after the row has fully appeared; find the row by a unique marker (such as a status field); fail loudly if not found, never let −1 become a coordinate |
| A gray patch in the middle when cutting from light to dark | A long cross-fade | Hard cut, or blur the previous shot's focal element out before the cut |
| Popover misplaced, does not follow the scaling | Portal mounted on body; panel rotating in 3D while open | Point the portal container inside the shot; no 3D rotation while it is open |
| A stretch of 3 seconds or more with nothing moving | Nothing follows the last action | Add a slow push-in or a continuing state (for example a new message arriving), or shorten the shot |
| Every element uses the same entrance | Only one reveal was used | Design separate entrances for the focal element, supporting information and background; change it between adjacent shots |
| The first frame is a blank background, and the thumbnail on social platforms is all white or all black | The opening enters from an empty frame, so the first frame has nothing yet | Put the opening's completed state in the first 5–10 frames as the poster frame, then fade out and enter normally; `firstFrames` in `check_delivery.py` reports blank frames |
| Every film looks the same | Case studies or the last film's devices were reused directly | Go back to sections 3–5 of `DIRECTION.md` and derive again from the product |
| The background effect steals from the UI | The atmosphere layer has too much contrast, or sits behind a dense UI | Keep feature-shot backgrounds quiet; save effects for title cards, branding and transitions |

## Metrics are only hints

`check_delivery.py --video` reports the ratio of static frames, the longest static stretch and the number of hard cuts (`pacing`). They exist to say "go look at that stretch": reading pauses are necessary, and small motion on a large dark background also counts as "static". **Do not add meaningless wobble to make the numbers look good, and do not treat passing numbers as the film looking good.**

## Sound

- Listen segment by segment when you can: `sfx-stem.wav` alone, then the master, then the encoded MP4.
- When you cannot listen, say so honestly and check the structure with visible evidence: a spectrogram (`ffmpeg -i music.wav -lavfi showspectrumpic=s=1600x500:scale=log:fscale=log music-spec.png`) and per-second loudness, confirming the impacts, pauses, crescendos and ending land where they should. Excess low end is obvious on the spectrogram.
