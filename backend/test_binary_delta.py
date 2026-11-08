"""Independent BSDIFF40 vectors and bounded complete-file reconstruction."""
import base64
import bz2
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from binary_delta import MAGIC,MAX_BLOCK,file_delta,patch_block

FIXTURE=Path(__file__).parent/'fixtures/binary-delta/bsdiff40.json'


def framed(source,target,patch):
    meta={'schema':1,'sourceBytes':len(source),'sourceSha256':hashlib.sha256(source).hexdigest(),
        'targetBytes':len(target),'targetSha256':hashlib.sha256(target).hexdigest(),
        'blocks':[{'sourceOffset':0,'sourceBytes':len(source),'targetBytes':len(target),'patchBytes':len(patch),'patchSha256':hashlib.sha256(patch).hexdigest()}]}
    header=json.dumps(meta).encode()
    return MAGIC+struct.pack('<I',len(header))+header+patch


class BinaryDeltaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        value=json.loads(FIXTURE.read_text(encoding='utf-8'))
        cls.vectors=[{k:base64.b64decode(v) for k,v in row.items()} for row in value['vectors']]

    def test_decodes_independent_native_bsdiff4_vectors(self):
        for index,row in enumerate(self.vectors):
            with self.subTest(vector=index):self.assertEqual(patch_block(row['source'],row['patch']),row['target'])

    def test_every_truncation_of_header_and_control_stream_is_rejected(self):
        row=self.vectors[1]
        for stop in [0,7,8,16,24,31,32,len(row['patch'])-1]:
            with self.subTest(stop=stop),self.assertRaises((ValueError,OSError,EOFError)):
                patch_block(row['source'],row['patch'][:stop])

    def test_output_bound_and_compression_bomb_are_rejected(self):
        row=self.vectors[1]
        bad=row['patch'][:24]+(MAX_BLOCK+1).to_bytes(8,'little')+row['patch'][32:]
        with self.assertRaises(ValueError):patch_block(row['source'],bad)
        controls=bz2.compress(bytes(MAX_BLOCK+1));empty=bz2.compress(b'')
        bad=b'BSDIFF40'+len(controls).to_bytes(8,'little')+len(empty).to_bytes(8,'little')+(1).to_bytes(8,'little')+controls+empty+empty
        with self.assertRaises(ValueError):patch_block(b'',bad)

    def test_file_output_is_bound_to_exact_source_and_final_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source';patch=root/'payload';target=root/'output'
            row=self.vectors[-1];source.write_bytes(row['source']);patch.write_bytes(framed(**row))
            sha=hashlib.sha256(row['target']).hexdigest()
            result=file_delta(source,patch,target,expected_target=sha)
            self.assertEqual(target.read_bytes(),row['target']);self.assertEqual(result['sha256'],sha)
            with self.assertRaises(ValueError):file_delta(source,patch,target,expected_target=sha)
            self.assertEqual(target.read_bytes(),row['target'])

    def test_wrong_base_is_rejected_before_creating_any_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source';patch=root/'payload';target=root/'output'
            row=self.vectors[1];source.write_bytes(b'changed source');patch.write_bytes(framed(**row))
            with self.assertRaises(ValueError):file_delta(source,patch,target,expected_target=hashlib.sha256(row['target']).hexdigest())
            self.assertFalse(target.exists())

    def test_trailing_or_corrupt_payload_never_reports_a_verified_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source';patch=root/'payload';row=self.vectors[1];source.write_bytes(row['source'])
            value=framed(**row)
            for index,data in enumerate([value+b'x',value[:-1]+bytes([value[-1]^1])]):
                patch.write_bytes(data)
                with self.assertRaises(ValueError):file_delta(source,patch,root/str(index),expected_target=hashlib.sha256(row['target']).hexdigest())


if __name__=='__main__':unittest.main()
