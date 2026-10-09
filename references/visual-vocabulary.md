# Visual device vocabulary

Common devices, grouped by purpose. Each entry says what it expresses, which aspect of the product it should be derived from, implementation notes and common pitfalls. **This is a vocabulary, not a menu**: one film picks 3–5 that can be derived from the product and leaves the rest. Read [Film direction](direction.md) before choosing.

All devices share one technical constraint: the frame is determined by time alone (seek-safe). GSAP animations hang on the master timeline; canvas/WebGL is written as a pure `render(t)` function registered with `onRender`; random numbers use a fixed seed. `assets/fx-lab/` has adaptable samples for the devices marked ★.

## Opening and hook

| Device | Expresses | Derive from | Implementation notes | Pitfall |
|---|---|---|---|---|
| Streak field / warp ★ | Speed, entering a world | The product's "fast" or "many" | Three.js line segments, position = integral of velocity | Looks overblown on a calm product |
| Slot cycling | Repetition of a pain point (A today, B tomorrow) | Things users actually switch between | Hard cuts or very short blurred cuts, intervals getting faster | Crossfades lose the rhythm |
| Real-UI macro | Straight into the product | The single most representative control | Real component scaled 3–4×, the rest blurred with depth of field | Text wraps or overflows once scaled up |
| One sentence written out character by character | Quiet, weighty | Writing and conversation products | Character by character or stroke by stroke, with a cursor | Sentence too long, the viewer won't wait |
| Data first | Open with the result | Provable numbers | Rolling numbers + chart paths drawn in | Numbers without a source |

## Brand and logo

| Device | Expresses | Derive from | Implementation notes | Pitfall |
|---|---|---|---|---|
| Particle settle into shape ★ | Scattered things coming together | The logo itself is a geometric construction | Sample cells from the rendered SVG (`targetsFromSvg`); swap to the crisp SVG once the particles settle | Forcing it on a logo that isn't geometric |
| Construction lines and control points | Precision, designed | Design products, or a logo with a grid | SVG lines drawn with `strokeDashoffset`, square nodes pop in | Too many or too bright lines steal from the subject |
| Wordmark stroke to fill | From sketch to finished | A distinctive wordmark | Draw the outline path, then fill | Chinese glyph paths are too complex |
| Extrusion / isometric blocks | Structure, solidity | The logo has 3D potential | CSS 3D stacked layers or Three.js extruded geometry | Overly glossy materials look cheap |
| Shape morph | One thing becoming another | Logo and product UI share a shape | SVG path interpolation (point counts must match) or masks | Ugly in-between states |

## Stage and background

| Device | Expresses | Derive from | Implementation notes | Pitfall |
|---|---|---|---|---|
| Glowing horizon ★ | Arrival, ceremony | Dark, premium products | Multi-layer CSS radial gradients + a dark body occluding them | Used in consecutive shots; clashes with light-colored products |
| Gradient field | Mood, brand color | Products with a rich brand palette | Slowly moving large color blobs (canvas or CSS), low contrast | Behind a dense UI it becomes hard to read |
| Glyph field ★ | Code, data, the underlying layer | Technical products, using their own code or data | 2D canvas glyph grid + noise brightness, center left empty | Feels cold to a non-technical audience |
| Paper and ink | Writing, warmth | Writing and note-taking products | Paper texture + ink-spread mask | Texture too heavy, looks dirty |
| Grid and dot matrix | Order, tool feel | Design and data tools | Very faint dots or lines with parallax against the camera | Fights the UI's own grid |
| Environmental depth of field | Real usage scenario | Hardware, mobile | Device mockup + blurred background | Faking hardware the product doesn't have |

## Product on screen

