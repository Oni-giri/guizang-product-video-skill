import React from 'react';
import {useFilmState} from '../film-store.js';
import {narration, typography} from '../engine.js';
// Caption bar for narrated films: shows the line being spoken, from just before the first word until
// shortly after the last one (or until the next line starts). Pure function of film time, so any frame
// renders the same on its own. Timing comes from plan.narration.lines as written by scripts/narrate.py.
// Restyle .caption-bar in film.css per film (position inside the safe area, font, backing); keep it legible at phone width.
// stills.mjs --hide-captions sets window.__hideCaptions so a poster still can be captured without a caption.
const LEAD = 0.12, HANG = 0.45;

export function currentLine(t) {
  if (!narration || !Array.isArray(narration.lines)) return null;
  let current = null, currentOn = -Infinity;
  for (const line of narration.lines) {
    if (typeof line.start !== 'number') continue;
    const on = line.start + (line.speechStart || 0);
    if (t >= on - LEAD && on > currentOn) { current = line; currentOn = on; }   // the line that started most recently wins
  }
  if (!current) return null;
  const off = current.start + (current.speechEnd ?? current.duration ?? 0);
  return t < off + HANG ? current : null;
}

const untag = text => text.replace(/\[[^\]]*\]\s*/g, '').trim();   // inline delivery tags ([calm], [warmly]) are for the voice only
/** The sentence being spoken: paragraph-per-shot takes carry sentence onsets (line.sentences, from narrate.py). */
export function currentText(line, t) {
  if (!Array.isArray(line.sentences) || !line.sentences.length) return untag(line.captionText || line.text);
  let text = line.sentences[0].text;
  for (const s of line.sentences) if (t >= line.start + s.start - LEAD) text = s.text;
  return untag(text);
}

export function CaptionBar() {
  const text = useFilmState(t => {
    if (typeof window !== 'undefined' && window.__hideCaptions) return null;
    const line = currentLine(t);
    return line ? currentText(line, t) : null;
  });
  return <div className="caption-bar" lang={narration?.language || typography.language || 'en'} data-active={text ? 'true' : 'false'} aria-live="off">
    {text ? <span>{text}</span> : null}
  </div>;
}
