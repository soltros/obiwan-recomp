#!/usr/bin/env python3
"""Local, read-only game analysis. All output stays inside this project."""
import argparse
import collections
import hashlib
import json
import re
import struct
import subprocess
import sys
from pathlib import Path
try:
    from obiwan_assets import inspect_bundle, BundleError, inspect_laf, LafError
except ImportError:
    inspect_bundle = BundleError = inspect_laf = LafError = None

PROJECT=Path(__file__).resolve().parents[1]
DEFAULT_ROOT=PROJECT.parent
TITLES={
 'obiwan':('Star Wars - Obi-Wan (USA)','3511048a815085f78a8f1c298355b0c887a9d1040e211f888f39376cf101da53')}

def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(path)

def file_paths(folder):
    result=[]
    for p in sorted(folder.rglob('*')):
        if p.is_symlink():raise ValueError(f'symlink not supported in inputs: {p}')
        if p.is_file():result.append(p)
    return result

def inventory(folder):
    rows=[]; folded=collections.defaultdict(list)
    for p in file_paths(folder):
        rel=p.relative_to(folder).as_posix();folded[rel.casefold()].append(rel)
        before=p.stat();sha=digest(p);after=p.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
            raise ValueError(f'input changed while hashing: {p}')
        rows.append({'path':rel,'size':after.st_size,'sha256':sha})
    return {'schema':1,'source_directory':folder.name,'files':rows,'file_count':len(rows),
            'total_bytes':sum(x['size'] for x in rows),'case_collisions':[v for v in folded.values() if len(v)>1]}

def differences(expected,actual):
    old={x['path']:x for x in expected['files']};new={x['path']:x for x in actual['files']}
    return {'missing':sorted(old.keys()-new.keys()),'added':sorted(new.keys()-old.keys()),
            'changed':sorted(k for k in old.keys()&new.keys() if old[k]!=new[k])}

def checked_sections(data):
    def get(fmt,off):
        size=struct.calcsize('<'+fmt)
        if off<0 or off+size>len(data):raise ValueError('truncated XBE structure')
        return struct.unpack_from('<'+fmt,data,off)
    def u(off):return get('I',off)[0]
    if data[:4]!=b'XBEH':raise ValueError('invalid XBE magic')
    base,headers,image=u(0x104),u(0x108),u(0x10c)
    if headers<0x178 or headers>len(data):raise ValueError('invalid header size')
    count,table=u(0x11c),u(0x120)-base
    if not 0<count<=4096 or table<0 or table+count*56>headers:raise ValueError('invalid section table')
    secs=[]
    for i in range(count):
        flags,va,vs,raw,size,name=get('6I',table+56*i)
        if raw+size>len(data) or size>vs or va<base or va+vs>base+image:
            raise ValueError(f'invalid section extent {i}')
        n=name-base
        end=data.find(b'\0',n,min(headers,n+256)) if 0<=n<headers else -1
        if end<0:raise ValueError('invalid section name')
        secs.append({'name':data[n:end].decode('ascii'),'va':va,'virtual_size':vs,'offset':raw,'size':size,'flags':flags})
    ordered=sorted(secs,key=lambda s:s['va'])
    for a,b in zip(ordered,ordered[1:]):
        if a['va']+a['virtual_size']>b['va']:raise ValueError('overlapping virtual sections')
    return secs

def va_offset(secs,va,size=1):
    for s in secs:
        if size>=0 and s['va']<=va and va+size<=s['va']+s['size']:
            return s['offset']+va-s['va']
    raise ValueError(f'VA 0x{va:08x} has no file-backed span of {size} bytes')