| Device | Expresses | Derive from | Implementation notes | Pitfall |
|---|---|---|---|---|
| Scaled framing + push/pull | Let the viewer see one thing clearly | All feature shots | A camera wrapper animated by GSAP on x/y/scale; measure the landing point on the timeline first (`screenCenterAt`) | Hand-computed landing points drift under a 3D tilt |
| Perspective-tilted panel | Space, premium feel | Dark UIs with clear hierarchy | Set `perspective` on the parent, small `rotationX/Y` on the panel, changing slowly over time | Popovers (portals) mis-position inside 3D transforms; return to flat when they open |
| Flat-laid board + camera flyover | Overview, system | Pages with many cards or modules | Whole page rises from `rotationX 50–60°` to 10–20° | Rising too fast is dizzying; card text too small |
| Lift details along Z | Point out the key item within the whole | Key items in a list/cards | In the same `preserve-3d` container, give a copy `translateZ` and a shadow, darken the background | Lifting a hand-drawn copy instead of the real component |
| Orbit ★ | Many things connected to one core | Integrations, providers, plugin count | Manual projection: depth controls size, opacity, blur and z-order | Inventing members to fill the ring |
| Cursor operation | This is a real thing you can click | Interactive features | Cursor moves in the product's coordinate system, clicks land on the beat, real clicks trigger state | No state change after the click |
| Real typing and streaming output | The agent/conversation is working | Conversation and generation products | Write into the real input with the native setter; truncate the reply by character over time | The whole passage appears at once |

## Chapters and text

| Device | Expresses | Derive from | Implementation notes | Pitfall |
|---|---|---|---|---|
| Chapter word | Section break, rhythm | Features group into a few verbs | One word fills the frame, 1–1.5 s | Meaningless words (UPDATE, NEW) |
| Sliced offset reveal ★ | Signal, interruption | One strong section change is needed | Text cut into horizontal strips that snap back from different offsets; with thin light bars | Used as the default title entrance |
| Per-character blur-in | Refined, breathing | Most titles | `Split` + `reveal`, 0.02–0.05 s stagger | Used on every element, becomes monotonous |
| Rapid word cuts | Many small features | Small features not worth a shot of their own | One word per beat, rotating entrance styles, with a counter | Each word stays too long, becomes subtitles |
| Light sweep | Emphasis, completion | End card or key words | A glowing horizontal line sweeps across fast | Frequent use loses its weight |
| Editorial serif title | Taste, content products | Content and reading products | Serif English + sans-serif Chinese, tightened tracking | Serif Chinese looks dated |

## Transitions

| Transition | Use for | Implementation notes |
|---|---|---|
| Hard cut on the beat | Impact, abrupt light/dark change | The cut lands on the beat; blur the previous shot's focal element first for a cleaner cut |
| Zoom-through | From concept into the product's interior | The previous shot's focal element scales up and fades out; the next shot scales back from slightly larger |
| Push-in continuation | An element of the previous shot is the next shot's focal element | Push in to that element; the next shot starts at the same position and size |
| White flash / black | Between major sections | 0.15–0.25 s, with an impact sound |
| Mask wipe | Between parallel features | Shape comes from the product (rounded rectangle, logo shape) |

Don't do long crossfades between light and dark shots: a grayish frame appears in the middle. Use a hard cut, or blur the previous shot's focal element out first and then cut.

## Technical notes

- **Three.js in headless export**: the starter project's `render.mjs` / `stills.mjs` already carry the SwiftShader flags; the renderer needs `preserveDrawingBuffer: true` and a pixel ratio of 1.
- **One scene per WebGL canvas**; keep the whole film within 2–4 contexts; if a background layer can be done with CSS or 2D canvas, don't use WebGL.
- **GSAP**: the master timeline is paused and driven by `seek`. `fromTo` writes start values at build time, so build after layout measurement is done. Don't use nodes React will re-render as GSAP targets; hang animations on a stable wrapper layer.
- **CSS filters** (blur) and 3D transforms both work in per-frame screenshots, but large-area blur slows the export down; render a few frames first to estimate the time.
