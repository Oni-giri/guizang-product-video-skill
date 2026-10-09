# Starter project: technical foundation, not a final-film template

After init you get a 10-second, 3-shot **technical sample**. It only proves that the chain "real components mounted → timeline → screenshot at any moment → MP4" works. It deliberately has no visual style: the production film's frame system, shots and devices are all rewritten for this product according to `DIRECTION.md`.

## Running

Requires Python 3, Node.js, FFmpeg. Run the environment check per SKILL.md first; install anything missing per [dependency installation](onboarding.md).

```sh
python3 <skill-dir>/scripts/init_project.py --output <video-dir> --style repo --repo <repo-dir>
cd <video-dir>
python3 <skill-dir>/scripts/check_environment.py --project . --engine browser
npm run build
node stills.mjs evidence/stills 1.5 5 8.5          # batch stills in one session, and print page errors and API requests
node render.mjs --from 4 --to 7 --output renders/draft.mp4   # partial draft, no audio needed
node render.mjs --silent-demo --output renders/technical-demo.mp4
npm run preview                                     # browser console: await seek(4) or playFilm()
node cover.mjs                                      # export 3:4 / 4:3 / 16:9 covers from cover/cover.html (see references/cover.md)
```

Final export:

```sh
python3 <skill-dir>/scripts/mix_audio.py plan.json
node render.mjs --audio assets/master.wav --output renders/final.mp4
python3 <skill-dir>/scripts/check_delivery.py plan.json --video renders/final.mp4 --mix-report evidence/audio-mix.json
```

Export takes per-frame screenshots (JPEG intermediate frames, x264 encoding). A 50-second film with WebGL and blur filters usually takes 2–4 minutes; render a few seconds first to estimate. `--silent-demo` is only for the technical sample; for a production silent film the user asked for, set `audioRequired:false` and record `audioExceptionReason`.

## Runtime structure

```
src/client.jsx        mounts <Film>, runs each shot's builder once fonts and fake data are ready, exposes window.seek / __filmReady
src/engine.js         seek(t): React clock → interaction drivers → GSAP master timeline → shot visibility → onRender canvases
src/film-store.js     useShotState(select): components read discrete state by in-shot time (which step, how many characters typed)
src/fake-api.js       fixed clock, fixed random seed, fetch that returns fixtures by path, silenced EventSource/WebSocket
src/fixtures/api.js   API fixtures; derive them from the product's own constants/catalogs where possible so names and icons are real
src/product-context.jsx  the providers the product shell would normally supply (i18n, theme, tooltip, router/panel context)
src/kit/              Split + reveal (split-text entrance), Cursor + paintCursor, offsetCenter / screenCenterAt, setFieldValue / typed / ensureOpen
src/shots/index.js    each plan.json shot id → view component + builder
src/film.css          this film's frame system (type scale, layout), plus the mechanics per-frame rendering needs
src/adapters/         static stand-ins for framework runtimes such as next/image, next/navigation; alias as needed
```

`seek(t)` is a pure function of t; jumping forward or backward and single-frame renders give identical results:

1. `flushSync` pushes the time to React. Components use `useShotState(l => stageAt(l, [...]))` to re-render only when a discrete state changes, e.g. a tool step appears or the reply gains a few characters.
2. Run the drivers registered with `onDrive(id, fn)`, i.e. **real interactions**: typing into the real input (`setFieldValue` + `typed`), clicking a real button to open a real popover (`ensureOpen`). Drivers must be idempotent: compute the expected state from time first, and act only when the DOM differs. Return a Promise when you need to wait for popover positioning; `render.mjs` awaits it.
3. `master.seek(t)`: all GSAP animations hang on this one paused master timeline, placed in absolute film time.
4. Show/hide shots by time (0.8 s of margin on each side for transition overlap).
5. Call each per-frame draw registered with `onRender(id, fn)`: Three.js, 2D canvas, time-dependent style computation.

### Writing a shot

```jsx
// src/shots/agent.jsx (illustrative; name and structure follow this film's needs)
export function AgentView() { /* real components + this film's layout; GSAP targets are stable wrapper layers */ }
export const buildAgent = tl => {
  const s = shot('agent');
  // 1. Measure first (layout exists): offsetCenter(el, root), or screenCenterAt(tl, t, el) for the screen position after 3D transforms
  // 2. Then place animations on tl: tl.fromTo(el, from, to, s.start + 0.4)
  // 3. Register per-frame work: onDrive('agent', local => ...), onRender('agent', local => ...)
};
```

