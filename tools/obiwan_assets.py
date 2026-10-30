"""Inspect observed BUNDLE records without extracting or modifying assets."""
import hashlib
import struct

class BundleError(ValueError):
    pass

class LafError(ValueError):
    pass

def inspect_laf(data):
    """Validate the observed LAF container without guessing glyph metrics.

    The title's files have an eight-word header, a uint16 character map,
    16-byte per-slot records whose first word points into a trailing bitmap
    payload, and no trailing bytes. Other record fields remain opaque here.
    """
    if len(data) < 32:
        raise LafError('truncated LAF header')
    header = struct.unpack_from('<8I', data)
    count, bitmap_size = header[:2]
    if count != 256:
        raise LafError(f'unsupported glyph slot count: {count}')
    payload_offset = 32 + count * 2 + count * 16
    expected_size = payload_offset + bitmap_size
    if expected_size != len(data):
        raise LafError(f'file size {len(data)} does not match declared layout size {expected_size}')
    charmap = list(struct.unpack_from('<256H', data, 32))
    record_start = 32 + count * 2
    offsets = [struct.unpack_from('<I', data, record_start + i * 16)[0]
               for i in range(count)]
    if any(offset > bitmap_size for offset in offsets):
        raise LafError('glyph data pointer is outside bitmap payload')
    if any(left > right for left, right in zip(offsets, offsets[1:])):
        raise LafError('glyph data pointers are not ordered')
    return {
        'slot_count': count,
        'header_words_opaque': list(header[2:]),
        'character_map_identity': charmap == list(range(256)),
        'payload_offset': payload_offset,
        'bitmap_payload_size': bitmap_size,
        'bitmap_payload_sha256': hashlib.sha256(data[payload_offset:]).hexdigest(),
        'glyph_data_offsets': offsets,
        'layout_status': 'valid under observed 256-slot layout; per-glyph fields are not decoded',
    }

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
