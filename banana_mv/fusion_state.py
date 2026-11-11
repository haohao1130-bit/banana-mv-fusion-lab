"""Fusion V1: deterministic, planned (not visually verified) clip-level garment state.

The sole upstream allocator may attach compact [[STATE Subject.item:from>to]]
annotations to its ordinary CLIP prose. No extra model is involved; Python
validates and applies only explicitly assigned transitions. A missing annotation
is NOT evidence that the model performed a physical change.
"""
import re
from banana_mv.scene_state import GARMENT_EDGES, SceneStateError, STATUSES

VERSION = 3
TAG = re.compile(
    r'\[\[STATE\s+([\w\-]+)\.([\w\-]+)\s*:\s*([a-z_]+)\s*>\s*([a-z_]+)\s*\]\]',
    re.I | re.U,
)
ANY_TAG = re.compile(r'\[\[\s*STATE\b.*?\]\]', re.I | re.S)
ALLOCATION_RULES = """FUSION V1 PHYSICAL CONTINUITY — ZERO ADDITIONAL MODEL CALLS:
If an event explicitly changes a named actor's garment, annotate that event in its
own CLIP block with exactly one compact marker: [[STATE S1.jacket:worn>removed]].
S1 is a stable actor ID, jacket is a stable garment ID; keep both IDs unchanged
across every CLIP. Repeat a marker ONLY for a genuinely new transition, such as
[[STATE S1.jacket:removed>worn]] when the story explicitly puts it back on.
Place the marker AFTER the current event, not in SETUP or STORY OUTCOME.
Use statuses worn, unfastened, partially_removed, removed, held, placed.
A full removal goes to removed. The first marker declares that item's true
pre-change state; Python carries its state to every following interval.
Do not produce initial-state JSON, per-shot state tables, or future-event previews.
For a segment with no physical change, write no STATE marker. A location cut or
camera shot change does not alter wardrobe. Other event descriptions stay creative.
Do not invent a garment transition merely to demonstrate this syntax."""

def parse_event(script):
    """Return unmodified prose (minus annotations) and ordered transitions."""
    if not isinstance(script, str):
        raise SceneStateError('Fusion clip prose must be text.')
    changes=[]
    for match in ANY_TAG.finditer(script):
        item=TAG.fullmatch(match.group(0))
        if item is None:
            raise SceneStateError('Fusion STATE marker must look like [[STATE S1.jacket:worn>removed]].')
        subject,garment,before,after=item.groups()
        before,after=before.lower(),after.lower()
        if before not in STATUSES or after not in STATUSES:
            raise SceneStateError('Fusion garment STATE uses an unsupported status.')
        if after not in GARMENT_EDGES[before]:
            raise SceneStateError('Fusion garment STATE transition is not permitted.')
        changes.append({'item':subject+'.'+garment,'from':before,'to':after,
                        'operation':'dress' if after=='worn' else 'remove'})
    clean=ANY_TAG.sub('',script).strip()
    if not clean:
        raise SceneStateError('Fusion clip contains no filmable event after STATE annotations.')
    return clean,changes

def compile_timeline(rows):
    """Calculate snapshots from ONE allocation; reject out-of-order transitions.

    The first explicit from-status is the item's starting state throughout
    intervals preceding its first change. Unknown items are not invented.
    """
    parsed=[parse_event(row['event']) for row in rows]
    initial={}
    for _,changes in parsed:
        for change in changes:
            initial.setdefault(change['item'],change['from'])
    state=dict(initial)
    output=[]
    for row,(clean,changes) in zip(rows,parsed):
        opening=dict(state)
        for change in changes:
            item=change['item']
            if state[item]!=change['from']:
                raise SceneStateError(
                    'Fusion state conflict: '+item+' is '+state[item]+
                    ', cannot transition from '+change['from']+'.')
            state[item]=change['to']
        output.append({
            'index':row['index'],
            'event':clean,
            'fusion_state':{'version':VERSION,'in':opening,'out':dict(state),
                            'changes':changes,'visual_verified':False},
        })
    return output

def fact_note(state):
    """Give the local writer only achieved facts + authorized current changes."""
    if not state or state.get('version') != VERSION:
        return ''
    entering=state.get('in',{})
    changes=state.get('changes',[])
    facts=', '.join(k+'='+v for k,v in sorted(entering.items())) or 'unchanged; unspecified wardrobe'
    allowed=', '.join(row['item']+':'+row['from']+'>'+row['to'] for row in changes) or 'none'
    return ('[CURRENT PHYSICAL FACTS — PLANNED, NOT OBSERVED]\n'
            'At entry: '+facts+'.\n'
            'Only authorized changes THIS clip: '+allowed+'.\n'
            'Do not replay completed actions, restore old outfits or do future changes. '
            'Reference images anchor identity; entry state overrides initial clothing.\n')

def ending_note(contract):
    """Respect source-time ending including a <=3s terminal tail and excerpts."""
    phase=(contract or {}).get('phase')
    if phase=='continuing':
        return ('[STORY TIME LOCK] Ongoing interval: no unassigned final KO, winner '
                'declaration, awards or whole-story resolution. Do not jump ahead.\n')
    if phase=='terminal_hold':
        return ('[STORY TIME LOCK] Residual tail: sustain achieved consequences; '
                'no new KO or replay of victory unless explicitly timed here.\n')
    if phase=='resolving':
        return ('[STORY TIME LOCK] Resolution interval: film only this clip\'s '
                'assigned decisive action, at its source-audio time.\n')
    return ''
