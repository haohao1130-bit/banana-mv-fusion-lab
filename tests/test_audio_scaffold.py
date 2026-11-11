"""Fusion V2: Python owns source time, provided SRT, audio evidence and ending gates.

Offline tests verify routing and call budget, not 5070 throughput or H3 visuals.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from PIL import Image

from banana_mv.core import segments
from banana_mv.director_scaffold import (
    VERSION, build_all_scaffolds, build_scaffold, ensure_scaffolds,
)
from banana_mv.lyrics_reference import normalize_references
from banana_mv.shoot_plan import ensure_shoot_plan, write_shoot_prompt
from test_fusion_v1 import four_clip_delivery, native_prompt


def with_audio_time(seconds, length=15):
    rows=segments(seconds,length)
    for seg in rows:
        seg.update(song_seconds=seconds,segment_count=len(rows))
    return rows


class AudioScaffoldV2Tests(unittest.TestCase):
    def test_python_owns_framed_585_song_and_long_overlapping_srt(self):
        req=normalize_references({
            'project_scope':'full','ending_policy_version':2,
            'director_scaffold_version':2,
            'srt_reference':('1\n00:00:10,000 --> 00:00:36,000\nlong sustained line'
                             '\n\n2\n00:00:45,000 --> 00:00:58,500\nclosing lyric'),
        },58.5)
        rows=with_audio_time(58.5)
        self.assertEqual([r['start'] for r in rows],[0,15,30,45])
        self.assertEqual([r['seconds'] for r in rows],[15,15,15,13.5])
        envelopes=build_all_scaffolds(req,rows)
        self.assertEqual(len(envelopes),4)
        self.assertEqual(envelopes[-1]['source_interval_s'],[45,58.5])
        self.assertEqual(envelopes[1]['timed_lyrics'],
                         [{'start_s':0,'end_s':15,'text':'long sustained line'}])
        self.assertEqual(envelopes[2]['timed_lyrics'],
                         [{'start_s':0,'end_s':6,'text':'long sustained line'}])
        self.assertEqual(envelopes[3]['timed_lyrics'],
                         [{'start_s':0,'end_s':13.5,'text':'closing lyric'}])
        self.assertEqual(envelopes[0]['story_gate']['phase'],'continuing')
        self.assertTrue(envelopes[-1]['story_gate']['allow_full_resolution'])
        # No inferred time for plain lyrics and no invented chorus identity.
        self.assertNotIn('predicted_structure',envelopes[0]['music'])

    def test_non_frame_multiple_song_ends_on_decoded_source_not_video_padding(self):
        rows=with_audio_time(58.51)
        envelopes=build_all_scaffolds(
            {'project_scope':'full','ending_policy_version':2,
             'director_scaffold_version':2},rows)
        self.assertEqual(envelopes[-1]['source_interval_s'][1],58.51)
        self.assertGreater(rows[-1]['start']+rows[-1]['seconds'],58.51)
        self.assertTrue(envelopes[-1]['story_gate']['allow_full_resolution'])

    def test_short_tail_resolution_belongs_to_previous_segment(self):
        rows=with_audio_time(62)
        req={'project_scope':'full','ending_policy_version':2,'director_scaffold_version':2}
        envelopes=build_all_scaffolds(req,rows)
        self.assertEqual([x['story_gate']['phase'] for x in envelopes],
                         ['continuing','continuing','continuing','resolving','terminal_hold'])
        self.assertEqual([x['story_gate']['allow_full_resolution'] for x in envelopes],
                         [False,False,False,True,False])
        self.assertEqual(envelopes[-1]['clip_duration_s'],2)
        self.assertIn('already',envelopes[-1]['story_gate']['boundary_rule'].replace('achieved','already achieved'))

    def test_excerpt_has_no_forced_full_film_finale(self):
        rows=with_audio_time(58.5)
        req={'project_scope':'excerpt','ending_policy_version':2,
             'director_scaffold_version':2}
        envelopes=build_all_scaffolds(req,rows)
        self.assertTrue(all(not e['story_gate']['allow_full_resolution'] for e in envelopes))
        self.assertTrue(all(e['story_gate']['phase']=='excerpt' for e in envelopes))

    def test_volume_is_not_automatically_a_chorus_or_lyric(self):
        seg=with_audio_time(60)[1]
        seg['audio_evidence']={'relative_energy':'high','energy_change_db':4.0,
                               'transient_candidates_s':[1.2,3.6],
                               'quiet_intervals_s':[]}
        env=build_scaffold({'project_scope':'full','director_scaffold_version':2},seg)
        self.assertEqual(env['music']['energy_trend'],'rising')
        self.assertEqual(env['music']['accent_candidates_s'],[1.2,3.6])
        self.assertNotIn('predicted_structure',env['music'])
        self.assertFalse(env['timed_lyrics'])
        seg['audio_evidence']['music_structure']={
            'bpm':133,'sections':[{'start_s':0,'end_s':15,'predicted_label':'chorus'}],
            'downbeats_s':[2,5],
        }
        predicted=build_scaffold({'project_scope':'full','director_scaffold_version':2},seg)
        self.assertTrue(predicted['music']['predicted_structure']['prediction'])
        self.assertEqual(predicted['music']['predicted_structure']['bpm'],133)

    def test_persisted_envelopes_are_not_rebuilt_on_resume(self):
        req={'project_scope':'full','ending_policy_version':2,'director_scaffold_version':2}
        rows=with_audio_time(60)
        ensure_scaffolds(req,rows)
        before=[s['director_scaffold'] for s in rows]
        ensure_scaffolds(req,rows)
        self.assertTrue(all(a is s['director_scaffold'] for a,s in zip(before,rows)))
        self.assertEqual(VERSION,2)

    def test_one_global_allocation_plus_four_local_writers_with_compact_scaffolds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            images=[]
            for i in range(2):
                pic=root/f'pic{i}.png'
                Image.new('RGB',(8,8)).save(pic)
                images.append(pic)
            guide=root/'h3.md';guide.write_text('OFFICIAL_NATIVE_H3_GUIDE')
            cfg={'guides':{'ref':str(guide)}}
            req={'prompt':'Adult singer on stage, champion in boxing arena. Intercut.',
                 'project_scope':'full','ending_policy_version':2,
                 'scene_state_version':3,'persistent_scene_state':True,
                 'director_scaffold_version':2,
                 'director_schema':5,'story_plan':True,'director_version':2,
                 'intensity':'high','dynamic_cuts':True,'director':'auto',
                 'rewrite_retries':0,'lyrics':'untimed whole-song context',
                 'srt_cues':[{'start':16,'end':19,'text':'timed second clip'}]}
            rows=with_audio_time(60)
            for seg in rows:
                seg['audio_evidence']={'relative_energy':'medium','energy_change_db':0,
                                       'transient_candidates_s':[], 'quiet_intervals_s':[]}
            allocator=Mock(return_value=four_clip_delivery())
            plan=ensure_shoot_plan(cfg,req,rows,images,root,allocator)
            self.assertEqual(allocator.call_count,1)
            allocation_task=json.loads(allocator.call_args.args[2][0][1])
            self.assertEqual(allocation_task['format'],'isolated_shoot_briefs_fusion_v2')
            self.assertEqual(len(allocation_task['timeline']),4)
            self.assertIn('scaffold',allocation_task['timeline'][1])
            self.assertNotIn('local_srt',allocation_task['timeline'][1])
            self.assertNotIn('audio_evidence',allocation_task['timeline'][1])
            self.assertEqual(allocation_task['timeline'][1]['scaffold']['timed_lyrics'][0]['text'],
                             'timed second clip')
            native=Mock(side_effect=[native_prompt(i) for i in range(4)])
            for i,seg in enumerate(rows):
                local=dict(seg,director_plan=plan['segments'][i],
                           fixed_reference_settings=plan['shared_setup'],
                           direction_ending_contract=plan['ending_contract'])
                result=write_shoot_prompt(cfg,req,local,images,None,native)
                self.assertIn('fully_copy',result)
                system,parts=native.call_args.args[1:3]
                self.assertIn('OFFICIAL_NATIVE_H3_GUIDE',system)  # no guide removal
                prompt=parts[0][1]
                self.assertNotIn('ONLY_THE_FINAL_INTERVAL_MAY_WIN_THE_FIGHT',prompt)
                self.assertIn('FILMING CALL SHEET JSON (input only):',prompt)
                sheet=json.loads(prompt.split('FILMING CALL SHEET JSON (input only):\n',1)[1])
                self.assertEqual(sheet['contract'],'FILMING_CALL_SHEET_V2')
                self.assertEqual(sheet['segment_index'],i)
                self.assertEqual(sheet['frame_window_half_open'],[i*360,(i+1)*360])
                self.assertNotIn('audio_evidence',sheet)
                self.assertNotIn('local_srt',sheet)
                self.assertEqual(sheet['source_window_s'],[i*15,(i+1)*15])
                self.assertNotIn('Current clip script:',prompt)
                self.assertEqual(prompt.count('FILMING CALL SHEET JSON'),1)
                self.assertIn('SIX native sections',prompt)
                self.assertIn('source_audio',sheet)
                self.assertFalse(sheet['physical_state']['visual_verified'])
                self.assertIn('<Picture',sheet['fixed_reference_settings'])
                if i==1:
                    self.assertEqual(sheet['physical_state']['entry']['S1.jacket'],'removed')
                    self.assertEqual(sheet['physical_state']['authorized_changes_this_clip'][0]['item'],'S1.top')
                    self.assertEqual(sheet['user_supplied_srt_clip_local'][0],
                                     {'start_s':1,'end_s':4,'text':'timed second clip'})
                if i<3:
                    self.assertFalse(sheet['resolution_gate']['allow_full_resolution'])
                    self.assertNotIn('decisive punch',prompt)
                else:
                    self.assertTrue(sheet['resolution_gate']['allow_full_resolution'])
                    self.assertIn('decisive punch',sheet['current_event_only'])
            self.assertEqual(native.call_count,4)
            self.assertEqual(allocator.call_count+native.call_count,5)
            cached=ensure_shoot_plan(cfg,req,rows,images,root,allocator)
            self.assertEqual(cached,plan)
            self.assertEqual(allocator.call_count,1)


if __name__=='__main__':
    unittest.main()
