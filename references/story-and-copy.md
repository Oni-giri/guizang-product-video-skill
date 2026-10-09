# Storyboard, copy and pacing

## From update list to story

Pick the structure first in [film direction](direction.md): "state the claim, then prove it section by section" is the most common; others include "problem → solution", "complete one full task", "one continuous take" and "before/after". Choose by content. 45–60 seconds usually fits 3–5 groups of updates and about 10–14 shots; this is a capacity reference, not a template that must be filled. A minor release can be 20 seconds; a complex feature can run longer.

Record each shot in `plan.json`: start/end time, type, main copy, explanation, selling-point source, real component / adapter, main action, sound cue. Estimate reading and demo time first, then fit to the music beat. Do not lock 48 seconds first and then cram copy into it.

Taking the "claim → proof" structure as an example, a reference section breakdown:

| Section | Job of the frame | Pacing reference |
| --- | --- | --- |
| Opening | One direct statement of the change, big type or brand | 2–4 s |
| Core capability | Title card states the capability → component close-up proves it → workspace gives context | 7–12 s per group |
| Small improvements | 2–3 independent, clearly separate details | 2–4 s each |
| Ending | Product mark and one closing line; the call to action follows release requirements | 2–3 s |

Shot variation comes from "where the viewer should look": a single component enlarged, side-by-side dialogue, focus on the input area, workspace expanded, pure big type, a few cards in parallel. Not random transitions to manufacture a sense of busyness.

## Captions must sound like a person talking

In a narrated film the voice carries this explanation and the caption bar shows the spoken line; write those lines per [narration](narration.md) (one idea per line, 2.2–2.8 words per second) and keep the rules below for them too.

- Headlines can be short; small text must not be reduced to keywords.
- Small text should have a subject / action / result, so a first-time viewer knows what changed.
- Use words the product's users already know; do not explain build scripts, SSR or technical adapters in a promo video.
- Feature names match the real UI; do not replace them with unprovable vague buzzwords like "smarter, smoother, freer".

Examples:

| Too terse | Clearer |
| --- | --- |
| Context keeps up. | After you switch models, the previous conversation comes along, so you can keep working. |
| Preview and browse, right beside you. | Open web pages in the built-in browser and check how your project looks at any time. |
| Task notifications. Less waiting around. | You get a notification when a task finishes, so you don't have to keep watching the chat window. |
| CLI maintenance. | Check the CLI status in Settings and update it directly when needed. |

These sentences are only examples of how CodePilot's copy was written; do not apply them to products that lack these features.

## Headline and caption roles

Every shot has a short headline and one clear caption sentence, both in the film language (`typography.language`, chosen by the user; English by default). The headline carries the hook and the typographic rhythm and names the capability / action; the caption explains so people understand directly. In `bilingual` mode a short English headline sits above the film-language caption, which is how the original Chinese films were made; it is an option for non-English films, not the default.

- Headlines and body text share one type system per language, with weight / size separating levels. CJK text (Chinese, Japanese, Korean) stays sans-serif throughout.
- The headline gets its own span and font (`typography.headlineFont`, `--film-font-headline`); the caption gets its own span and font (`typography.captionFont`, `--film-font-caption`). The headline can use a serif with character while the caption uses a clean sans-serif, or pick two suitable sans-serifs per the brand. **Assign a font to each role explicitly; do not let font fallback hand out glyphs at random.** For CJK captions under an English headline, the two fonts must differ.
- The main title card can use a big headline + a medium caption; component pages can place the short headline above the caption, still prominent enough. Not every small button gets a headline treatment, and nothing inside the product UI is re-typeset.
- The headline must fit the feature; do not mechanically compress the caption into it, and do not force in unrelated slogans for the sake of layout. The caption must stand on its own even for a viewer who skips the headline.
- Font choice comes from the product's design or available licensed fonts; system fonts are for technical previews only. The production project freezes font assets and checks the actual glyphs. A CSS font name alone does not prove the font loaded.