- Shot start/end times live only in `plan.json`; code reads them through `shot(id)`, so time has a single source.
- GSAP's `fromTo` writes start values at build time, so measure before placing animations.
- GSAP timelines are thenable: `await tl` waits for the timeline to finish, and a paused master timeline never finishes. A builder can be an async function, but never await the timeline itself.
- Don't use nodes that React re-renders or conditionally renders directly as GSAP targets: wrap them in a stable wrapper layer and animate that.
- The product's micro-animations (motion/framer-motion, CSS transitions) fight the film clock for state: `film.css` already freezes CSS animations; for products using the motion library, enable `MotionGlobalConfig.skipAnimations` in `client.jsx`. Things that must move, like a spinning loader icon, set their transform by time in `onRender`.
- Background effects can be adapted from `assets/fx-lab/`; see [visual device vocabulary](visual-vocabulary.md).

### Poster frame

Most openings enter from an empty frame, but platforms use the first frame as the thumbnail. Solution: overlay a still of the opening's completed state on the top layer, fully opaque for the first 0.3 s (about 9 frames), then fade it out over 0.3 s. The opening animation underneath still starts at 0 s as normal; the timeline and SFX don't change.

In the starter project the same DOM is driven by the GSAP master timeline and can't sit at 0 s and at the completed moment at once, so the poster uses a still from a real render:

1. Once the opening is built, pick the moment when the opening section is complete and all titles are present, export a still, and put it in `public/` (`build.mjs` copies it to `dist`):
   ```sh
   node stills.mjs public/poster 5.9 && mv public/poster/t005.90.png public/poster.png && rmdir public/poster
   ```
2. Add `<img id="poster" src="poster.png" alt="" />` at the end of `<main>` in `film.jsx`, styled to fill the frame with a `z-index` above every shot, then `npm run build`.
3. In the opening shot's builder, hang the fade-out on the master timeline. Don't use `onRender`: it is only called near its shot, so jumping straight to a later part of the film leaves the poster covering everything.
   ```js
   tl.fromTo('#poster', {opacity: 1}, {opacity: 0, duration: 0.3, ease: 'none'}, 0.3);
   ```

If the opening changes, export the still again, or the poster and the film won't match. For films whose views are themselves pure functions of time (rendered directly from `t`), you can skip the still and mount a second `<Opening t={completed moment} />` as the poster layer within the 0.6 s; same principle.

## Integrating the repository

1. Import the feature's original feature components and composition layers directly in the shot views. Don't wire up a few basic buttons and hand-write the rest of the UI.
2. Read the product's root layout and App shell, and write the providers the components depend on into `product-context.jsx`, all with static values. A missing provider throws at runtime (`xxx must be used within yyy`); add them one by one following the errors.
3. For components that fetch data in effects, provide fixtures by path in `fixtures/api.js`. The `api` list printed by `stills.mjs` is the set of paths actually requested; use it to find gaps.
4. Compile the product's real styles into `src/product.css` (below), keeping theme, fonts, icons and state rules. When the product has a dark theme, enable `ProductContext dark` directly.
5. Put brand assets, fonts and public icons in `public/` (copied to the web root), and fix root-path references in components (such as `/provider-icons/...`).
6. The build writes `evidence/component-imports.json`; record reuse evidence shot by shot, see [component pipeline](component-pipeline.md).

`--style default` / `hybrid` copy the default style components; `repo` does not. The starter sample is laid out for 1920×1080; changing the aspect ratio requires re-laying it out.

### Resolution config

```js
// integration.config.mjs
import path from 'node:path';
const repo = '/absolute/path/to/product', video = path.resolve('.');
export default {
  repoDir: repo,
  aliases: {
    '@': path.join(repo, 'src'),
    'next/image': path.join(video, 'src/adapters/next-image.jsx'),     // add only if a component actually uses it
  },
  external: [], loaders: {}, define: {},
  esbuild: {},   // other esbuild options, e.g. tsconfigRaw
};
```

