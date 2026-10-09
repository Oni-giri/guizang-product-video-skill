#!/usr/bin/env python3
"""Initialize an isolated promo workspace without installing dependencies or touching the repo."""
import argparse
import json
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--style', required=True, choices=['repo', 'default', 'hybrid'])
    parser.add_argument('--repo', type=Path)
    parser.add_argument('--language', default='en', help='film language as a BCP-47 tag (en, fr, de, zh, ja, ...); captions and headlines are written in it')
    parser.add_argument('--bilingual', action='store_true', help='add a short English headline span above each film-language headline (the original Chinese films used this)')
    parser.add_argument('--narration', nargs='?', const='edge', metavar='ENGINE', help='add a narration block (one line per shot, captions on) for scripts/narrate.py; engine: edge | openai | elevenlabs | piper | say | file')
    args = parser.parse_args()
    language = args.language.strip() or 'en'
    cjk = language.lower().split('-')[0] in ('zh', 'ja', 'ko')
    bilingual = args.bilingual and language.lower().split('-')[0] != 'en'
    repo = args.repo.expanduser().resolve() if args.repo else None
    target = args.output.expanduser().resolve()
    if args.style in ('repo', 'hybrid') and (repo is None or not repo.is_dir()):
        parser.error('repo/hybrid requires --repo pointing to an existing repository')
    if repo is not None and not repo.is_dir():
        parser.error('--repo must be a directory')
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        parser.error('output must be absent or empty; existing work is never overwritten')
    skill = Path(__file__).resolve().parents[1]
    if target == skill or skill in target.parents:
        parser.error('output must be outside the skill bundle')
    target.mkdir(parents=True, exist_ok=True)
    shutil.copytree(skill / 'assets/starter', target, dirs_exist_ok=True)
    for name in ['assets', 'evidence', 'renders', 'public']:
        (target/name).mkdir(exist_ok=True)
    if args.style != 'repo':
        shutil.copytree(skill/'assets/fallback', target/'assets/fallback')
        (target/'src/presentations.jsx').write_text("""import React from 'react';
import {CardFrame, CardSurface, FilmButton, FilmBadge} from '../assets/fallback/primitives.jsx';
// Technical fixture using the adapted fallback primitives, not product business components.
export function FeatureVisual() {
  return <CardFrame data-skill-placeholder="true"><CardSurface style={{padding:54}}>
    <FilmBadge>COMPONENT SHOWCASE / DEMO</FilmBadge>
    <h2>Components plug straight in.</h2>
    <p>Wire in the real product components, then choreograph selection, expansion and switching.</p>
    <div style={{display:'flex',gap:16,marginTop:42,fontSize:26}}>
      <FilmButton>Primary action</FilmButton><FilmButton variant="secondary">Secondary action</FilmButton>
    </div>
  </CardSurface></CardFrame>;
}
""")
    shots = [
        {'id':'intro','start':0,'end':3,'type':'title','headlineEn':"What's new",'headline':'What does this update bring?','description':'Say what changed in one sentence, then show it.'},
        {'id':'component','start':3,'end':7,'type':'detail','headlineEn':'Real components','headline':'Use the components from the product itself','description':"Wire in the repository's buttons and cards, then choreograph them with code.",'component':'src/presentations.jsx'},
        {'id':'close','start':7,'end':10,'type':'end','headlineEn':'Ready to share','headline':'Check picture and sound together','description':'Check captions read and actions sound, then export.'},
    ]
    for shot in shots:
        if not bilingual: shot.pop('headlineEn')   # monolingual films carry one headline, in the film language
        shot.update({'descriptionAt':0,'claim':False,'source':[], 'plainExplanation':shot['description'],
                     'actions':[{'id':shot['id']+'-enter','at':0,'action':'copy enters','soundRequired':False}]})
        shot.setdefault('component', None)
    shots[1]['actions'].append({'id':'component-appear','at':0.45,'action':'controls appear','soundRequired':True})
    shots[2]['actions'][0]['soundRequired']=True
    typography = {'language':language,'mode':'bilingual' if bilingual else 'monolingual',
                  'headlineFont':'Georgia','captionFont':'PingFang SC / Noto Sans CJK SC' if cjk else 'Inter / system-ui'}
    if cjk: typography['cjkStyle'] = 'sans-serif'
    plan = {'demo':True,'product':'Software update · technical sample','style':args.style,'width':1920,'height':1080,'fps':30,'duration':10,
            'repo':str(repo) if repo else None,'audioRequired':True,'sfxRequired':True,
            'typography':typography,
            'audio':{'ducking':{'enabled':True},'music':{'file':'assets/music.wav','gain':0.65},'cues':[
              {'at':3.45,'actionId':'component-appear','file':'assets/sfx/click.wav','gain':0.8,'role':'sfx','kind':'click'},
              {'at':7.0,'actionId':'close-enter','file':'assets/sfx/ding-dong.wav','gain':0.7,'role':'sfx','kind':'ding-dong'}]},
            'shots':shots}
    if args.narration:
        plan['narration'] = {'enabled':True,'language':language,'voice':{'engine':args.narration,'id':None,'speed':1.0},
                             'lead':0.35,'tail':0.6,'gap':0.3,'targetRms':-20,'duck':{'db':9,'attack':0.15,'release':0.6},'captions':True,
                             'lines':[{'id':s['id'],'shotId':s['id'],'text':s['description'],
                                       'intensity':'strong' if s['type']=='title' else ('soft' if s['type']=='end' else 'normal')} for s in shots]}
    (target/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
    (target/'BRIEF.md').write_text(f"""# Video brief

- Status: technical start; product research and storyboard not yet done.
- Style choice: {args.style} (should come from a choice the user has confirmed)
- Repository: {repo or 'not specified; add before producing real product content'}
- Product / update scope / release status: to be determined from user input and the repository.
- Language: {language}, {'bilingual (English headline + ' + language + ' caption)' if bilingual else 'monolingual'} (from --language / --bilingual; confirm with the user).
- Platform / aspect ratio / length: to be recorded; plan.json is currently only a 10-second technical sample.
- Brand assets / fonts: to be audited.
- Links / CTA allowed: user requirement to be recorded.
- Sound: music is code-original by default; for SFX, find samples that suit this film first and use the skill's built-in WAVs only for gaps. The technical sample has no soundtrack yet; the plan lists the score and key action SFX separately, and they must actually be prepared and mixed in.
- Narration: {('engine ' + args.narration + '; one line per shot in plan.narration.lines, captions on. Write the script per references/narration.md, then run scripts/narrate.py (--fit-shots lets the picture follow the voice).') if args.narration else 'none (add plan.narration and run scripts/narrate.py if the user wants a voice-over; see references/narration.md).'}
- Claim evidence, style audit and asset sources: recorded in evidence/.

Keep the user's existing decisions; never present unconfirmed fields as confirmed. Once the production film is finished, sync plan.json with the actual timeline.
""")
    (target/'DIRECTION.md').write_text('''# Film direction (complete before writing code; see references/direction.md)

> This file contains only questions, no answers. Derive every item from this product itself; do not copy the case study or the previous film.

## 1. Reference breakdown (only if the user supplied references)
| Device in the reference | What it expresses | Adopted in this film? How is it rewritten? |
|---|---|---|

## 2. Product character
- What the product does, who uses it, and what it feels like to use:
- Design language (palette, fonts, radii, light/dark theme) and its sources:
- Product elements that can become visual motifs (logo geometry, core UI, data shapes, domain metaphors):

## 3. Three directions (pulled apart along different axes)
| Direction | Base color and light | Type voice | Motif source | Camera language | Pacing | Music |
|---|---|---|---|---|---|---|
| A | | | | | | |
| B | | | | | | |
| C | | | | | | |

## 4. Choice and rationale
- Which one, and why it fits this product and audience:
- This film's specific devices (3–5; for each, say which part of the product it is derived from):
- How it differs from earlier films in this workspace (opening, transitions, background, score):

## 5. Frame system
- Aspect ratio / frame rate / base color / safe area:
- Type scale (headline, caption-language text, descriptions) and font sources; CJK text sans-serif:
- Product UI on-screen scale factor (body text ≥ 22px) and light/dark theme:
- Motion grammar (entrances, camera moves, easing, what is forbidden):

## 6. Shot list
| # | Time | Shot | Focal element | Picture and action | Copy | Sound |
|---|---|---|---|---|---|---|
''')
    print(json.dumps({'project':str(target),'style':args.style,'language':language,'mode':typography['mode'],'demo':True,'next':'Research the product, then write DIRECTION.md (references/direction.md) before production shots.'},ensure_ascii=False))

if __name__ == '__main__':
    main()
