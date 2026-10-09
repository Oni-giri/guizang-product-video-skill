# From real components to renderable frames

## Find the feature's real entry point first, not just a few base controls

Start from the actual page/route and locate the feature components the feature uses and how they are composed, then trace their theme, CSS, fonts, icons, providers and state dependencies. For example, to show model switching, reuse the real model selector and its options; to show a file tree, reuse the file tree/node components, instead of importing one Button and hand-writing the rest of the page.

Pipeline order:

1. Import the original feature components or the real composite components directly, and load the full style chain they use. An existing Storybook story, demo route or preview harness can serve as the controlled mount point.
2. Add the minimal providers/contexts, fixed props with no sensitive data, and state fixtures. The adapter's job is to make the **original component** run, not to redraw its internal DOM.
3. When dependencies are complex, solve the concrete problems first: aliases, asset paths, CSS compilation, providers, network/IPC stubs. The starter project mounts components in a browser, so component effects really run: a missing provider gets a provider; a data request gets a fixture in `fixtures/api.js`. Do not hand-write a re-creation because of one error.
4. If it still cannot run directly, prefer reusing existing pure-presentation subcomponents, keeping the original composition structure and original styles. Any necessary source extraction keeps its origin and minimizes changes; do not redesign along the way.
5. Only when a clear platform/technical boundary makes the paths above infeasible, state the specific blocker, what was tried and which shots are affected, and propose a controlled screen recording or a faithful display adapter. If the user has already authorized an alternative, continue; otherwise let the user choose. "Saves time, too many dependencies, hard to animate" are not grounds for a silent re-creation. Keep moving on the other reusable shots.

"Abstraction" means reducing the amount of information on screen at once, highlighting key original components and adjusting the framing. It does not mean redrawing the software. The default style wraps the promo frame; it does not replace the software being demonstrated.

## Getting original components to run inside the video

A tested approach that works (the CodePilot input box, messages, tool steps, approval dialog, model selector and the full plugin page all went on screen this way):

- **Providers**: read the product's App shell and supply the contexts the component depends on (i18n, tooltip, panel/split state, icon defaults) as static values in `product-context.jsx`. A `must be used within ...` error tells you which one is missing.
- **Data**: when a component calls `fetch('/api/...')` in an effect, `fake-api.js` returns a fixture by path. Derive fixtures from the product's own constants or directories (for example, generate the model list from the product's built-in provider presets), so names and icons are real.
- **Non-determinism**: `fake-api.js` pins the clock and the random seed, so components that switch greetings by time of day or pick a random line render identically every time.
- **Real interaction**: typing writes into the real textarea through the native setter and dispatches an `input` event, so React's onChange fires as usual; popovers open and close through real clicks; items are selected through real clicks. The driver computes the expected state from time and only acts when the DOM disagrees, so seeking forward and backward both hold.
- **Popovers and 3D**: Radix-style portals mount on `document.body` by default and do not scale with the shot. Write an adapter that points the portal container at a node inside the shot. While a popover is open, its panel must not have a 3D rotation (positioning libraries compute in the plane).
- **Video scale**: feature shots scale up the product root node as a whole (body text ≥ 22px) or push in with a camera wrapper; do not shrink type to cram it into the frame. If the product has a dark theme and the film goes dark, use its dark theme directly.

## State and animation of original components

- Expand/collapse, selected, toggle, loading, done and similar states are triggered preferably through the original component's props, controlled state or real interaction. Discrete states that change over time (which step is complete, how many characters of the reply are shown) are computed with `useShotState` and passed into the original component as props.
- When the original animation cannot be seeked, wire time to the master timeline only at the display entry point, keeping the original visuals, state semantics and layout; do not remove the original component and swap in fake DOM because of this.
- The shot's outer layer may add scaling, movement, masks, focus and choreography. Extra promo title cards must not pose as product UI; the Chinese/English title typography rules are not forced onto fonts inside components either.
- Choreographed shots may pull out real subcomponents and enlarge them, but must not invent states, interactions or compositions the original software does not have.

## Reuse evidence for every feature shot

Record per shot in `evidence/component-usage.json` or an equivalent manifest: `shotId`, `featureEntry`, `components`, `styleEntries`, `stateDriver`, `adapters`, `reuseMode`, `exceptions`. Paths must point to the source actually used, not a list of component names you hoped to use.