def string_anchors(data,secs):
    anchors=[]
    for s in secs:
        payload=data[s['offset']:s['offset']+s['size']]
        for m in re.finditer(rb'[ -~]{8,}',payload):
            text=m.group().decode('ascii')
            if re.search(r'(?i)(\\.*\.(cpp|h|pdb)|tanis|ucdeathmatch|xboxloadsave|script\.lin)',text):
                va=s['va']+m.start();needle=struct.pack('<I',va);refs=[]
                for section in secs:
                    start=section['offset'];end=start+section['size'];at=data.find(needle,start,end)
                    while at>=0:
                        refs.append({'va':section['va']+at-start,'section':section['name']});at=data.find(needle,at+1,end)
                anchors.append({'va':va,'section':s['name'],'text':text,'raw_address_occurrences':refs})
    return {'warning':'Raw address occurrences are candidates, NOT decoded instruction xrefs or function starts.','anchors':anchors}

def xbe_reports(key,folder):
    path=folder/'default.xbe';data=path.read_bytes();secs=checked_sections(data)
    if hashlib.sha256(data).hexdigest()!=TITLES[key][1]:raise ValueError('unsupported executable hash')
    entry=struct.unpack_from('<I',data,0x128)[0]^0xa8fc57ab
    thunk=struct.unpack_from('<I',data,0x158)[0]^0x5b6d40b6
    va_offset(secs,entry);ords=[]
    for i in range(4096):
        v=struct.unpack_from('<I',data,va_offset(secs,thunk+4*i,4))[0]
        if not v:break
        if not v&0x80000000:raise ValueError('non-ordinal kernel thunk')
        ords.append(v&0x7fffffff)
    else:raise ValueError('unterminated kernel thunk table')
    out=PROJECT/'reports'/key;out.mkdir(parents=True,exist_ok=True)
    subprocess.run([sys.executable,str(PROJECT/'vendor/xboxrecomp-parser/xbe_parser.py'),str(path),'--quiet','--json',str(out/'xbe.json')],check=True)
    upstream=json.loads((out/'xbe.json').read_text())
    if int(upstream['entry_point'],16)!=entry or [x['ordinal'] for x in upstream['kernel_imports']]!=ords:
        raise ValueError('independent header/thunk checks disagree with upstream parser')
    for s,other in zip(secs,upstream['sections'],strict=True):
        if (s['va'],s['offset'],s['size'])!=(int(other['virtual_addr'],16),int(other['raw_addr'],16),other['raw_size']):
            raise ValueError('upstream section mismatch')
    write_json(out/'section-map.json',{'sha256':TITLES[key][1],'entry':entry,'kernel_thunk':thunk,'sections':secs,'kernel_ordinals':ords,'upstream_crosscheck':'passed'})
    write_json(out/'string-anchors.json',string_anchors(data,secs))
    # An ordinary Linux objdump can inspect a bounded entry window; this is not CFG recovery.
    import shutil
    if shutil.which('objdump'):
        offset=va_offset(secs,entry)
        sec=next(s for s in secs if s['offset']<=offset<s['offset']+s['size'])
        raw=out/'entry-window.bin';raw.write_bytes(data[offset:min(offset+256,sec['offset']+sec['size'])])
        cmd=['objdump','-D','-b','binary','-m','i386','-M','intel',f'--adjust-vma={entry}',str(raw)]
        result=subprocess.run(cmd,capture_output=True,text=True,check=True)
        (out/'entry-disassembly.txt').write_text('Linear 256-byte entry window; not a function-boundary proof.\n'+result.stdout)
    write_json(PROJECT/'target.json',{'id':key,'directory':folder.name,'executable':'default.xbe','sha256':TITLES[key][1],'entry':f'0x{entry:08x}','target':'x86_64-linux','status':'static analysis only','section_policy':'Determine reachable code in every section; never treat section executable flags as proof.'})
    print(f'{key}: upstream cross-check passed, {len(secs)} sections, {len(ords)} kernel imports')

