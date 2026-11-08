from contextlib import closing
import base64,bz2,copy,gzip,hashlib,io,json,sqlite3,struct,tempfile,unittest
import threading,time
from pathlib import Path
from unittest.mock import patch
from public_field_patch import patch_file,validate,remote_value,digest,RESOURCE_ROOT

class PublicFieldPatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.app=self.root/'app';(self.app/'state').mkdir(parents=True);self.database=self.app/'state/tb-library.sqlite3'
        self.public=json.dumps({'figure':'public exact figure 中文'},ensure_ascii=False).encode()
        self.old=b'public immutable old source';self.template=bytes(512);self.final=self.template[:100]+self.public+self.template[100+len(self.public):]
        self.source=self.root/'source';self.source.write_bytes(self.old);self.target=self.root/'new'
        packed=gzip.compress(self.public,mtime=0);compressed=digest(packed)
        self.fields=[{'sha256':digest(self.public),'bytes':len(self.public),'compressedSha256':compressed,'compressedBytes':len(packed),'url':RESOURCE_ROOT+compressed+'.bin','candidates':[{'table':'solutions','id':'public::fixture'}],'spans':[[100,0,len(self.public)]]}]
        self.patch=self.root/'literal.tbbd';self.write_patch(self.template)
        with closing(sqlite3.connect(self.database)) as db,db:
            db.execute('CREATE TABLE solutions(problem_id TEXT PRIMARY KEY,images TEXT)');db.execute('INSERT INTO solutions VALUES(?,?)',('public::fixture',self.public.decode()))
            db.execute('CREATE TABLE drafts(code TEXT)');db.execute("INSERT INTO drafts VALUES('private draft must never be read')")
        self.before=self.database.read_bytes()

    def write_patch(self,template):
        control=bz2.compress(struct.pack('<qqq',0,len(template),0));difference=bz2.compress(b'');extra=bz2.compress(template)
        block=b'BSDIFF40'+struct.pack('<qqq',len(control),len(difference),len(template))+control+difference+extra
        info={'schema':1,'sourceBytes':len(self.old),'sourceSha256':digest(self.old),'targetBytes':len(template),'targetSha256':digest(template),'blocks':[{'sourceOffset':0,'sourceBytes':len(self.old),'targetBytes':len(template),'patchBytes':len(block),'patchSha256':digest(block)}]}
        header=json.dumps(info).encode();self.patch.write_bytes(b'TBBD1\r\n\0'+struct.pack('<I',len(header))+header+block)

    def apply(self):return patch_file(self.source,self.patch,self.target,app=self.app,expected_target=digest(self.final),template_sha=digest(self.template),fields=self.fields,target_bytes=len(self.final))

    def test_exact_public_data_is_reused_without_any_private_write_or_network(self):
        with patch('public_field_patch.remote_value',side_effect=AssertionError('public value already present')):result=self.apply()
        self.assertEqual(result['reusedPublicFields'],1);self.assertEqual(self.target.read_bytes(),self.final);self.assertEqual(self.database.read_bytes(),self.before)

    def test_a_different_private_value_is_never_inserted_into_the_public_seed(self):
        with closing(sqlite3.connect(self.database)) as db,db:db.execute("UPDATE solutions SET images='private customized figure'")
        before=self.database.read_bytes()
        with patch('public_field_patch.remote_value',return_value=self.public) as fetched:result=self.apply()
        self.assertEqual(fetched.call_count,1);self.assertEqual(result['downloadedPublicFields'],1)
        self.assertEqual(self.target.read_bytes(),self.final);self.assertEqual(self.database.read_bytes(),before)

    def test_private_tables_and_overlapping_ranges_are_rejected_before_output(self):
        for mutate in [lambda x:x[0]['candidates'][0].update(table='drafts'),lambda x:x[0]['spans'].append(x[0]['spans'][0]),lambda x:x[0]['spans'][0].__setitem__(0,-1),lambda x:x[0].update(url='https://example.com/redirect')]:
            fields=copy.deepcopy(self.fields);mutate(fields)
            with self.assertRaises(ValueError):validate(fields,len(self.final))
        self.assertFalse(self.target.exists());self.assertEqual(self.database.read_bytes(),self.before)

    def test_a_nonempty_template_span_is_not_silently_overwritten(self):
        self.template=self.template[:100]+b'x'+self.template[101:];self.write_patch(self.template)
        with self.assertRaises(ValueError):self.apply()
        self.assertEqual(self.database.read_bytes(),self.before)

    def test_network_bytes_require_compressed_and_expanded_hashes(self):
        item=self.fields[0];raw=gzip.compress(self.public,mtime=0)
        def response(data):
            stream=io.BytesIO(data);stream.status=200;return stream
        opener=unittest.mock.Mock();opener.open.return_value=response(raw)
        with patch('public_field_patch.build_opener',return_value=opener):self.assertEqual(remote_value(item),self.public)
        opener.open.return_value=response(raw[:-1]+b'x')
        with patch('public_field_patch.build_opener',return_value=opener),self.assertRaises(ValueError):remote_value(item)

    def multiple_fields(self):
        self.template=bytes(2048);self.final=bytearray(self.template);self.fields=[];values={}
        for index in range(3):
            raw=json.dumps({'figure':f'公开原图 {index}'},ensure_ascii=False).encode();packed=gzip.compress(raw,mtime=0);sha=digest(raw)
            self.fields.append({'sha256':sha,'bytes':len(raw),'compressedSha256':digest(packed),'compressedBytes':len(packed),
                'url':RESOURCE_ROOT+digest(packed)+'.bin','candidates':[{'table':'solutions','id':f'figure::{index}'}],'spans':[[100+index*200,0,len(raw)]]})
            self.final[100+index*200:100+index*200+len(raw)]=raw;values[sha]=raw
        self.final=bytes(self.final);self.write_patch(self.template)
        return values

    def test_missing_public_fields_download_concurrently_without_reordering_spans(self):
        values=self.multiple_fields();barrier=threading.Barrier(3);threads=set();lock=threading.Lock()
        def fetched(item):
            with lock:threads.add(threading.get_ident())
            barrier.wait(timeout=3)
            # Finish in the reverse order to catch span/value misassociation.
            time.sleep((3-int(item['candidates'][0]['id'].split('::')[1]))*.005)
            return values[item['sha256']]
        with patch('public_field_patch.remote_value',side_effect=fetched):result=self.apply()
        self.assertEqual(len(threads),3);self.assertEqual(result['downloadedPublicFields'],3)
        self.assertEqual(self.target.read_bytes(),self.final);self.assertEqual(self.database.read_bytes(),self.before)

    def test_one_failed_public_download_stops_before_creating_the_output(self):
        values=self.multiple_fields()
        def fetched(item):
            if item is self.fields[1]:raise ValueError('Corrupt public response')
            return values[item['sha256']]
        with patch('public_field_patch.remote_value',side_effect=fetched),self.assertRaises(ValueError):self.apply()
        self.assertFalse(self.target.exists());self.assertEqual(self.database.read_bytes(),self.before)
        self.assertEqual(self.source.read_bytes(),self.old)

if __name__=='__main__':unittest.main()
