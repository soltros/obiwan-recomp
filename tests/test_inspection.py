import struct
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from workspace import checked_sections, va_offset, inventory, differences

def xbe():
    b=bytearray(0x220);b[:4]=b'XBEH'
    for off,val in {0x104:0x10000,0x108:0x200,0x10c:0x1020,0x11c:1,0x120:0x10180}.items():struct.pack_into('<I',b,off,val)
    struct.pack_into('<6I',b,0x180,6,0x11000,0x20,0x200,0x10,0x101c0);b[0x1c0:0x1c6]=b'.text\0'
    return b

from obiwan_assets import inspect_bundle, BundleError, inspect_laf, LafError

class XbeTests(unittest.TestCase):
    def test_mapping_and_zero_fill(self):
        secs=checked_sections(xbe());self.assertEqual(va_offset(secs,0x11004,4),0x204)
        with self.assertRaises(ValueError):va_offset(secs,0x11010)
        with self.assertRaises(ValueError):va_offset(secs,0x1100f,2)
    def test_truncated_xbe(self):
        with self.assertRaises(ValueError):checked_sections(xbe()[:100])
    def test_section_overrun(self):
        b=xbe();struct.pack_into('<I',b,0x190,0x1000)
        with self.assertRaises(ValueError):checked_sections(b)

class BundleTests(unittest.TestCase):
    def test_records(self):
        b=b'BUNDLE\nd:\\a.wav\n'+struct.pack('<I',4)+b'RIFF'
        d=inspect_bundle(b);self.assertEqual(d['complete_entries'],1);self.assertIsNone(d['anomaly'])
    def test_truncation_is_explicit(self):
        b=b'BUNDLE\nd:\\a.wav\n'+struct.pack('<I',10)+b'RIFF'
        d=inspect_bundle(b);self.assertEqual(d['anomaly']['available_size'],4)
    def test_unsafe_path(self):
        with self.assertRaises(BundleError):inspect_bundle(b'BUNDLE\n../x\n'+struct.pack('<I',0))
    def test_missing_header_terminator(self):
        with self.assertRaises(BundleError):inspect_bundle(b'BUNDLE\nd:\\x')

class LafTests(unittest.TestCase):
    def make_laf(self, offsets=(0,2), payload=b'abc'):
        count=256
        offsets=list(offsets)+[offsets[-1]]*(count-len(offsets))
        header=struct.pack('<8I',count,len(payload),1,2,3,4,0,255)
        charmap=struct.pack('<'+'H'*count,*range(count))
        records=b''.join(struct.pack('<I',offset)+bytes(12) for offset in offsets)
        return header+charmap+records+payload
    def test_observed_layout(self):
        report=inspect_laf(self.make_laf())
        self.assertEqual(report['bitmap_payload_size'],3)
        self.assertEqual(report['glyph_data_offsets'][:2],[0,2])
        self.assertEqual(report['glyph_records'][0],{
            'slot':0,'character_code':0,'record_hex':'00000000000000000000000000000000',
            'bitmap_offset':0,'bitmap_span_bytes':2})
        self.assertEqual(report['glyph_records'][-1]['bitmap_span_bytes'],1)
    def test_declared_size_mismatch(self):
        with self.assertRaises(LafError):inspect_laf(self.make_laf()[:-1])
    def test_out_of_range_offset(self):
        with self.assertRaises(LafError):inspect_laf(self.make_laf(offsets=(0,4)))
    def test_descending_offsets(self):
        with self.assertRaises(LafError):inspect_laf(self.make_laf(offsets=(2,1)))

class ManifestTests(unittest.TestCase):
    def test_changes_missing_and_added(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'a').write_bytes(b'a');(p/'b').write_bytes(b'b');old=inventory(p)
            (p/'a').write_bytes(b'z');(p/'b').unlink();(p/'c').write_bytes(b'c')
            self.assertEqual(differences(old,inventory(p)),{'missing':['b'],'added':['c'],'changed':['a']})
    def test_case_collision(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'A').write_bytes(b'a');(p/'a').write_bytes(b'b')
            self.assertEqual(len(inventory(p)['case_collisions']),1)
    def test_known_runtime_artifact_can_be_excluded(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'asset').write_bytes(b'a')
            (p/'snapshot').mkdir();(p/'snapshot/__ui_ss.mismark').touch()
            baseline=inventory(p,('snapshot/__ui_ss.mismark',))
            current=inventory(p,('SNAPSHOT/__UI_SS.MISMARK',))
            self.assertEqual(differences(baseline,current),{
                'missing':[],'added':[],'changed':[]})
            self.assertNotIn('snapshot/__ui_ss.mismark',
                             [row['path'] for row in current['files']])
    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'a').symlink_to('/nonexistent')
            with self.assertRaises(ValueError):inventory(p)


if __name__=='__main__':unittest.main()
