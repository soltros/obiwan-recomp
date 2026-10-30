#!/usr/bin/env python3
"""Hash-pinned, isolated Obi-Wan analysis and C generation. Run inside nix develop."""
import argparse,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SDK=Path(os.environ.get('XBOXRECOMP_DIR', ROOT.parent/'xbox-linux/third_party/xboxrecomp'))
WORK=ROOT/'build/obiwan-analysis'
GEN=ROOT/'src/recomp/gen'
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--game-dir',type=Path,help='path to the legally obtained extracted game directory')
    args=ap.parse_args()
    import capstone
    target=json.loads((ROOT/'target.json').read_text())
    pin=json.loads((ROOT/'toolchain.json').read_text())['xboxrecomp']['revision']
    head=subprocess.check_output(['git','-C',str(SDK),'rev-parse','HEAD'],text=True).strip()
    if head!=pin:raise RuntimeError('framework revision does not match toolchain.json')
    source=(args.game_dir if args.game_dir else ROOT.parent/target['directory'])/target['executable']
    if hashlib.sha256(source.read_bytes()).hexdigest()!=target['sha256']:raise RuntimeError('unexpected XBE hash')
    WORK.mkdir(parents=True,exist_ok=True);GEN.mkdir(parents=True,exist_ok=True)
    xbe=WORK/'default.xbe';shutil.copyfile(source,xbe)
    dis=WORK/'disasm';ids=WORK/'func-id';abi=WORK/'abi'
    jobs=[('parse',['tools.xbe_parser',str(xbe),'--quiet','--json',str(WORK/'default_analysis.json')]),
          ('disasm',['tools.disasm',str(xbe),'--text-only','--extra-sections','D3D,D3DX,XGRPH,DSOUND,XPP','-o',str(dis)]),
          ('identify',['tools.func_id',str(xbe),'--functions',str(dis/'functions.json'),'--strings',str(dis/'strings.json'),'--xrefs',str(dis/'xrefs.json'),'--output',str(ids)]),
          ('abi',['tools.abi_analysis',str(xbe),'--disasm-dir',str(dis),'--func-id-dir',str(ids),'--output-dir',str(abi)]),
          ('generate',['tools.recomp',str(xbe),'--all','--split','100','--disasm-dir',str(dis),'--func-id-dir',str(ids),'--abi-dir',str(abi),'--gen-dir',str(GEN)])]
    report={'framework_revision':head,'xbe_sha256':target['sha256'],'python':sys.version,'capstone':capstone.__version__,'stages':[],'section_policy':'.text plus D3D,D3DX,XGRPH,DSOUND,XPP; data/image sections and DOLBY excluded from initial CPU discovery; revisit if execution reaches an excluded address.'}
    for name,args in jobs:
        start=time.monotonic();log=WORK/(name+'.log');cmd=[sys.executable,'-m',*args]
        print(f'{name}: running; log {log}',flush=True)
        with log.open('w') as f:r=subprocess.run(cmd,cwd=SDK,stdout=f,stderr=subprocess.STDOUT)
        report['stages'].append({'stage':name,'command':cmd,'returncode':r.returncode,'seconds':round(time.monotonic()-start,2)})
        (WORK/'pipeline.json').write_text(json.dumps(report,indent=2)+'\n')
        if r.returncode:
            print(log.read_text()[-5000:]);return r.returncode
        print(f'{name}: finished in {report["stages"][-1]["seconds"]} seconds',flush=True)
    subprocess.run([sys.executable, str(ROOT/'tools/make_obiwan_entry_stub.py')], check=True)
    return 0
if __name__=='__main__':sys.exit(main())
