"""Fusion V1 contract/state integration: offline 1+N handoff, not visual GPU proof."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from PIL import Image

from banana_mv.creative_contract import creative_contract, CONTRACT_POLICY
from banana_mv.fusion_state import compile_timeline, parse_event, fact_note, ending_note
from banana_mv.scene_state import SceneStateError
from banana_mv.core import segments
from banana_mv.mv_scope import ending_contract, clip_ending
from banana_mv.shoot_plan import ensure_shoot_plan, write_shoot_prompt


def four_clip_delivery():
    return ("""=== SETUP ===
<Picture 1> is adult singer S1, wardrobe starts with jacket, top and trousers.
<Picture 2> is adult champion S2; champion never sings. Two separate locations.
=== STORY OUTCOME ===
ONLY_THE_FINAL_INTERVAL_MAY_WIN_THE_FIGHT
=== CLIP 0 action ===
<Picture 1> begins the show and removes the jacket while the boxer makes the first exchange.
[[STATE S1.jacket:worn>removed]]
=== CLIP 1 action ===
<Picture 1> continues dancing and takes off the top; boxer counters a jab, fight ongoing.
[[STATE S1.top:worn>removed]]
=== CLIP 2 action ===
<Picture 1> removes trousers as stage lights change; boxer defends and remains standing.
[[STATE S1.trousers:worn>removed]]
=== CLIP 3 action ===
<Picture 2> lands the decisive punch; the referee declares the winner.
<Picture 1> performs a closing stage movement.
=== END ===""")


def native_prompt(index):
    return ('<Picture 1> performs the current staged interval. '
            '<Audio 1>: fully_copy. ' + 'Camera and staging follow the active scene. '*90)


class FusionV1Tests(unittest.TestCase):
    def test_ported_source_contract_extracts_parallel_and_duty(self):
        brief='舞台與拳場雙線交錯。拳王不演唱。主唱是唯一歌手。'
        extracted=creative_contract(brief)
        self.assertTrue(extracted['relationship_evidence'])
        self.assertTrue(extracted['explicit_constraints'])
        self.assertIn('No split-screen',CONTRACT_POLICY)

    def test_state_transitions_only_authorized_and_not_replayed(self):
        rows=[{'index':i,'event':t} for i,t in enumerate([
            'S1 removes coat. [[STATE S1.coat:worn>removed]]',
            'S1 removes top. [[STATE S1.top:worn>removed]]',
            'S1 removes trousers. [[STATE S1.trousers:worn>removed]]',
            'S1 continues performing, no new garment action.',
        ])]
        timeline=compile_timeline(rows)
        self.assertEqual(timeline[0]['fusion_state']['out']['S1.coat'],'removed')
        self.assertEqual(timeline[1]['fusion_state']['in']['S1.coat'],'removed')
        self.assertEqual(timeline[1]['fusion_state']['out']['S1.top'],'removed')
        self.assertEqual(timeline[2]['fusion_state']['in']['S1.trousers'],'worn')
        self.assertEqual(timeline[3]['fusion_state']['out'],
                         {'S1.coat':'removed','S1.top':'removed','S1.trousers':'removed'})
        self.assertEqual(timeline[3]['fusion_state']['changes'],[])
        self.assertNotIn('removes coat',timeline[1]['event'])
        self.assertIn('S1.coat=removed',fact_note(timeline[1]['fusion_state']))
        self.assertNotIn('STATE S1.top',timeline[1]['event'])

    def test_wrong_order_replay_and_unapproved_redress_are_rejected(self):
        with self.assertRaises(SceneStateError):
            compile_timeline([
                {'index':0,'event':'First removal [[STATE S1.coat:worn>removed]]'},
                {'index':1,'event':'Repeat old action [[STATE S1.coat:worn>removed]]'},
            ])
        with self.assertRaises(SceneStateError):
            parse_event('Unsupported leap [[STATE S1.coat:removed>unfastened]]')
        with self.assertRaises(SceneStateError):
            parse_event('Bad syntax [[STATE S1.coat:removed>>worn]]')
        restored=compile_timeline([
            {'index':0,'event':'Remove [[STATE S1.coat:worn>removed]]'},
            {'index':1,'event':'Explicitly redress [[STATE S1.coat:removed>worn]]'},
        ])
        self.assertEqual(restored[-1]['fusion_state']['out']['S1.coat'],'worn')
        self.assertEqual(restored[-1]['fusion_state']['changes'][0]['operation'],'dress')

    def test_short_tail_resolves_preceding_segment_not_late(self):
        req={'project_scope':'full','ending_policy_version':2}
        clips=segments(62,15)
        contract=ending_contract(req,62,clips)
        self.assertEqual(contract['short_tail_seconds'],2)
        prior=clip_ending(req,dict(clips[-2],song_seconds=62,segment_count=len(clips),
                                   direction_ending_contract=contract))
        last=clip_ending(req,dict(clips[-1],song_seconds=62,segment_count=len(clips),
                                  direction_ending_contract=contract))
        self.assertIn('Resolution interval',ending_note(prior))
        self.assertIn('Residual tail',ending_note(last))
        self.assertIn('no new knockout',ending_note(last))

    def test_one_allocation_and_four_native_writers_in_fusion_v3(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            images=[]
            for i in range(2):
                pic=root/f's{i}.png'
                Image.new('RGB',(12,12)).save(pic)
                images.append(pic)
            guide=root/'guide.md';guide.write_text('NATIVE_H3_GUIDE')
            cfg={'guides':{'ref':str(guide)}}
            clips=segments(60,15)
            req={'prompt':'Adult singer stage and boxer fight intercut. S2 never sings.',
                 'project_scope':'full','ending_policy_version':2,
                 'scene_state_version':3,'persistent_scene_state':True,
                 'story_plan':True,'director_schema':5,'director_version':2,
                 'intensity':'high','dynamic_cuts':True,
                 'director':'auto','rewrite_retries':0}
            allocator=Mock(return_value=four_clip_delivery())
            plan=ensure_shoot_plan(cfg,req,clips,images,root,allocator)
            self.assertEqual(allocator.call_count,1)
            self.assertEqual(plan['fusion_version'],3)
            self.assertIn('FUSION V1 PHYSICAL CONTINUITY',allocator.call_args.args[1])
            self.assertIn('No split-screen',allocator.call_args.args[1])
            self.assertNotIn('ONLY_THE_FINAL_INTERVAL_MAY_WIN_THE_FIGHT',plan['shared_setup'])
            writer=Mock(side_effect=[native_prompt(i) for i in range(4)])
            for i,seg in enumerate(clips):
                segment=dict(seg,director_plan=plan['segments'][i],
                             fixed_reference_settings=plan['shared_setup'],
                             direction_ending_contract=plan['ending_contract'],
                             song_seconds=60,segment_count=4)
                prompt=write_shoot_prompt(cfg,req,segment,images,None,writer)
                self.assertIn('<Audio 1>',prompt)
                text=writer.call_args.args[2][0][1]
                self.assertNotIn('ONLY_THE_FINAL_INTERVAL_MAY_WIN_THE_FIGHT',text)
                self.assertNotIn('[[STATE',text)
                self.assertIn('No split-screen',text)
                if i<3:
                    self.assertIn('Ongoing interval',text)
                    self.assertNotIn('decisive punch',text)
                    self.assertNotIn('winner.',text)
                else:
                    self.assertIn('Resolution interval',text)
                    self.assertIn('decisive punch',text)
            self.assertEqual(writer.call_count,4)
            self.assertEqual(allocator.call_count+writer.call_count,5)
            replay=ensure_shoot_plan(cfg,req,clips,images,root,allocator)
            self.assertEqual(replay,plan)
            self.assertEqual(allocator.call_count,1)


if __name__=='__main__':
    unittest.main()
