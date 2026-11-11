"""Offline test of first-install, reuse and failure for CPU music analyzer.

Does not download model weights or install packages during CI.
"""
import importlib.util
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('music_analyzer_setup',ROOT/'tools/install_music_structure.py')
setup=importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class MusicInstallerTests(unittest.TestCase):
    def test_installs_analyzer_isolated_once_and_reuses_pinned_environment(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            venv=root/'music'
            interpreter=setup.interpreter(venv)
            calls=[]
            def run(args,**kwargs):
                cmd=[str(v) for v in args]
                calls.append(cmd)
                if cmd[1:3]==['-m','venv']:
                    interpreter.parent.mkdir(parents=True,exist_ok=True)
                    interpreter.touch()
                if len(cmd)>2 and cmd[1]=='-c' and 'print(torch.__version__)' in cmd[2]:
                    return types.SimpleNamespace(returncode=0,stdout='2.9.0+cu130\n',stderr='')
                return types.SimpleNamespace(returncode=0,stdout=b'',stderr=b'')
            with patch.object(setup.subprocess,'run',side_effect=run):
                first=setup.install('/any/working/python',venv)
                self.assertEqual(first,str(interpreter))
                self.assertEqual((venv/'banana_music_revision.txt').read_text().strip(),setup.REVISION)
                self.assertEqual((venv/'torch-constraint.txt').read_text(),'torch==2.9.0+cu130\n')
                install=[c for c in calls if 'all-in-one-infer @ git+' in ' '.join(c)]
                self.assertEqual(len(install),1)
                self.assertIn('@'+setup.REVISION,install[0][-1])
                self.assertFalse(any('download.pytorch.org' in ' '.join(c) for c in calls))
                before=len(calls)
                self.assertEqual(setup.install('/any/working/python',venv),str(interpreter))
                self.assertEqual(len(calls),before+1)  # import probe only
                self.assertFalse(any(c[0].endswith('python.exe') and 'pip' in c
                                     for c in calls[before:]))

    def test_installs_cpu_torch_when_isolated_venv_has_no_usable_torch(self):
        with tempfile.TemporaryDirectory() as temp:
            venv=Path(temp)/'music'
            interpreter=setup.interpreter(venv)
            calls=[]
            def run(args,**kwargs):
                cmd=[str(a) for a in args];calls.append(cmd)
                if len(cmd)>2 and cmd[1:3]==['-m','venv']:
                    interpreter.parent.mkdir(parents=True,exist_ok=True);interpreter.touch()
                if len(cmd)>2 and cmd[1]=='-c' and 'import torch; print(torch.__version__)' in cmd[2]:
                    return types.SimpleNamespace(returncode=0,stdout='2.10.0+cpu\n',stderr='')
                if len(cmd)>2 and cmd[1]=='-c' and cmd[2]=='import torch':
                    return types.SimpleNamespace(returncode=1)
                return types.SimpleNamespace(returncode=0)
            with patch.object(setup.subprocess,'run',side_effect=run):
                setup.install('/working/python',venv)
            self.assertTrue(any('https://download.pytorch.org/whl/cpu' in c for c in calls))
            self.assertFalse(any('--index-url' in c and 'cu130' in c for c in calls))

    def test_failure_is_visible_and_does_not_mark_incomplete_install_ready(self):
        with tempfile.TemporaryDirectory() as temp:
            venv=Path(temp)/'music'
            interpreter=setup.interpreter(venv)
            def run(args,**kwargs):
                cmd=[str(a) for a in args]
                if len(cmd)>2 and cmd[1:3]==['-m','venv']:
                    interpreter.parent.mkdir(parents=True,exist_ok=True);interpreter.touch()
                if len(cmd)>2 and cmd[1]=='-c' and 'print(torch.__version__)' in cmd[2]:
                    return types.SimpleNamespace(returncode=0,stdout='2.9.0+cu130\n',stderr='')
                if 'all-in-one-infer @ git+' in ' '.join(cmd):
                    kwargs['stdout'].write('ERROR: test dependency failure\n')
                    return types.SimpleNamespace(returncode=1)
                return types.SimpleNamespace(returncode=0)
            with patch.object(setup.subprocess,'run',side_effect=run):
                with self.assertRaisesRegex(RuntimeError,'test dependency failure'):
                    setup.install('/working/python',venv)
            self.assertFalse((venv/'banana_music_revision.txt').exists())
            self.assertIn('ERROR', (Path(temp)/'music_structure_install.log').read_text())

    def test_windows_launcher_provisions_and_exports_selected_interpreter(self):
        launcher=(ROOT/'tools/start_fusion_local.ps1').read_text(encoding='utf-8')
        standalone=(ROOT/'tools/install_music_analyzer.ps1').read_text(encoding='utf-8')
        self.assertIn('install_music_analyzer.ps1',launcher)
        self.assertIn('$env:BANANA_MUSIC_PYTHON',launcher)
        self.assertIn('install_music_structure.py',standalone)
        self.assertIn('music-venv',standalone)
        self.assertNotIn('CUDA_VISIBLE_DEVICES',standalone)

    def test_windows_error_prompts_install_instead_of_switching_off_analyzer(self):
        from banana_mv import music_structure
        with tempfile.TemporaryDirectory() as tmp:
            missing=Path(tmp)/'missing.exe'
            source=Path(tmp)/'song.wav';source.touch()
            with patch.object(music_structure,'source_hash',return_value='x'), \
                 patch.dict(os.environ,{'BANANA_MUSIC_PYTHON':str(missing)}):
                with self.assertRaisesRegex(RuntimeError,'install_music_analyzer.ps1'):
                    music_structure.load_structure(source,Path(tmp)/'cache.json',12.5)


if __name__=='__main__':
    unittest.main()
