# Film direction: decide the direction before writing code

What decides whether a film looks good is the design done before any code is written: what it says, what character it has, who the focal element of each shot is, how large the type is, how much the UI is scaled up. Write these into `DIRECTION.md` (a question template is generated at init) before you start building.

Two side-by-side runs show how much this step weighs: the version built only from the checklist and metrics hit the beat 100% of the time, yet the frames were crowded, the type was small, and it looked like a slideshow; the version that wrote the frame system and shot list first, with the same product and the same components, looked completely different (see [case study](case-study.md)).

## 1. Break down the reference (when the user provides a reference video/images)

1. Extract frames and view the whole film: `ffmpeg -i ref.mp4 -vf "fps=1,scale=400:-1,tile=6x8" -frames:v 1 sheet.png`, then capture full-size frames at the key moments.
2. List the devices one by one: what it is, what it expresses (speed? order? connection?), where it appears, how long it lasts.
3. Learn the "method", don't copy the "look": the reference's colors, shapes and fonts belong to its brand. Write down whether this film adopts each one, what it is rewritten into, and the reasoning behind the rewrite.

## 2. Distill the product character

Answer from the repository and the user's input, not from impression:

- **Who uses it, in what situation, and how it feels to use**: calm and professional, light and quick, warm, hardcore, quiet...
- **Design language**: palette, fonts, corner radii, shadows, light/dark theme (if the product has a dark theme, treat it as a candidate), icon style. Write the source down as a file path.
- **Motif candidates**: product elements that can turn into frames directly.
  - The geometric construction of the logo (dot grid, lines, letterforms)
  - The core UI itself (input box, list, canvas, timeline)
  - The shape of the data the product handles (text streams, charts, file trees, waveforms, maps)
  - Domain metaphors (writing → paper and ink; design → construction lines and control points; music → waveforms; finance → trend lines)
  - The literal imagery of the product name

## 3. Propose three directions, spread along different axes

Each direction picks one option on every axis in the table below; the directions must **differ on at least three axes**, and each must be internally consistent. The options are only examples; add your own:

| Axis | Options (examples) |
|---|---|
| Ground and light | Black stage + glow; paper white + ink lines; large blocks of brand color; alternating light and dark; real-environment photographic feel |
| Type voice | Ultra-thin large type; heavy and punchy; editorial serif; monospace technical; rounded and friendly |
| Motif source | Logo geometry; the UI itself; data shapes; domain metaphor; user scenarios |
| Camera language | Flat editorial typography; 3D stage (tilt, orbit, flyover); macro close-up; one continuous shot; screen-recording texture |
| Transition vocabulary | Hard cut on the beat; zoom-through; mask wipe; shape morph; match cut (an element of the previous shot becomes an element of the next) |
| Pacing | Keynote-style unhurried; trailer-style tight; light and playful; quiet narrative |
| Sound | Electronic pulse; piano and strings; percussion-led; ambient pad; a track the user provides |

Then pick one based on product character, audience and release platform, and write down the reasons. If the user wants to see the directions first, give them the three directions and 3–6 key stills to choose from; otherwise continue directly.

## 4. This film's product-specific devices (3–5)

Every device must be expressible as "because the product has X, we use Y". Delete any device for which you cannot name X.

Some derivation examples (they only illustrate the way of deriving; this is not a menu):

| What the product has | What it can grow into |
|---|---|
| A logo built from a dot grid | Particles settle from afar into each cell of the grid |
| Many connected services/plugins | Members orbit the core UI along a tilted ring |
| Developer-facing, code as the material | A glyph field made of the product's own code |
| Note-taking/writing product | Words written stroke by stroke, paper texture, ink bleeding |
| Data analytics product | Real chart paths drawn segment by segment, numbers rolling and settling |
| Design tool | Construction lines, control points, grid snapping |
| Collaboration product | Multiple cursors enter at once, state merges in real time |

[Visual device vocabulary](visual-vocabulary.md) lists more devices with implementation notes; `assets/fx-lab/` has a few samples you can adapt.

## 5. Anti-repetition

- **Across films**: before you start, look at earlier films made with this skill in the same workspace (`DIRECTION.md` and `evidence/contact-sheet.png` in neighboring directories) and the [case study](case-study.md); list their openings, chapter treatment, background devices and score. The new film must differ from the most recent one on at least three axes, and must not reuse its opening device, chapter device or background effect as-is.
- **Within the film**: don't give every element the same entrance; change framing between adjacent shots (wide ↔ close-up ↔ large type) or switch light/dark; don't use the same transition more than three times in a row.
- **The case study is not a template**: the CodePilot film's starfield opening, silver-white light arc and Ask/Switch/Extend chapter title cards belong to that product and that one derivation. Copying them straight into another product is exactly what makes everything look the same.

## 6. Narrative structure, chosen by content

The default "hook → brand → feature proof ×3–5 → quick cuts of small features → ending" is only one option. Alternatives:

- Problem → turn → solution (suits updates that fix a clear pain point)
- Completing one real task end to end (suits agents and workflow products)
- One continuous shot through the product's areas (suits UIs with a strong sense of space)
- Before/after comparison (suits performance work and redesigns)
- Countdown list (suits many small updates)
- A day of use (suits everyday tools)

## 7. Frame system (frame design system)

Derive it from the product and write it as concrete numbers:

- Aspect ratio, frame rate, ground color, safe area (keep important content out of the bottom ~13%).
- Type scale: main title, subtitle, description, with size and weight given per role (and per language in a bilingual film); fonts come from the product or are licensed, with the headline and caption fonts specified separately (`typography.headlineFont / captionFont`).
- UI on-screen scale factor: keep UI body text ≥ 22px in the final film (1080p). Factor ≈ 22 ÷ the product's body-text pixel size. A full window serves only as an establishing shot that shows the whole.
- Light/dark theme: when the product has a dark theme and the film goes dark, use the product's dark theme directly.
- Motion grammar: entrance style, easing family, duration range, and what this film does **not** use (e.g. "no bounce", "no rainbow colors").

## 8. Shot list

For every shot write: time, focal element (only one), frame and action (with sub-beat timing), on-screen copy, sound. Each shot has at least one state change or camera move; more than 2.5 seconds of complete stillness is allowed only while the viewer is reading text. Vary shot length: opening and quick cuts short, feature proofs long.

Finish the shot list before building shots. After building each shot, export stills and check them against the shot list (see [Review](review.md)).
