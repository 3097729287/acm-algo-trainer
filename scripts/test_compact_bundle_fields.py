"""A public-field builder may produce an ordinary binary patch with zero fields."""
import hashlib,json,sqlite3,sys,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'desktop'),str(ROOT/'backend')]
from build_compact_bundle import build
from compact_update import load

class EmptyPublicFieldsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.base=self.root/'base';self.target=self.root/'target'
        for path,version,raw in [(self.base,'1.6.6',b'O'*2048),(self.target,'1.6.10',b'N'*2048)]:
            (path/'data').mkdir(parents=True);(path/'_internal').mkdir()
            (path/'VERSION').write_text(version);(path/'ToBe.exe').write_bytes(b'fixture native runner')
            (path/'_internal/base_library.zip').write_bytes(b'fixture immutable runtime')
            (path/'data/library.sqlite3').write_bytes(raw)
        self.patch=self.root/'verified.tbbd';self.patch.write_bytes(b'prebuilt binary payload, independently checked by its producer')
        self.proof={'sourceSha256':hashlib.sha256(b'O'*2048).hexdigest(),'targetSha256':hashlib.sha256(b'N'*2048).hexdigest(),
                    'templateSha256':hashlib.sha256(b'N'*2048).hexdigest(),'patch':str(self.patch),'fields':[]}
    def test_zero_fields_emit_an_ordinary_variant_accepted_by_the_unchanged_runtime_validator(self):
        receipt=self.root/'fields.json';receipt.write_text(json.dumps(self.proof));output=self.root/'update.zip'
        result=build(self.target,[self.base],output,self.root/'unused-tool',field_delta=receipt)
        with zipfile.ZipFile(output) as archive:
            manifest=load(archive,'1.6.10');variant=manifest['files']['data/library.sqlite3']['variants'][0]
            self.assertEqual(archive.read(variant['payload']),self.patch.read_bytes())
            self.assertEqual(variant['format'],'binary');self.assertNotIn('publicFields',variant);self.assertNotIn('templateSha256',variant)
        self.assertEqual(result['fromVersion'],'1.6.6')
    def test_zero_fields_cannot_claim_an_intermediate_template_digest(self):
        self.proof['templateSha256']='0'*64;receipt=self.root/'fields.json';receipt.write_text(json.dumps(self.proof))
        with self.assertRaisesRegex(ValueError,'empty public-field proof'):build(self.target,[self.base],self.root/'update.zip',self.root/'unused-tool',field_delta=receipt)
if __name__=='__main__':unittest.main()
