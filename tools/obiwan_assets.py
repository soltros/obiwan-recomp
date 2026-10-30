"""Inspect observed BUNDLE records without extracting or modifying assets."""
import hashlib
import struct

class BundleError(ValueError):
    pass

def inspect_bundle(data, loose=None):
    if data[:7] != b'BUNDLE\n':raise BundleError('unsupported bundle header')
    pos=7;entries=[];anomaly=None
    while pos<len(data):
        end=data.find(b'\n',pos,min(pos+4096,len(data)))
        if end<0 or end+5>len(data):raise BundleError(f'truncated record header at {pos}')
        try:name=data[pos:end].decode('ascii')
        except UnicodeDecodeError as e:raise BundleError('non-ASCII bundle path') from e
        size=struct.unpack_from('<I',data,end+1)[0];pos=end+5;available=len(data)-pos
        rel=name.replace('\\','/');rel=rel[3:] if rel[:3].lower()=='d:/' else rel
        # Lookup only. Never pass bundle paths to a filesystem writer.
        if '..' in rel.split('/') or rel.startswith('/') or ':' in rel:raise BundleError('unsafe resource path')
        row={'resource':name,'relative_path':rel,'offset':pos,'declared_size':size}
        if size>available:
            row['available_size']=available;anomaly={'kind':'truncated_payload',**row};break
        row['sha256']=hashlib.sha256(data[pos:pos+size]).hexdigest()
        if loose is not None:
            other=loose.get(rel.casefold());row['loose_path']=other['path'] if other else None
            row['matches_loose']=row['sha256']==other['sha256'] if other else None
        entries.append(row);pos+=size
    return {'complete_entries':len(entries),'entries':entries,'anomaly':anomaly,'bytes':len(data),
            'format_status':'Observed newline path + little-endian uint32 length + payload; no loader execution yet.'}