def obiwan_assets(folder):
    manifest=json.loads((PROJECT/'manifest.json').read_text())
    loose={r['path'].casefold():r for r in manifest['files']}
    reports=[]
    for p in sorted(folder.rglob('*.bndl')):
        data=p.read_bytes(); report=inspect_bundle(data,loose);report['path']=p.relative_to(folder).as_posix()
        anomaly=report['anomaly']
        if anomaly:
            other=loose.get(anomaly['relative_path'].casefold())
            if other:
                payload=(folder/other['path']).read_bytes()
                anomaly['loose_path']=other['path'];anomaly['loose_size']=len(payload)
                anomaly['matches_loose_prefix']=data[anomaly['offset']:]==payload[:anomaly['available_size']]
        reports.append(report)
    write_json(PROJECT/'reports/obiwan/bundles.json',reports)
    training=folder/'data/levels/training'
    world=(training/'tr.tan').read_text();actors=(training/'tr.act').read_text()
    counts={k:int(v) for k,v in re.findall(r'(?m)^(ZONES|REGIONS|PORTALS):\s+(\d+)',world)}
    actor_types=collections.Counter(re.findall(r'(?m)^ACTOR\s+\d+\s+"([^"]+)"',actors))
    write_json(PROJECT/'reports/obiwan/training.json',{'declared_world_counts':counts,
        'script_reference':re.search(r'(?m)^SCRIPT:\s*(.+)',world).group(1),
        'actor_types':dict(actor_types),'actor_lines':sum(actor_types.values()),
        'files':[p.relative_to(folder).as_posix() for p in sorted(training.iterdir()) if p.is_file()],
        'scope':'Text export metadata only; not a proven runtime dependency closure.'})
    print(f'Obi-Wan: {len(reports)} bundles inspected; {sum(r["anomaly"] is not None for r in reports)} payload anomaly')

def obiwan_fonts(folder):
    reports=[]
    for path in sorted((folder/'data/fonts').glob('*.laf')):
        data=path.read_bytes()
        try:
            result=inspect_laf(data)
        except LafError as exc:
            result={'layout_status':'invalid','error':str(exc)}
        reports.append({'path':path.relative_to(folder).as_posix(),'size':len(data),
                        'sha256':hashlib.sha256(data).hexdigest(),**result})
    write_json(PROJECT/'reports/obiwan/fonts.json',{
        'font_files':reports,
        'scope':'Validates observed container length, character map, ordered in-range bitmap offsets, and payload hash. Glyph metrics and pixel encoding remain opaque.'})
    invalid=sum(x['layout_status']=='invalid' for x in reports)
    print(f'Obi-Wan: {len(reports)} LAF fonts inspected; {invalid} invalid containers')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('command',choices=['manifest','verify','xbe','assets','fonts','baseline']);ap.add_argument('--game-root',type=Path,default=DEFAULT_ROOT);ap.add_argument('--game-dir',type=Path,help='use this extracted title directory directly');ap.add_argument('--title',choices=['all',*TITLES],default='all');ap.add_argument('--replace-manifest',action='store_true',help='explicitly replace baseline hashes')
    a=ap.parse_args();keys=list(TITLES) if a.title=='all' else [a.title]
    for key in keys:
        folder=a.game_dir if a.game_dir else a.game_root/TITLES[key][0]
        if not folder.is_dir():raise ValueError(f'missing input directory: {folder}')
        path=PROJECT/'manifest.json'
        if a.command in ('manifest','verify','baseline'):
            actual=inventory(folder)
            if path.exists() and not (a.command=='manifest' and a.replace_manifest):
                diff=differences(json.loads(path.read_text()),actual)
                write_json(PROJECT/'reports'/key/'manifest-verification.json',diff)
                if any(diff.values()):raise ValueError(f'{key}: baseline mismatch; see verification report')
                print(f'{key}: verified {actual["file_count"]} files / {actual["total_bytes"]} bytes')
            elif a.command=='verify':raise ValueError(f'no baseline manifest: {path}')
            else:
                write_json(path,actual);print(f'{key}: created manifest, {actual["file_count"]} files')
        if a.command in ('xbe','baseline'):xbe_reports(key,folder)
        if key=='obiwan' and a.command in ('assets','baseline'):obiwan_assets(folder)
        if key=='obiwan' and a.command in ('fonts','baseline'):obiwan_fonts(folder)

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.CalledProcessError) as e:print(f'ERROR: {e}',file=sys.stderr);sys.exit(1)
