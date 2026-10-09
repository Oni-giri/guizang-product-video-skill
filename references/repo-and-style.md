# Repository and style audit

## Update facts

Read the repository rules and the relevant directory index first, then search in a targeted way. Prefer release notes, changelog, version tags and implementation paths; do not dump full logs or environment files.

Build `feature-evidence`, with each entry containing:

| Field | Meaning |
| --- | --- |
| feature / benefit | What was implemented / what the user gains |
| status / release | Released, merged or in development; which version it belongs to |
| source | repo-relative path + commit/tag, or a document the user provided |
| component | Real reusable components and related styles |
| demoState | Inputs, state and fixtures needed for the demo |
| limits | Parts that cannot be proven, or the scope of the demo |

When the user says "the last few weeks", set the range from today's date first, then map it to the version history; do not use the date of a reference tweet. If the range is not yet settled, suggest the last 2–4 weeks and state that this is a proposed range.

## Auditing original components and design dependencies

Follow the feature pages to find the actual feature components and composition layer first, then read the tokens / CSS variables / Tailwind config, fonts, icons and theme context they use. The audit outputs the feature components, the composition structure and their complete design dependencies.

Write in `style-audit.md`:

1. Palette and semantic roles: background, surface, text, muted text, stroke, accent, with code sources.
2. Fonts: determine separately the font, weight, line height and actual load result for English headlines and for Chinese headlines / body. The specific font assignment for promo headlines follows [storyboard and copy](story-and-copy.md).
3. Space and shape: base spacing, corner radius, shadows, line widths, density.
4. Brand: full app icon / horizontal logo / monochrome version and where each applies; use the repository's existing assets.
5. Shot fit: which details of the original UI can be reused directly, which need enlarging, cropping or splitting; whether the product has a dark theme that can be enabled directly.
6. Motif candidates: the geometry of the logo, the core interface, the shape of the data the product handles, domain metaphors. These are the raw material from which [film direction](direction.md) derives product-specific devices.
7. Decision: repo / default / hybrid, with reasons and the brand identity points to keep.

"The aesthetics are bad" must become actionable judgments: messy hierarchy, inconsistent type size / spacing, insufficient contrast, information density too high, cluttered borders / shadows. Do not treat your own taste as an objective conclusion, and do not swap out the user's brand behind their back.

## Scope of the default style

The default style is extracted / adapted from CodePilot's CardFrame / CardSurface, rounded buttons, tags and visual tokens. It provides the frame container and the typographic base; it does not include feature functionality such as model lists or browsers, nor does it supply another product's brand.

- `default`: the visual tone is used for promo title cards, backgrounds and outer containers; feature shots keep the original feature components and their internal styles first. Only when the user separately and explicitly asks for a reskin, handle it within the scope they give.
- `hybrid`: borrow only the frame wrapping; the target product's key interfaces, brand colors and states stay recognizable.
- `repo`: build according to the product design audit results.

Do not copy real conversations, accounts, keys, browsing history or business data from the user's repository into a shareable project. Fixtures must express real functionality but must not pose as real performance / customer results.
