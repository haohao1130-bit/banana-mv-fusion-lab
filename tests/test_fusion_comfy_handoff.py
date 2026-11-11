"""Regression checks for the proven local ComfyUI handoff.

Python mocks cannot assert what actually runs on the user's Windows PC.
Windows Actions separately parses every PowerShell launcher.
"""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class ReuseWorkingComfyTests(unittest.TestCase):
    def test_fusion_reuses_live_classic_vnext_t8_not_second_comfy(self):
        source=(ROOT/'tools/start_fusion_local.ps1').read_text(encoding='utf-8')
        self.assertIn("BananaMVVNext\\config.json",source)
        self.assertIn("BananaMVClassic\\config.json",source)
        self.assertIn("comfy_input_dir",source)
        self.assertIn("MiniMaxH3AudioConditioningT8",source)
        self.assertIn("TextGenerate",source)
        self.assertIn("Invoke-RestMethod",source)
        self.assertIn("No verified working H3/T8 ComfyUI",source)
        self.assertIn("InputDir",source)
        self.assertIn("-ComfyUrl",source)
        self.assertNotIn("Start-Process -FilePath $python",source)
        self.assertNotIn("Comfy-Desktop\\ComfyUI-Installs",source)

    def test_comfy_is_checked_before_installing_music_ears(self):
        source=(ROOT/'tools/start_fusion_local.ps1').read_text(encoding='utf-8')
        self.assertLess(source.index('Verified T8 node:'),
                        source.index('install_music_analyzer.ps1'))
        self.assertIn("$config | Add-Member -NotePropertyName 'comfy_input_dir' -NotePropertyValue $comfyInputDir",source)

    def test_video_workflow_uses_pinned_t8_node_id(self):
        from banana_mv.core import build_workflow
        graph=build_workflow('image.png','song.wav',640,384,360,'',42)
        self.assertEqual(graph['7']['class_type'],'MiniMaxH3AudioConditioningT8')


if __name__=='__main__':
    unittest.main()
