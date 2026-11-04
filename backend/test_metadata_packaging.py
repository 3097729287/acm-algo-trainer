"""Source and compressed release metadata produce the same public overlay."""
import gzip,json,tempfile,unittest
from pathlib import Path
from integrations import read_public_metadata

class MetadataPackagingTests(unittest.TestCase):
    def test_compression_preserves_every_public_record_and_rejects_corruption(self):
        source=Path(__file__).parent/'resources/public-problem-metadata.json'
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/source.name
            compressed=gzip.compress(source.read_bytes(),compresslevel=9,mtime=0)
            Path(str(target)+'.gz').write_bytes(compressed)
            self.assertEqual(read_public_metadata(target),read_public_metadata(source))
            target.write_text('{"stale upgrade residue":true}','utf8')
            self.assertEqual(read_public_metadata(target),read_public_metadata(source),'The current compressed overlay wins over an obsolete uncompressed file')
            self.assertLess(len(compressed),source.stat().st_size//3)
            Path(str(target)+'.gz').write_bytes(b'corrupt fixture')
            with self.assertRaises((OSError,ValueError)):read_public_metadata(target)
