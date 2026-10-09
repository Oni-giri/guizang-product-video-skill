# The original CodePilot case: keep the practices, do not freeze incidental parameters

The final film was 48 seconds, 1920×1080, 30 FPS, 14 shots, 120 BPM. Real React components bundled with esbuild formed the picture, driven by GSAP, exported with HyperFrames. The music was code-original instrumental, paired with recorded SFX from a local sample library whose source is credited as Pixabay; in the very first version even the alert tones were code-synthesized. The skill's default flow adopts the later combination; see [audio sourcing](audio-sourcing.md) for sources and built-in substitute SFX. The above is one successful instance, not the mandatory stack or length for every product.

## What worked

- Import the model selector, RuntimeSelector, input box, tabs, card container, CLI maintenance row, buttons and icons directly; providers use a minimal read-only adapter.
- Shots cut from a chapter word to selection cards, then to the input area, workspace and notification, without repeating the same layout.
- File tree, diff, browser content and system notifications are controlled display data; do not claim the whole business system is really running.
- Music, SFX cues and visuals share one timeline. Operation actions of about 0.3–0.6 seconds, plus enough explanatory hold.

## Problems actually fixed during iteration

| Problem | Root cause | Reusable check |
| --- | --- | --- |
| Picture good but seems silent | Early music too quiet; a track existed but was not audible enough | Measure loudness and audition the final film |
| Pacing feels stuck | Repeated layouts, animation and static holds too long | Explain earlier, intersperse title cards and close-ups, make every pause carry information |
| Direction draft drifts from the user's intent | Generated concept images cannot replace real component animation | Wire in code components early; stills come from actual renders |
| GLM 5.3 card cropped at the bottom edge | Positioning offset stacked with zoom scaling, exceeding the local mask | Check component bounds after transform, center and reserve space |
| TokenDance icon broken image | Component referenced the website root path; the standalone preview lacked the asset | Inline the original SVG or copy it correctly; verify images in preview and export separately |
| Little text yet unclear | Small text was only phrases, with no feature or result | Full sentences, appear early, schedule shots by reading time |
| Incomplete logo | Only the central symbol of the icon was used | Use the official rounded-rectangle app icon |
| Components missing in extracted frames | CSS transition/visibility fought the main timeline for state | Hook the original animation to the main clock; disable only the specific conflicting elements when necessary; seek back and forth to verify |
| Does not meet this release's requirements | Browser and ending contained URLs | Strip URLs from fixtures, neutralize the address bar, remove the ending link and its animation |

Checking stills cannot replace watching the pacing; a passing framework check cannot replace checking the final film. Social covers are made at the user's request, see [cover](cover.md) for the method; when not mentioned, ask once at delivery and do not expand by default.

## Lessons from the second project

Chinese serif (Song) headlines, decorative English labels, vague full sentences and a BGM-only audio track exposed default-value problems. For the specific practices see [storyboard and copy](story-and-copy.md) and [audio and delivery checks](audio-and-qa.md); this file keeps the case background.

## The third project: why checklist-style iteration got worse

The same CodePilot repository went through three versions, and the comparison is telling:

| Version | Approach | Result |
|---|---|---|
| Model working directly (HyperFrames) | First wrote a `frame.md` frame system (type scale, UI enlarged to 22px, margins, safe area), then wrote a detailed shot description for every shot, finally orchestrated shot by shot with GSAP | Good pacing, refined components, text motion in place |
| Skill after iterating on "12 blueprints + motion primitives + beat-landing/static-frame metrics" | Each shot wore a blueprint name, entered via uniform data attributes, accepted by metrics | 29/29 actions on the beat, every cut on a bar line; yet the frame was cramped, text small, headlines collided with icons, large empty areas in the UI |
| This skill's current flow | First write `DIRECTION.md` (reference breakdown, product character, three directions, frame system, shot list); real components on screen at video scale; GSAP main timeline + Three.js/canvas background layer; stills per shot, contact sheet and transition strip for the whole film | See next section |

Lesson: **the model will satisfy whatever can be quantified.** Compress "looks good" into blueprint names and metrics and you get a film with perfect metrics and a mediocre picture. What makes quality land is the design before writing code: the frame system written as concrete numbers, the shots written down to the second.

## The CodePilot film: how the devices were derived from the product

50 seconds, dark stage. What the two reference videos (the Hero UI brand film, the Talis launch film) yielded on breakdown were practices: starfield warp, construction lines drawing the logo, the product rising from behind a glowing horizon, chapter words, sliced offset reveal, faux 3D. Colors were not copied, because CodePilot is charcoal monochrome.

| Device | Because CodePilot has… |
|---|---|
| Streak-field opening, with "today it's Claude / GPT / Gemini…" rotating | Users switch back and forth between models; that is the pain point it solves |
| Particle settle into each cell of a 5×5 dot grid | The logo itself is a fading dot grid; geometry and opacity taken from the real SVG |
| Silver-white light arc with only the faintest color fringe | Monochrome brand, with a dark theme |
| Dark real UI enlarged 1.6–2×, with a slight perspective angle | The product has a complete dark theme; Agent chat, approvals and model selection are real interactions of real components |
| Provider icons orbiting the input box | 17+ providers in the presets (count from the README, icons from product dependencies) |
| Plugin page laid flat as a board, camera fly-over, skill cards lifting along the Z axis | Skills and MCP are a full page of cards |
| Glyph field made of the product's source code | A developer-facing tool |
| Chapter words Ask / Switch / Extend | The three core capabilities happen to be three verbs |

The score is code-synthesized F minor electronic music (`assets/audio/score-example-cinematic.py`), with sections arranged on shot boundaries; the SFX are Pixabay recordings from the local media-use library, each landmark measured individually.

**This table is an example of one derivation, not a template.** Swap in another product and most of these devices no longer hold: no dot-grid logo means no particle settle; a light, paper-like product should not use a glowing horizon; a product that connects only one or two services should not do an orbit. Re-derive from the new product following the [film direction](direction.md); when making consecutive films in the same workspace, change the opening, chapter and background devices.

The specific pitfalls hit while making this film (popover portal, 3D push-down near the landing point, light/dark switching going gray, punctuation dropping to its own line, GSAP timelines being thenables) are written into [component pipeline](component-pipeline.md), [starter project](starter.md) and [review](review.md).
