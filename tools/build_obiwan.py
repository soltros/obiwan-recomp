#!/usr/bin/env python3
"""Build the launcher; optionally reuse resolved dependency locations from the runtime build."""
import argparse,json,os,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--reuse-runtime-cache',action='store_true');ap.add_argument('--jobs',type=int,default=4);a=ap.parse_args()
    env=os.environ.copy();args=[];cmake=shutil.which('cmake')
    if a.reuse_runtime_cache:
        cache={}
        for line in (ROOT/'build/runtime/CMakeCache.txt').read_text().splitlines():
            if line and not line.startswith(('#','//')) and '=' in line:
                key,val=line.split('=',1);cache[key.split(':',1)[0]]=val
        cmake=cache['CMAKE_COMMAND']
        for key in ['CMAKE_C_COMPILER','CMAKE_MAKE_PROGRAM','PKG_CONFIG_EXECUTABLE','SDL2_DIR','OPENSSL_INCLUDE_DIR','OPENSSL_CRYPTO_LIBRARY','OPENSSL_SSL_LIBRARY']:
            if cache.get(key):args.append('-D'+key+'='+cache[key])
        # Reuse only dependency locations, never source/build directory cache entries.
        roots=[Path(cache[k]).parent for k in ['EPOXY_INCLUDEDIR','OPENSSL_INCLUDE_DIR'] if cache.get(k)]
        roots += [Path(cache['SDL2_DIR']).parents[2]] if cache.get('SDL2_DIR') else []
        pc_dirs=[p for pattern in ['*-dev/lib/pkgconfig','*-dev/share/pkgconfig','*/lib/pkgconfig','*/share/pkgconfig'] for p in Path('/nix/store').glob(pattern) if p.is_dir()]
        pc_files={}
        for directory in pc_dirs:
            for file in directory.glob('*.pc'):pc_files.setdefault(file.stem,file)
        needed=set();pending=['epoxy']
        while pending:
            name=pending.pop()
            if name in needed:continue
            needed.add(name);file=pc_files.get(name)
            if not file:continue
            for line in file.read_text(errors='replace').splitlines():
                if line.startswith(('Requires:','Requires.private:')):
                    pending.extend(x.strip().split()[0] for x in line.split(':',1)[1].split(',') if x.strip())
        pc=[str(path.parent) for name,path in pc_files.items() if name in needed]
        env['PKG_CONFIG_PATH']=os.pathsep.join(pc+[env.get('PKG_CONFIG_PATH','')])
        env['PATH']=os.pathsep.join([str(Path(cache[k]).parent) for k in ['CMAKE_C_COMPILER','CMAKE_MAKE_PROGRAM','CMAKE_COMMAND','PKG_CONFIG_EXECUTABLE']]+[env['PATH']])
    if not cmake:raise SystemExit('cmake unavailable: enter nix develop or use --reuse-runtime-cache')
    dest=ROOT/'build';dest.mkdir(parents=True,exist_ok=True)
    config=[cmake,'-S',str(ROOT),'-B',str(dest),'-G','Ninja','-DCMAKE_BUILD_TYPE=Debug',*args]
    subprocess.run(config,env=env,check=True)
    with (dest/'build.log').open('w') as log:
        result=subprocess.run([cmake,'--build',str(dest),'--parallel',str(a.jobs)],env=env,stdout=log,stderr=subprocess.STDOUT)
    print((dest/'build.log').read_text()[-6500:]);return result.returncode
if __name__=='__main__':raise SystemExit(main())
