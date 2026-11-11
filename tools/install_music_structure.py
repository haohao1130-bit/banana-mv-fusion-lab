"""Install the optional music-structure 'ears' in an isolated environment.

Run on a Windows host with:
  python tools/install_music_structure.py --venv-dir <path>

The H3/9B Python environment and its CUDA wheels are never uninstalled or
upgraded. The analysis subprocess is CPU-only. A first analysis may fetch
model weights independently of this Python-package installation.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from banana_mv.music_structure import REVISION

REPO = 'https://github.com/openmirlab/all-in-one-infer.git'


def interpreter(venv):
    venv=Path(venv)
    return venv/('Scripts/python.exe' if os.name=='nt' else 'bin/python')


def probe(python):
    """Check that the entry environment imports the pinned model runtime."""
    if not Path(python).is_file():
        return False
    try:
        result=subprocess.run([str(python),'-c','import torch; import allin1_infer'],
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90)
    except (OSError,subprocess.TimeoutExpired):
        return False
    return result.returncode==0


def has_module(python, module):
    result=subprocess.run([str(python),'-c',f'import {module}'],
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90)
    return result.returncode==0


def call_logged(command, logfile, *, timeout=1800):
    with open(logfile,'a',encoding='utf-8') as log:
        log.write('\nCOMMAND: '+ ' '.join(map(str,command[:3]))+' ...\n')
        log.flush()
        result=subprocess.run([str(x) for x in command],
                              cwd=str(ROOT),stdout=log,stderr=subprocess.STDOUT,
                              timeout=timeout)
    if result.returncode:
        lines=Path(logfile).read_text(encoding='utf-8',errors='replace').splitlines()[-45:]
        raise RuntimeError('音樂結構分析器安裝失敗。請查看 '+str(logfile)+
                           '\n'+'\n'.join(lines))


def install(host_python, venv_dir, *, force=False):
    host_python=Path(host_python)
    venv_dir=Path(venv_dir)
    python=interpreter(venv_dir)
    stamp=venv_dir/'banana_music_revision.txt'
    logfile=venv_dir.parent/'music_structure_install.log'
    venv_dir.parent.mkdir(parents=True,exist_ok=True)
    if not force and stamp.is_file() and stamp.read_text(encoding='utf-8').strip()==REVISION and probe(python):
        print('✅ 音樂結構分析器已就緒：'+str(python))
        return str(python)
    if not python.is_file():
        print('建立獨立音樂分析環境（不修改 ComfyUI／9B 的 Python）。',flush=True)
        try:
            subprocess.run([str(host_python),'-m','venv','--system-site-packages',
                            str(venv_dir)],check=True,timeout=180)
        except (subprocess.CalledProcessError,OSError) as exc:
            raise RuntimeError('無法建立音樂結構 Python 環境。請檢查 Python venv 支援：'+str(exc)) from exc
    if not python.is_file():
        raise RuntimeError('音樂分析環境缺少 Python：'+str(python))
    if not has_module(python,'pip'):
        # A packaged Python may lack ensurepip; use host pip's documented
        # --python bootstrap instead of modifying global packages.
        print('為獨立分析環境補裝 pip。',flush=True)
        call_logged([str(host_python),'-m','pip','--python',str(python),
                     'install','--upgrade','pip'],logfile)
    if not has_module(python,'torch'):
        # Never install a second CUDA stack merely to analyze music on CPU.
        print('安裝獨立 CPU PyTorch（不影響 RTX 5070 的 CU130）。',flush=True)
        call_logged([str(python),'-m','pip','install','torch',
                     '--index-url','https://download.pytorch.org/whl/cpu'],logfile)
    result=subprocess.run([str(python),'-c','import torch; print(torch.__version__)'],
                          capture_output=True,text=True,timeout=90)
    if result.returncode:
        raise RuntimeError('分析器無法載入 PyTorch：'+result.stderr[-1200:])
    torch_version=result.stdout.strip().splitlines()[-1]
    constraints=venv_dir/'torch-constraint.txt'
    constraints.write_text('torch=='+torch_version+'\n',encoding='utf-8')
    print('安裝固定版 All-In-One 音樂結構分析器（CPU），詳細紀錄：'+str(logfile),flush=True)
    call_logged([str(python),'-m','pip','install','-c',str(constraints),
                 'all-in-one-infer @ git+'+REPO+'@'+REVISION],logfile)
    if not probe(python):
        raise RuntimeError('安裝器已結束但無法 import allin1_infer／torch；查看 '+str(logfile))
    stamp.write_text(REVISION+'\n',encoding='utf-8')
    print('✅ 音樂結構分析器就緒，CPU 分析可用。首次分析會另外下載原始模型權重。')
    return str(python)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--host-python',default=sys.executable)
    parser.add_argument('--venv-dir',required=True)
    parser.add_argument('--force',action='store_true')
    args=parser.parse_args()
    try:
        install(args.host_python,args.venv_dir,force=args.force)
    except (RuntimeError,subprocess.TimeoutExpired) as exc:
        print('❌ '+str(exc),file=sys.stderr)
        return 1
    return 0


if __name__=='__main__':
    raise SystemExit(main())