| Headline | Caption (use only when the feature really exists) | French equivalent (same structure in any language) |
| --- | --- | --- |
| Switch models, keep talking | After you switch models, the previous conversation comes along; no need to explain everything again. | Changez de modèle, gardez le fil : la conversation précédente vous suit, inutile de tout réexpliquer. |
| Web pages open right beside you | Open web pages inside the app and read them while you keep chatting. | Les pages web s'ouvrent dans l'application, et vous les lisez sans quitter la conversation. |
| When it's done, you'll be told | A notification pops up when the task finishes, so you can go do something else first. | Une notification s'affiche quand la tâche est terminée ; vous pouvez faire autre chose en attendant. |

Do not keep reusing these three sets as a fixed template for every product; check the facts first, then rewrite. When the user explicitly asks for a different language mix or specific fonts, respect the choice and record their words / the basis in `typography.exceptionReason`.

## Copy read-through: a full stop does not rule out empty phrases

Run per feature and write to `evidence/copy-review.md`:

1. Write the plain-language fact first: "what you had to do before, how you do it now, how the result differs." Only write the parts that have a source; if the previous behavior is unknown, do not invent a comparison.
2. Distill the headline from it, then write the explanation. The explanation must state **the object acted on + the action + the observable result**, adding the use case where needed; the length is whatever it takes to be clear.
3. Cover the screenshot and the headline, and read only the caption aloud to someone who has never used the product. If they still have to ask "what got connected? where do I see it? what happens?", rewrite.
4. Check whether headline and explanation merely repeat each other; the explanation should add the action or the result, not praise the product again.
5. Read it aloud in a natural conversational tone, then check the subtitle display time. Do not substitute "enough characters" or "it has a full stop" for a content check.

More counter-examples:

| Fails | Why it is unclear | Say this instead (assuming the feature is real) |
| --- | --- | --- |
| Let your workflow flow naturally. | Does not say which action changed | After you submit changes, you can see the check results in the same window. |
| From idea to shipping, in one go. | All-purpose praise, no information | Write down what you need, the AI generates the code, and you can preview the changed page directly. |
| Results, within reach. | What "results" are and where to see them is unclear | When a task finishes, click the notification to return to the matching conversation. |

`plainExplanation` holds the plain-language explanation written from facts; `description` is the final on-screen text. The two may be identical; never re-compress a concrete explanation into an abstract phrase for the sake of "sophistication". Scripts can only catch missing fields / some suspicious wording; whether the meaning is clear still needs the read-through above.

## Action, hold and music

- Enter / select / switch actions usually take 0.25–0.6 s; give each action a clear start and end.
- Each shot generally runs "establish the frame → core action → readable result → cut away". Do not float every element in together and then sit still for 5 seconds.
- Show the explanation text early so reading time overlaps with the component demo. Do not fix long sentences by shrinking the type; first cut filler words, split sentences or add hold.
- Roughly 2–3 words per second (6–9 characters per second for CJK text) is a rough warning line; `check_delivery.py` applies the same thresholds from `typography.language`. Leave extra margin when the UI is changing in complex ways at the same time; this is a starting point for human reading, not a pass threshold.
- Start arranging from 110–125 BPM; a beat is about `60 / BPM` seconds. Main actions land on the downbeat, small actions offset by half a beat. Do not hard-quantize every clip to the same length.
- Blank or fully still frames are not automatically wrong: short pauses serve emphasis / reading. Watch out for long holds with no information; do not add meaningless wobble just to defeat stillness detection.
- The ending needs a complete end card and a sound resolution. Without a website link, the product name / logo and one closing line is enough.

## Reviewing stills

Capture representative shots from the real code and lay them out as one contact sheet in playback order. Check whether the frame scale changes, whether the hierarchy is obvious at a glance, whether the explanation is still readable when shrunk to phone width, and whether a caption leaves a lone word, character or punctuation mark orphaned on the next line. Passing stills only proves the layout direction; pacing, action continuity and sound still need the final film, see [review](review.md).
