# fx-lab: rewritable device samples

The files here prove that several devices can be made seek-safe ("any single frame renders the same on its own") and exported from a headless browser (WebGL via SwiftShader). They are **samples, not a style pack**:

- Don't move the whole set of devices into one film. A film usually has 3–5 specific devices, derived from the "product character" section of `DIRECTION.md`.
- Rewrite before use: colors, shape sources, density, speed curves and direction all change to this product's. Every entry in the parameter table says where its value should come from.
- In the same workspace, the opening, transitions and backgrounds the previous film used get replaced or clearly rewritten in this one (see "anti-repetition" in `references/direction.md`).
- Devices not included here (gradient fields, ink, isometric extrusion, data curves, paper, physical springs…) are written under the same constraints: pure functions of time, attached to `onRender` or the GSAP timeline.

| File | Device | Where its parameters come from in the product | When not to use it |
|---|---|---|---|
| `warp.js` | Streak field (points rushing toward/away from the camera) | Color and density from the palette and the film's energy; direction matches the narrative (entering/leaving/passing through) | Calm, gentle products; shots that already have a large moving background |
| `settle.js` | Particles settling into a shape | Target shape from the product's own geometry: logo SVG, icons, chart paths, key UI outlines (`targetsFromSvg`) | Forcing a logo that isn't geometric; shapes too thin for particles to read |
| `glyph-field.js` | Glyph field | Characters from the product: its code, CLI output, data values, the language it serves | Products for non-technical audiences (unless the characters are themselves the product's content) |
| `horizon.jsx` | Glowing horizon stage | Core and edge colors from the brand; monochrome brands keep a near-white core and a very faint color edge | Light, paper-like, hand-drawn products; several consecutive shots all using it |
| `slices.jsx` | Sliced offset reveal | Slice count, offset amplitude, light-bar color | As the default title entrance; quiet narrative passages |
| `orbit.js` | Hand-projected orbit | Member count from real data (integrations, providers, plugins) | Too few members to form a ring; inventing members to fill it |

Each file has more specific notes at the top. For how the CodePilot film mapped these devices to its product, see `references/case-study.md`; it's one example of derivation, not the standard answer.
