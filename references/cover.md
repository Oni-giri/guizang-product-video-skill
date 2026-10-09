# Cover: 3:4, 4:3, 16:9

Make covers when the user is about to publish the film, or explicitly asks for one; otherwise, ask in one sentence at delivery. The cover is an extension of the film: its visual language comes from this film's `DIRECTION.md`, not from a generic template. The cover of a dark stage film and the cover of a light editor film should be recognizably different at a glance.

## Three aspect ratios

| Ratio | Design size (CSS px, exported at 2x) | Common use | Layout approach |
|---|---|---|---|
| 3:4 | 1080×1440 | Vertical feeds such as Xiaohongshu (RED) and WeChat Moments | Stacked vertically: title on top, main image in the middle, tags and byline at the bottom |
| 4:3 | 1440×1080 | X / Threads / WeChat official account images | Two columns: roughly the left 40% for title and tags, main image on the right |
| 16:9 | 1920×1080 | Video platform thumbnails, Bilibili, YouTube | Main image dominates, title larger with fewer words; avoid the duration badge at bottom right and the progress bar area at the bottom |

## Method

1. **Pick the frames.** Look at the whole film on a contact sheet first, then choose 1 main image and 0–2 supporting images. Use only frames actually rendered from this film: `node stills.mjs cover/frames <moments…>` outputs PNGs, which are sharper than frames extracted from the MP4.
   - The main image must still read when shrunk: large shapes, a clear product UI, a recognizable moment (for example the provider orbit in the CodePilot film, or the instant the cursor draws the logo in the Zed film).
   - A frame that is mostly pure black or pure white looks like a blank board as a supporting image; replace it.
2. **Set the copy.**
   - Main title: the user's own post wording comes first; otherwise take the film's core claim. A Chinese main title stays under about 12 characters (keep English titles equally short), optionally with one short English line.
   - One subtitle sentence. At most 4 tags.
   - A claim is either the user's own opinion in the user's own words, or has a source in the repository. Comparisons with other products go on the cover only when the user wrote them, and keep the user's exact wording.
3. **Set the design.** Background color, fonts and motifs follow the film's frame system directly: if the film's titles are code comments, the cover title can be a comment line too; if the film uses a glowing horizon, the cover can too. The three ratios share one set of elements and only re-lay them out; proportional scaling is not enough.
4. **Lay out and export.** In the video project, write `cover/cover.html` with one element per ratio, marked `data-cover="3x4"`, `"4x3"` or `"16x9"`, sized per the table above. Reference fonts and images by relative path (for example `../public/fonts/…`, `frames/…`). Then run:

   ```sh
   node cover.mjs            # outputs covers/cover-3x4.png etc., at 2x pixels
   ```

   The script verifies each element's size and fails outright on page errors or failed asset loads.
5. **Thumbnail test.** Shrink each cover to 320px wide and look again: is the title still readable? Is the main image still recognizable? In feeds, 3:4 and 4:3 often appear only at this size.

## Common problems

| Symptom | Fix |
|---|---|
| The supporting image is almost completely hidden behind the main image | Move the supporting image outward so at least one third shows, and the visible part has content |
| Title overlaps the main image | Separate the title area from the image area, or give the title a backing color; never let the title sit on UI text |
| Title too small in 16:9 | At thumbnail size the title height is at least 1/8 of the frame height; halve the word count |
| The three ratios look like the same image scaled | Re-lay each out per its own layout approach; the main image's size and position must both change |
| Spaces lost in code/monospace text (`fnname`, `1//`) | The line container used `display:flex`, which drops whitespace-only text nodes; make lines plain block elements with `white-space:pre` |
| Fonts not loaded (fell back to system fonts) | Check the relative paths in `@font-face`; `cover.mjs` waits for `document.fonts.ready` |

Do not make covers disguised as platform UI (fake view counts, fake platform buttons, other people's branding). A play icon on a cover may only be a neutral shape.
