import React from 'react';
import {useFilmState} from '../film-store.js';
import {narration, typography} from '../engine.js';
// Caption bar for narrated films: shows the line being spoken, from just before the first word until
// shortly after the last one (or until the next line starts). Pure function of film time, so any frame
// renders the same on its own. Timing comes from plan.narration.lines as written by scripts/narrate.py.
// Restyle .caption-bar in film.css per film (position inside the safe area, font, backing); keep it legible at phone width.
const LEAD = 0.12, HANG = 0.45;

export function currentLine(t) {
  if (!narration || !Array.isArray(narration.lines)) return null;
  let current = null;
  for (const line of narration.lines) {
    if (typeof line.start !== 'number') continue;
    const on = line.start + (line.speechStart || 0);
    if (t >= on - LEAD) current = line;        // the latest line that has started wins
  }
  if (!current) return null;
  const off = current.start + (current.speechEnd ?? current.duration ?? 0);
  return t < off + HANG ? current : null;
}

export function CaptionBar() {
  const id = useFilmState(t => currentLine(t)?.id ?? null);
  const line = id ? narration.lines.find(l => l.id === id) : null;
  return <div className="caption-bar" lang={narration?.language || typography.language || 'en'} data-active={line ? 'true' : 'false'} aria-live="off">
    {line ? <span>{line.captionText || line.text}</span> : null}
  </div>;
}
