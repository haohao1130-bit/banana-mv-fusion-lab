"""Fusion V2 — deterministic audio-to-brief scaffold, not an automatic story writer.

Everything here comes from preexisting decoded audio windows, optional fallible
structure predictions, user-supplied SRT and the existing source-time ending rule.
Do not infer verse/chorus, lyrics, instrumentation or story events from loudness.
"""
from banana_mv.lyrics_reference import excerpt
from banana_mv.mv_scope import clip_ending, ending_contract

VERSION = 2


def _music(evidence):
    if not evidence:
        return {'measured': False, 'note': 'No audio analysis; preserve source-song timing.'}
    level = evidence.get('relative_energy', 'unmeasured')
    change = evidence.get('energy_change_db', 0)
    slope = ('rising' if isinstance(change, (int, float)) and change >= 3 else
             'falling' if isinstance(change, (int, float)) and change <= -3 else 'stable')
    result = {'measured': level != 'unmeasured', 'relative_energy': level,
              'energy_trend': slope,
              'accent_candidates_s': evidence.get('transient_candidates_s', []),
              'quiet_intervals_s': evidence.get('quiet_intervals_s', [])}
    pulse = evidence.get('pulse_estimate')
    if pulse:
        result['estimated_pulse'] = pulse  # This is NOT a perfect beat grid.
    vocal = evidence.get('provided_vocal_stem_quiet_intervals_s')
    if vocal is not None:
        result['provided_vocal_stem_quiet_intervals_s'] = vocal
    structure = evidence.get('music_structure')
    if structure:
        result['predicted_structure'] = {
            'prediction': True,
            'sections': structure.get('sections', []),
            'downbeats_s': structure.get('downbeats_s', []),
            'bpm': structure.get('bpm'),
        }
    return result


def build_scaffold(req, segment, ending=None):
    """Make one source-time, clip-local filming envelope using facts Python owns.

    The actual dramatic events / allowed wardrobe transitions are still
    commissioned by the one upstream whole-film 9B writer.
    """
    contract = ending or clip_ending(req, segment)
    phase = contract.get('phase') or 'excerpt'
    if phase not in ('continuing', 'resolving', 'terminal_hold', 'excerpt'):
        phase = 'continuing'
    return {
        'version': VERSION,
        # The H3 shot clock is frame-quantized; source-song time may end
        # inside the last frame. Never promote padding to musical evidence.
        'source_interval_s': [round(segment['start'], 6),
                              round(min(segment['start']+segment['seconds'],
                                        segment.get('song_seconds', segment['start']+segment['seconds'])), 6)],
        'clip_duration_s': round(segment['seconds'], 6),
        'timed_lyrics': [
            {'start_s': row['clip_start'], 'end_s': row['clip_end'], 'text': row['text']}
            for row in excerpt(req, segment)
        ],  # Supplied SRT only; no speech recognition or invented timecodes.
        'music': _music(segment.get('audio_evidence', {})),
        'story_gate': {
            'phase': phase,
            'allow_full_resolution': phase == 'resolving' and contract.get('finish_work', False),
            'scope': contract.get('project_scope', req.get('project_scope', 'full')),
            'boundary_rule': (
                'Film only assigned local events and achieved consequences; no future full-work resolution.'
                if phase == 'continuing' else
                'Maintain the achieved result in this short tail, except explicitly source-timed events.'
                if phase == 'terminal_hold' else
                'Perform only locally assigned decisive events at source-audio times.'
                if phase == 'resolving' else
                'An excerpt may resolve a local event, but do not invent a full-film ending.'
            ),
        },
        # Creative freedom is stated once in the director system contract,
        # not repeated N times as scaffold token overhead.
    }


def build_all_scaffolds(req, segments):
    """Precompute from exact existing clip boundaries; never repartition the song."""
    if not segments:
        return []
    # Existing source duration is authoritative when the last image-frame
    # rounding extends a fractional last frame past the final decoded sample.
    total = segments[0].get('song_seconds', segments[-1]['start'] + segments[-1]['seconds'])
    ending = ending_contract(req, total, segments)
    result = []
    for segment in segments:
        local = dict(segment, song_seconds=total, segment_count=len(segments),
                     direction_ending_contract=ending)
        result.append(build_scaffold(req, local, clip_ending(req, local)))
    return result


def ensure_scaffolds(req, segments):
    """Use persisted envelopes on resume; fill only missing ones, once per work cycle."""
    if req.get('director_scaffold_version') != VERSION:
        return
    if all(seg.get('director_scaffold', {}).get('version') == VERSION for seg in segments):
        return
    built = build_all_scaffolds(req, segments)
    for seg, scaffold in zip(segments, built):
        # Do not rewrite frozen scopes on resume after the plan was approved.
        if seg.get('director_scaffold', {}).get('version') != VERSION:
            seg['director_scaffold'] = scaffold


def build_call_sheet(req, segment, row, *, current_event=None,
                     fixed_reference_settings='', opening_frame=None):
    """One filming commission; Python owns facts, the writer owns camerawork.

    A call sheet carries only the local allocated event, never the complete
    outcome or the full-script plan. Timed SRT was authored by the user, not
    transcribed from audio. Physical state is planned, not visually observed.
    """
    if req.get('director_scaffold_version') != VERSION:
        raise ValueError('Filming call sheets require Fusion scaffold version 2.')
    if row.get('handoff_version') != 1:
        raise ValueError('A call sheet requires a validated isolated clip assignment.')
    scaffold = segment.get('director_scaffold')
    if not isinstance(scaffold, dict) or scaffold.get('version') != VERSION:
        scaffold = build_scaffold(req, segment)
    state = row.get('fusion_state') or segment.get('fusion_state') or {}
    entry = dict(state.get('in', {}))
    changes = list(state.get('changes', []))
    ending = dict(state.get('out', entry))
    start_frame = int(segment.get('start_frame', round(segment['start'] * 24)))
    frames = int(segment.get('frames', round(segment['seconds'] * 24)))
    sheet = {
        'contract': 'FILMING_CALL_SHEET_V2',
        'segment_index': segment['index'],
        'frame_window_half_open': [start_frame, start_frame + frames],
        'source_window_s': scaffold['source_interval_s'],
        'clip_shot_clock_s': scaffold['clip_duration_s'],
        'primary_mode': row['mode'],
        'current_event_only': row['event'] if current_event is None else current_event,
        'physical_state': {
            'entry': entry, 'authorized_changes_this_clip': changes,
            'planned_exit': ending, 'visual_verified': False,
        },
        'source_audio': scaffold['music'],
        'user_supplied_srt_clip_local': scaffold['timed_lyrics'],
        'resolution_gate': scaffold['story_gate'],
        'adaptation': 'FREE' if req.get('story_plan', True) else 'FAITHFUL',
    }
    if fixed_reference_settings:
        sheet['fixed_reference_settings'] = fixed_reference_settings
    if opening_frame:
        sheet['opening_frame'] = opening_frame
    return sheet
