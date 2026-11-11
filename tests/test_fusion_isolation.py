"""Ensure Fusion Lab launch paths and notebook don't accidentally point at production."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class FusionIsolationTests(unittest.TestCase):
    def test_colab_entrypoint_targets_fusion_repository_and_data(self):
        text=(ROOT/'BANANAMV_FUSION_LAB.ipynb').read_text(encoding='utf-8')
        self.assertIn('banana-mv-fusion-lab.git',text)
        self.assertIn('MyDrive/BananaMVFusionLab',text)
        self.assertNotIn('banana-mv-public.git',text)
        self.assertNotIn('/content/banana-mv-public',text)

    def test_colab_runtime_separates_drive_data(self):
        text=(ROOT/'tools/colab_runtime.py').read_text(encoding='utf-8')
        self.assertIn('MyDrive/BananaMVFusionLab',text)
        self.assertNotIn("MyDrive/BananaMV')",text)

    def test_windows_launcher_has_independent_port_and_data(self):
        text=(ROOT/'tools/start_fusion_local.ps1').read_text(encoding='utf-8')
        self.assertIn('$Port = 8192',text)
        self.assertIn("BananaMVFusionLab",text)

if __name__=='__main__':
    unittest.main()
