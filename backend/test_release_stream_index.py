"""Disposable authoring files and explicit synthetic GitHub metadata only."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from release_stream_index import CHUNK_BYTES,reviewed_stream_asset,merge_stream_index,validate_asset


class ReleaseStreamIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='tb-release-range-author-');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.path=self.root/'ToBe-Full-Setup-1.6.10-win64.exe'
        self.raw=b'installer-proof-fixture\0'*(CHUNK_BYTES//23+20000)
        self.path.write_bytes(self.raw)
        self.sha=hashlib.sha256(self.raw).hexdigest()
        self.github={'name':self.path.name,'size':len(self.raw),'digest':'sha256:'+self.sha,
                     'browser_download_url':'https://ignored-untrusted.example/requester-url'}

    def item(self,**kwargs):return reviewed_stream_asset(self.path,'1.6.10',self.github,**kwargs)

    def test_real_file_chunks_are_bound_to_the_complete_local_and_github_digest(self):
        item=self.item()
        self.assertEqual(item['sha256'],self.sha);self.assertEqual(item['githubDigest'],self.github['digest'])
        self.assertEqual(item['chunkBytes'],1024*1024)
        self.assertEqual(item['chunkSha256'],[hashlib.sha256(self.raw[i:i+CHUNK_BYTES]).hexdigest()for i in range(0,len(self.raw),CHUNK_BYTES)])
        self.assertNotIn('url',item);self.assertNotIn('browser_download_url',item)

    def test_incorrect_github_size_name_or_digest_cannot_author_range_proofs(self):
        for field,value in [('name','other.exe'),('size',len(self.raw)+1),('digest','sha256:'+'a'*64)]:
            with self.subTest(field=field),self.assertRaises(ValueError):
                reviewed_stream_asset(self.path,'1.6.10',dict(self.github,**{field:value}))

    def test_admin_or_nonpublic_names_fail_before_local_bytes_are_read(self):
        path=self.root/'ToBe-Admin-Setup-1.6.10-win64.exe';path.write_bytes(self.raw)
        with patch.object(Path,'open',side_effect=AssertionError('Private artifact must not be hashed')),self.assertRaises(ValueError):
            reviewed_stream_asset(path,'1.6.10',dict(self.github,name=path.name))

    def test_public_route_alias_retains_the_exact_original_filename(self):
        item=self.item(name='ToBe-Setup-1.6.10-win64.exe')
        self.assertEqual(item['sourceName'],self.path.name)
        for name in ['../ToBe-Setup-1.6.10-win64.exe','ToBe-Admin-Setup-1.6.10-win64.exe','https://untrusted.example/file.exe']:
            with self.assertRaises(ValueError):self.item(name=name)

    def test_existing_identity_can_gain_proofs_but_cannot_change_source_bytes(self):
        item=self.item();old={k:item[k]for k in ['version','name','size','sha256']}
        existing={'schema':1,'assets':[old]};snapshot=copy.deepcopy(existing)
        upgraded=merge_stream_index(existing,[item]);self.assertEqual(existing,snapshot)
        self.assertEqual(upgraded['assets'],[item])
        self.assertEqual(merge_stream_index(upgraded,[old]),upgraded)
        with self.assertRaisesRegex(ValueError,'Duplicate'):merge_stream_index({'schema':1,'assets':[old,old]},[item])
        for field,value in [('sha256','b'*64),('size',item['size']+1),('sourceName','ToBe-Setup-1.6.10-win64.exe')]:
            changed=dict(old,**{field:value})
            with self.assertRaisesRegex(ValueError,'immutable'):merge_stream_index(existing,[changed])

    def test_malformed_block_authority_and_history_overflow_are_rejected(self):
        item=self.item()
        for change in [{'githubDigest':'sha256:'+'b'*64},{'chunkBytes':65536},{'chunkSha256':[]},{'chunkSha256':['invalid']}]:
            with self.assertRaises(ValueError):validate_asset(dict(item,**change))
        history=[{'version':f'1.0.{i}','name':f'ToBe-Setup-1.0.{i}-win64.exe','size':10,'sha256':'0'*64}for i in range(100)]
        with self.assertRaises(ValueError):merge_stream_index({'schema':1,'assets':history},[item])
        self.assertEqual(len(history),100)

    def test_actual_authoring_cli_creates_only_a_verified_new_index_and_refuses_drafts(self):
        metadata=self.root/'public-gh-fixture.json';output=self.root/'approved-index.json'
        release={'isDraft':False,'tagName':'v1.6.10','assets':[self.github]}
        metadata.write_text(json.dumps(release),'utf8')
        command=[sys.executable,str(ROOT/'scripts/release_stream_index.py'),'--asset',str(self.path),
                 '--version','1.6.10','--github-release',str(metadata),'--output',str(output)]
        result=subprocess.run(command,capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(output.read_text('utf8'))['assets'],[self.item()])
        before=output.read_bytes();self.assertNotEqual(subprocess.run(command,capture_output=True,timeout=10).returncode,0)
        self.assertEqual(output.read_bytes(),before)
        release['isDraft']=True;metadata.write_text(json.dumps(release),'utf8');command[-1]=str(self.root/'must-not-exist.json')
        self.assertNotEqual(subprocess.run(command,capture_output=True,timeout=10).returncode,0)
        self.assertFalse(Path(command[-1]).exists())


if __name__=='__main__':unittest.main()
