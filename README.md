# Guizang product video skill

**You shipped the update. Ship the promo video with it.**

[![GitHub stars](https://img.shields.io/github/stars/op7418/guizang-product-video-skill?style=flat-square)](https://github.com/op7418/guizang-product-video-skill/stargazers)
[![License](https://img.shields.io/github/license/op7418/guizang-product-video-skill?style=flat-square)](LICENSE)
![Agent Skill](https://img.shields.io/badge/Agent-Skill-252525?style=flat-square)
![Claude Code](https://img.shields.io/badge/Claude-Code-D97757?style=flat-square)
![Codex](https://img.shields.io/badge/Codex-supported-252525?style=flat-square)

Hand your codebase to an AI, tell it what changed in this release or that you want to introduce the whole product, and it can start making a promo video: sort out the selling points, write the copy, wire in the original components, animate them, write a score, add sound effects, and finally export a video plus a project you can keep editing.

I distilled the process I kept refining while making CodePilot's promo videos into this skill. It focuses on three things: **it looks like your product, people understand what you're saying, and it never feels slow.**

![Guizang product video skill: you shipped the update, where's the promo video?](assets/readme/hero.jpg)

<!-- Paste the GitHub video attachment URL here after uploading. The intro video is not distributed with the skill package. -->

## Start in 30 seconds

Install from the terminal:

```bash
npx skills add https://github.com/op7418/guizang-product-video-skill --skill guizang-product-video-skill
```

Then open your product's codebase and tell an AI coding tool that supports skills:

> Use guizang-product-video-skill to turn this project's main updates from the last three weeks into a promo video. Landscape, 45–60 seconds. Look at the codebase's own components and design style first, show me a few key frames, then continue with animation and sound.

You can also just send it the repository URL:

> Install this skill for me: https://github.com/op7418/guizang-product-video-skill , then use it to make a release-update promo video for the current project.

The first run checks Node.js, Python, FFmpeg and the rendering dependencies, and installs whatever is missing using the official installation methods. Installing system software still follows your tool's and your system's permission settings.

## What can it do for you?

| What you have | What it does with it |
| --- | --- |
| The last few weeks of commits and release notes | Finds the changes worth talking about and organizes them into a few selling points viewers can understand |
| The software's components and pages | Wires in the original components, styles and demo states first, then drives the animation with code |
| An already good design | Keeps the product's colors, fonts, radii, hierarchy and interaction language |
| No mature promo visuals yet | Uses the built-in CodePilot warm-white / charcoal style for the outer frame |
| A few very technical update notes | Rewrites them as full plain-language sentences so people know what changed and what's different in use |
| A film with picture only | Writes a code-generated score for this film, gives actions their own sound effects, and ducks the music when key sounds play |

The picture is rendered by code, so it stays editable. Titles, feature close-ups, full workspaces and detail shots alternate, with both big headline copy and enough time to see what's happening.

![Real components with bilingual typography](assets/readme/components.jpg)

## Three styles: pick the one that fits

On the first run the AI confirms the style. Choices you've already made are reused; you don't answer again each time.

| Mode | When it fits |
| --- | --- |
| **Follow the product's style `repo`** · recommended | The product already has a complete design and you want the video to look like your software at a glance |
| **Default style `default`** | You want to start with CodePilot's warm white, charcoal, card hierarchy and bilingual typography |
| **Hybrid `hybrid`** | Keep the software's real interface inside, and make the outer copy, framing and pacing more shareable |

In all three modes, feature shots use the original product components first. The default style mainly handles outer typography and visual packaging; when platform or framework limits block a component, the AI explains why and offers an alternative.

English headlines and Chinese captions get separate fonts. English carries rhythm and typography; Chinese makes things clear. You can also ask for all-Chinese or all-English.

## How to ask so it gets done right the first time

You don't need a long brief. Say **what to introduce, who it's for and where it's going to be posted**.

**Make a release-update video**

> Introduce the main updates from v2.1 to v2.4, leading with multi-model switching, file preview and browser control. For Bilibili, landscape, about 50 seconds. Follow our product design, keep the copy conversational, and don't read the commit log line by line.

**For overseas users**

> Make an English changelog promo, 45 seconds, mainly for people seeing the product for the first time. Explain what problems these updates solve first, then show the actions. Keep the product's original components and fonts.

**See the direction before the full film**

> First sort out the selling points, the storyboard and four really rendered key frames. Use the default CodePilot style, Chinese with English headlines, and wait for my confirmation before doing the full animation.

**Change a finished film**

> The model-selection part is too slow, compress it to three seconds. Add a clear ding-dong when the notification appears and duck the music. Finally remove the website address at the end and mask any place in the browser where a link shows.

You don't have to supply everything at once; existing context is reused, and you'll only be asked about gaps that affect production.

## From codebase to finished film

1. **Set the scope.** Confirm the product, update range, audience, publishing platform, aspect ratio, language and style; include a reference video if you have one.
2. **Find real content.** Check releases and code, verify feature status, mount the real components and scale them up to video scale.
3. **Set the direction.** Break down the references, distill the product character, propose three clearly different directions and pick one; every visual device has to answer "because the product has what?"; write type sizes, UI scale factors and the shot list as concrete numbers before building.
4. **Build shot by shot.** A GSAP master timeline orchestrates the animation, Three.js / canvas provides background layers, and real components are driven by real clicks and typing; render stills after each shot and compare.
5. **Get the sound right.** Arrange by storyboard, pick timbres from the product character, use recorded samples for SFX first, measure landmarks and align them to actions, then mix and duck the music.
6. **Review, then export.** Look at the contact sheet, every transition and full-size frames of dense shots; fix, then re-export.
7. **Make covers if needed.** 3:4, 4:3 and 16:9, in the visual language of this film, using only frames actually rendered from it.

Every film's devices are derived from the product itself rather than one shared template: the same process should produce completely different films for a note-taking app and for a developer tool.

## One process, three different films

The three films below used the same process but look and sound nothing alike: each one first answered "what does this product have?" and only then "so what should the picture do?".

| Product | What was found in the product | So the film does this | Sound |
| --- | --- | --- | --- |
| **CodePilot** (desktop AI coding client) | Connects to many model providers; a dark, textured desktop app | Dark stage and silver-white light arcs; particles settle into the logo; providers orbit the product; a fly-over of the board | 120 BPM cinematic electronic |
| **Zed** (collaborative code editor) | The editor itself is the star; teammates' cursors appear live | One continuous light-themed shot, the camera never leaves the editor; titles are typed as code comments; teammates' cursors lead the way and finally draw the logo | 128 BPM marimba percussion |
| **T3 Code** (open-source coding-agent console) | Positioned as a "control plane"; ships 5 themes; each harness has its own login command | The whole film is a 3×3 console panel, and pushing into a card enters that chapter; each chapter switches to one of the product's built-in theme colors; the opening types five login commands in five terminals, then sucks them into the panel | 96 BPM lo-fi electric piano |

When making consecutive films in the same workspace, the opening, transitions and background devices of the previous film are avoided too.

The default starting point is **45–60 seconds, landscape, Chinese captions with English headlines**. You can change the length and aspect ratio; portrait needs new framing and text layout, and usually isn't a matter of cropping the sides.

## Where do the music and sound effects come from?

**Music is chosen in order: a track you supply → a music-generation model that actually runs on this machine → original code synthesis.** Code synthesis keeps the arrangement source, lays out sections along this film's shot boundaries and picks timbres from the product character. The repository has synthesis examples in two moods (bright keys, cinematic electronic); what's borrowed is the technique, not the tune.

**Sound effects: find suitable ones first, then fill gaps with the built-in set.** Search available sample libraries first and record source, license and the action each sample suits; for categories without a suitable sample, use the 11 code-synthesized WAVs that ship with the skill, or adjust the synthesis parameters.

**Music and SFX are mixed separately.** Clicks, pop-ups, toggles and completion alerts each have their own sound-effect events. When key feedback plays, the music dips briefly so the ding-dong, confirmation and transition are actually audible.

![Score, action SFX and music ducking](assets/readme/audio.jpg)

## What do you get at the end?

- A publishable **MP4**.
- A **video project** you can keep editing and re-rendering.
- A few key frames for confirming the direction or making covers later.
- Component sources, asset sources, sound events and check records for later tracing and adjustment.

Automated checks catch some structural, file and timeline problems; whether the text is easy to understand, the picture is comfortable and the sound fits still needs actual watching and listening. The project distinguishes what has been verified from what still has caveats.

## Install and update

### With the skills CLI

```bash
npx skills add https://github.com/op7418/guizang-product-video-skill --skill guizang-product-video-skill
```

Follow the prompts to choose your AI tool and install scope. To update, ask the AI to check this repository and update the installed skill; if you've changed files locally, keep your own changes first.

### Manual install

**Codex:**

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/op7418/guizang-product-video-skill.git \
  ~/.agents/skills/guizang-product-video-skill
```

**Claude Code:**

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/op7418/guizang-product-video-skill.git \
  ~/.claude/skills/guizang-product-video-skill
```

For install locations see the [Codex docs](https://learn.chatgpt.com/docs/customization/overview#skills) and the [Claude Code docs](https://code.claude.com/docs/en/skills#choose-where-skills-load). The generic install command above uses the [skills CLI](https://github.com/vercel-labs/skills).

Reopen the session so the tool picks up the newly installed skill. If you cloned manually and have no local changes, run `git pull --ff-only` in the install directory to update.

You can also download the repository ZIP, extract it, and put the folder containing `SKILL.md` into the matching skills directory, naming the folder `guizang-product-video-skill`.

## What environment is needed?

The built-in starter project renders frames with React, esbuild and Playwright, then encodes with FFmpeg. Existing HyperFrames projects can be reused.

| Dependency | Purpose |
| --- | --- |
| Node.js ≥ 22, npm | Build components, run the browser rendering tools |
| Python ≥ 3.9 | Project init, environment check, score and mixing scripts |
| FFmpeg / ffprobe | Audio processing, video encoding and file checks |
| Playwright Chromium | Stills and frame-by-frame rendering for the built-in browser pipeline (WebGL via SwiftShader) |
| React, GSAP, Three.js | Mounting real components, master-timeline animation, background effect layers (installed in the video project) |
| The product repository and its dependencies | Wiring in the original components and styles directly |

Dependency installation instructions are loaded on demand; see [onboarding and dependency check](references/onboarding.md). No extra video service needs to be purchased to use the built-in browser pipeline; the AI coding tool itself and any external services you choose are used under their own terms.

Integration effort varies by component framework. React codebases have ready-made examples; monorepo workspace packages and unusual TypeScript compiler options can be mapped and relaxed in the video project's `integration.config.mjs` without changing product code. Components that need a server, a native runtime or complex context may also need a display adapter layer; interfaces that genuinely can't be wired in are rebuilt faithfully from source and marked item by item in the evidence.

## What's in the repository?

```text
LICENSE                  GNU AGPL-3.0 main license
COMMERCIAL_LICENSING.md   Entry point for separate commercial licensing
SKILL.md                 Workflow, hard constraints and tool entry points
agents/                  Display info for Codex
references/              Film direction, visual device vocabulary, component pipeline, storyboard and copy, audio, review, covers, dependencies and acceptance methods
scripts/                 Init, environment check, SFX landmark measurement, SFX synthesis, mixing, delivery check
assets/starter/          Runnable starter project (technical base, no styling)
assets/fx-lab/           Rewritable visual device samples (streak field, particle settle, glyph field, horizon, slices, orbit)
assets/fallback/         CodePilot default style and display components
assets/audio/            Score synthesis examples in two moods, 11 built-in SFX and their source notes
assets/readme/           Frames from the intro film used on this page
tests/                   Script regression tests and component integration tests
```

When maintaining this skill, you can run:

```bash
python3 -m unittest discover -s tests
node tests/integration.mjs --modules <some-video-project>/node_modules
```

Integration and rendering notes are in the [starter project](references/starter.md); the full production entry point is [SKILL.md](SKILL.md).

## FAQ

**Can it only make videos for CodePilot?**

It works for other software. CodePilot provides the default style and a worked example of the process; in normal use, your own product's components come first.

**Does a model generate a video clip?**

The main picture here is rendered from code, components and a timeline, and the score is synthesized by code too. You can keep changing text, layout, length, animation and sound and re-export.

**Can it produce a film straight from a repository URL?**

Sometimes it still needs to download the repository, install dependencies and confirm demo states. It's a production process that lets an AI complete the work step by step, not a one-click converter that ignores the project environment.

**Can the default style be used commercially without restriction?**

The components and styles adapted from CodePilot in the default style keep their original BSL license. Before use, read the [source notes](assets/fallback/SOURCE.md) and [LICENSE.CodePilot](assets/fallback/LICENSE.CodePilot) and judge the applicable conditions for your use case. The default style has not been relicensed as MIT here.

**Can I use my own music, logo or reference film?**

Yes, hand the assets and requirements to the AI. Reference films are used to understand pacing and presentation; imported assets need an applicable license, and their sources are kept.

## Feedback and improvements

Share your work, problems and suggestions in [Issues](https://github.com/op7418/guizang-product-video-skill/issues). When reporting, include the AI tool you used, the product's tech stack, the stage that failed, and redacted logs or frames.

If you'd also like an AI to help with image-and-text posts, see the [Guizang social card skill](https://github.com/op7418/guizang-social-card-skill).

## License

GNU AGPL-3.0 © 2026 [op7418](https://github.com/op7418)

Except for the separately licensed content noted below, this repository's workflow, documentation, scripts, starter project and original audio assets are licensed under the **GNU AGPL-3.0**; see [LICENSE](LICENSE) for the full terms.

- Keep the copyright, license and related notices when copying or distributing; state your changes when publishing a modified version.
- When distributing a modified version or derivative program governed by this license, follow the AGPL-3.0 requirements on licensing and corresponding source.
- If a modified program supports remote network interaction, offer the users interacting with it a free way to obtain the corresponding source of that version, per section 13.
- The AGPL-3.0 allows commercial use and paid distribution; charging does not waive the applicable license and source obligations.

**Separately licensed content:** the components and styles adapted from CodePilot in [assets/fallback/](assets/fallback/SOURCE.md) remain under the [Business Source License 1.1](assets/fallback/LICENSE.CodePilot), including its Additional Use Grant and Change Date. Adding the main license does not convert them to AGPL. When using, modifying or distributing a project that contains these components, check the relevant terms as well; a combined project cannot be declared as governed solely by the AGPL or as commercially unrestricted.

Integrated product components, logos, fonts, third-party music or sound effects are used under their own applicable licenses. A generated video does not automatically become an AGPL work merely because this tool was used; if the output contains protected components, assets or code, their applicable terms still need to be kept and followed.

For closed-source integration, white-labeling, platform bundling, marketplace partnerships or a separate license where the AGPL conditions don't fit, see the [commercial licensing guide](COMMERCIAL_LICENSING.md). This section is a reading guide; the actual rights and obligations are those of the applicable license or a written agreement between the parties.