Cross-check the manifest against the build import graph, the actual JSX/mount entry and the stills:

- Were the feature components for that feature used, rather than only generic buttons/cards?
- Do the styles come from the CSS/theme/fonts/assets the component actually uses, rather than a few color constants?
- Are selected, expanded and similar states really rendered by the original component?
- Do the components in the shot match the original page in shape, hierarchy, spacing, icons and state details (framing and proportional scaling are allowed)?

An import in the build graph does not mean it went on screen; a similar-looking still does not prove the source was reused. Read both pieces of evidence together. Mark clearly the parts that do not use original components; do not describe the whole film loosely as "all native components".

React/Next projects: handle the `@/` alias, CSS/Tailwind, Next Image, router, client providers and icon libraries according to the project's actual setup. A successful bundle does not mean styles took effect, nor that data arrived: render stills and look.

Vue/Svelte use their own render entry points; an Electron shell must not start real IPC inside the promo process; when native UI cannot be imported directly, explain why you chose a controlled screen recording or a display-layer adapter.

For native apps (for example Rust/GPUI, SwiftUI), when the user agrees to a faithful rebuild: take dimensions from the source (title bar, tab bar, default panel widths, font sizes and line heights), colors from the theme files, and fonts, icons and logos from the original files in the repository. Model everything that changes on screen (buffer text, cursor, popovers, panel state) as a pure function of film time, and read both the frame and the action timings in `plan.json` from that model. In component-usage, name the source file for each UI element and state that this is a rebuild, not the running app. When the user explicitly asks for code-driven motion, do not quietly degrade into a screen-recording collage.

## Project and assets

Keep source, assets, evidence and renders in a separate project. Record dependency versions and the lockfile, dimensions, FPS, duration, component origins, font and music sources. Do not ship the full original repository/node_modules to others.

Asset handling must cover references inside real components:

- Root paths like `/provider-icons/...` often break in a standalone player. Copy the public assets and fix the base path, or convert small SVGs to data URIs.
- Also handle `url(...)` in CSS, font files, inline icon references and image loading strategies.
- Wait for fonts and image decoding before capturing. No page errors does not mean images are complete; check `img.complete && img.naturalWidth > 0`.
- A local HTTP server is closer to the export environment than `file://`. The final files should avoid depending on the public internet.
- Shared assets need the appropriate license; music from a reference video must not be extracted and reused by default.

## Determinism and timeline

All animation is driven by one master timeline or a pure `seek(t)`. Any `t` must restore the complete frame without depending on earlier frames having been played.

- GSAP: a paused master timeline; in HyperFrames, register `window.__timelines[compositionId]` per its current project contract, and the framework handles media.
- Remotion: state is computed from frame/fps.
- Standalone browser (starter project): `window.seek(seconds)` advances the React clock, the interaction driver, the GSAP master timeline and per-frame drawing in order; Playwright captures frame by frame and FFmpeg exports.

Define the initial/final state of every shot and test seeking forward and backward. The starter project freezes all CSS transitions/animations; micro-animations from motion libraries can jump to their end state with a global switch; product motion that must be kept (loading spinners, progress bars) is rebuilt from time in `onRender`. Random numbers, requests and timers use fixed fixtures.

## Composition and clipping

CardFrame handles shadow, corner radius and outer space and does not clip; CardSurface handles the inner background and clipping. When scaling components up, check the **transformed** bounds. Do not assume a parent with enough height will not clip a zoomed child.

For a card to be centered, center it with an outer flex/grid, scale it with an inner transform, and reserve room for the transform. Avoid a positioning offset multiplied by CSS zoom causing an unexpected drop. The page's total width not overflowing does not prove text/icons inside a local mask are not clipped.

Use the product's complete, official icon, especially an app icon with a rounded-rectangle backplate. Do not crop out the inner symbol as a substitute.

## Handling links

Follow the user's publishing requirements; do not assume every platform in a region bans links. When links must not appear, prefer clearing URLs from the fixtures and showing the address bar as a neutral shape or a blurred placeholder; if a visual cover is unavoidable, the mask must move and scale together with the component. Check the end card, corner badges, screenshots and exported frames together. Do not blur one spot in the DOM while another shot exposes the full URL.