The builder emits a browser IIFE bundle: dependencies are resolved from the product's `node_modules` first, with React/ReactDOM always pointed at the video project's copy (two copies of React cause `Cannot read properties of null (reading 'useContext')`). When a product dependency is missing, install only pinned display dependencies in the video project. For strictly isolated layouts such as pnpm, map resolution paths according to the actual workspace. Dependencies containing top-level await can't be bundled into an IIFE: switch to their synchronous entry, or change the build to ESM.

Workspace packages in a monorepo that export TS source directly: alias the package name to its `src`; for packages with subpath `exports`, read their `package.json` and generate an alias table of subpath → source file. When the product has `verbatimModuleSyntax` enabled, type imports are preserved as-is and may drag server runtime into the browser bundle; use `esbuild: {tsconfigRaw: {compilerOptions: {verbatimModuleSyntax: false}}}` to relax it for this display build only.

When dark tokens hang on the `dark` variant of `:root`, the `dark` class must go on `<html>` (run `document.documentElement.classList.add('dark')` before mounting in `client.jsx`); putting it on a div has no effect. When several themes must appear in the same frame at once, first confirm the Tailwind utilities reference `var(--token)` directly, then write the theme colors as element-level CSS variables.

When an alias needs to "replace one export of a module and keep the rest" (e.g. to mount a popover's portal inside the shot), the adapter can first `export * from '<absolute path to the real file>'` and then separately export a stand-in with the same name.

### Next / Tailwind style chain

Tailwind source CSS must be compiled first. Tailwind v4: create `src/product.input.css`, import the product's real CSS entry, and scan both the product source and the video source:

```css
@import "/absolute/path/to/product/src/app/globals.css";
@source "/absolute/path/to/product/src";
@source "./";
```

```sh
npx @tailwindcss/cli -i src/product.input.css -o src/product.css   # same version as the product
npm run build
```

If shot code adds new Tailwind classes, recompile. Tailwind v3 uses the matching version of the CLI and a config that inherits the product's theme/plugins, with `content` covering both the product and the video source. `url(...)` fonts/images in the product CSS must be findable under `dist/`. Sources: [esbuild nodePaths](https://esbuild.github.io/api/#node-paths), [Tailwind CLI](https://tailwindcss.com/docs/installation/tailwind-cli).

## plan fields

- `demo`: true for the technical sample; set it to false once the production content is done.
- `product / width / height / fps / duration / style / audioRequired`: project specs.
- `typography`: defaults to `mode:bilingual`, with `zhFont / enFont` specified separately and `zhStyle:sans-serif`; when the user specifies monolingual or other fonts, record the reasoning in `exceptionReason`.
- `shots[]`: `id, start, end, type, headlineEn, headline, plainExplanation, description, descriptionAt, claim, source, component, actions`. The shot's implementation in code follows the shot list in `DIRECTION.md`; plan records time, facts and sound, and the two must agree.
- Shots with `claim` set to true must have a `source`. Format: `file:docs/release.md` (relative to the video project) or `repo:src/features/panel.tsx` (relative to `plan.repo`), with `:line` / `#Lline` supported; a bare path is looked up in the video project first, then in `plan.repo`; URLs, version tags and commit references are left to fact-checking. A brand opening doesn't need a fabricated source.
- `component`: the actual source path or adapter; may be null for title cards.
- `actions`: unique `id`, `at` relative to shot start, action description, `soundRequired`.
- `audio.music / audio.cues`: a cue's `at` is the absolute film time where the file starts, `syncOffset` is the audible landmark within the file, satisfying `at + syncOffset = action time`. Measure landmarks with `scripts/sfx_landmarks.py`, don't guess. Optional `onBeat` / `beatDivision` are checked against `audio.beatGrid`.
- `descriptionAt`: when the description text appears, relative to shot start; used for reading-time hints.

Re-mix after any change to the storyboard or score; the final export verifies the hashes of plan and master. Generic placeholder components carry `data-skill-placeholder`; in production mode the build rejects placeholder content still on screen.

## Integration regression

After modifying the builder, engine or kit, run:

```sh
python3 -m unittest discover -s <skill-dir>/tests
node <skill-dir>/tests/integration.mjs --modules <video-dir>/node_modules
```

The integration test constructs a product repository in a temporary directory and verifies: dependencies and aliases that exist only in the product resolve, CSS assets are copied, component effects receive data through the fixture API, GSAP state is correct when jumping forward and backward, and WebGL renders in headless export. It does not install dependencies automatically.
