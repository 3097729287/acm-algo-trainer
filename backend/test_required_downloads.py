"""Only synthetic small ZIPs; real P7351 end-to-end proof is a separate script."""
from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import http.client
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import zipfile

from required_downloads import RequiredDownloads,CHUNK_BYTES,MAX_DOWNLOAD,attach_statement,byte_range,validate_manifest
from public_assets import MAX_ASSET,PUBLIC_ROOT,validate_reference
import test_accounts as account_fixtures


class Response(io.BytesIO):
    def __init__(self,raw,start,end,url,*,fault=False,wrong_range=False):
        super().__init__(raw[start:end+1]);self.status=206;self.url=url;self.fault=fault;self.reads=0
        self.headers={'Content-Length':str(end-start+1),'Content-Range':f'bytes {start}-{end}/{len(raw)}'}
        if wrong_range:self.headers['Content-Range']='bytes 0-1/2'
    def read(self,count=-1):
        self.reads+=1
        if self.fault and self.reads==2:raise OSError('Synthetic interrupted HTTP transfer')
        return super().read(count)


class RequiredDownloadTests(unittest.TestCase):
    def setUp(self):
        # Positive transfers use the in-memory synthetic opener even when the
        # full offline test runner exports TB_OFFLINE=1. Offline behavior is
        # exercised explicitly, without weakening the production guard.
        online_fixture=patch.dict('os.environ',{'TB_OFFLINE':'0'})
        online_fixture.start();self.addCleanup(online_fixture.stop)
        self.temp=tempfile.TemporaryDirectory(prefix='tb-required-inputs-');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.member=(b'exact synthetic input\n'*11000)
        data=io.BytesIO()
        with zipfile.ZipFile(data,'w',compression=zipfile.ZIP_STORED)as archive:archive.writestr('fixture.in',self.member)
        self.raw=data.getvalue();self.sha=hashlib.sha256(self.raw).hexdigest()
        self.url='https://fixture.example/original/down.zip';self.source='https://fixture.example/problem/1'
        self.markdown='# Required fixture\n\n[Original inputs]('+self.url+')\n'
        self.item={'sha256':self.sha,'bytes':len(self.raw),'mime':'application/zip','fileName':'down.zip',
            'problemId':'fixture::required','problemType':'output-only','role':'required-output-only-inputs',
            'manuallyReviewed':True,'requiredForStatement':True,'optional':False,'reviewSha256':'a'*64,
            'sourceUrl':self.source,'originalDownloadUrl':self.url,
            'statementSha256':[hashlib.sha256(self.markdown.encode()).hexdigest()],
            'chunkBytes':CHUNK_BYTES,'chunkSha256':[hashlib.sha256(self.raw[i:i+CHUNK_BYTES]).hexdigest()for i in range(0,len(self.raw),CHUNK_BYTES)],
            'members':[{'name':'fixture.in','bytes':len(self.member),'sha256':hashlib.sha256(self.member).hexdigest()}]}
        self.manifest=self.root/'manifest.json';self.manifest.write_text(json.dumps({'schema':1,'downloads':[self.item]}),'utf8')
        self.requests=[];self.fault_once=False;self.corrupt=False;self.wrong_range=False
        self.manager=RequiredDownloads(manifest_path=self.manifest,cache_root=self.root/'cache',origin='http://127.0.0.1:19999',opener_factory=lambda url:self,retries=1)

    def open(self,request,timeout):
        self.requests.append(request)
        self.assertEqual(timeout,20)
        self.assertEqual(request.full_url,'http://127.0.0.1:19999/updates/required-downloads/'+self.sha+'.zip')
        self.assertFalse(request.has_header('Authorization'));self.assertFalse(request.has_header('Cookie'))
        start,end=map(int,request.get_header('Range')[6:].split('-'))
        raw=self.raw
        if self.corrupt:
            changed=bytearray(raw);changed[CHUNK_BYTES+100]^=1;raw=bytes(changed)
        fault=self.fault_once;self.fault_once=False
        return Response(raw,start,end,request.full_url,fault=fault,wrong_range=self.wrong_range)

    def download(self,**kwargs):return b''.join(self.manager.blocks(self.sha,**kwargs))

    def test_exact_download_has_durable_verified_cache_and_offline_reuse(self):
        self.assertEqual(self.download(),self.raw)
        self.assertEqual((self.root/'cache'/(self.sha+'.zip')).read_bytes(),self.raw)
        self.assertFalse((self.root/'cache'/(self.sha+'.part')).exists())
        self.assertEqual(len(self.requests),1)
        with patch.dict('os.environ',{'TB_OFFLINE':'1'}):self.assertEqual(self.download(),self.raw)
        self.assertEqual(len(self.requests),1)
        self.assertTrue(self.manager.status(self.sha)['cached'])
    def test_uncached_offline_request_never_opens_the_distribution_origin(self):
        with patch.dict('os.environ',{'TB_OFFLINE':'1'}):
            with self.assertRaisesRegex(OSError,'offline'):self.download()
        self.assertEqual(self.requests,[])
        self.assertFalse(self.manager.status(self.sha)['cached'])

    def test_disconnect_retries_from_verified_prefix_without_restarting_download(self):
        self.fault_once=True
        self.assertEqual(self.download(),self.raw)
        self.assertEqual([r.get_header('Range')for r in self.requests],[f'bytes=0-{len(self.raw)-1}',f'bytes={CHUNK_BYTES}-{len(self.raw)-1}'])

    def test_corrupt_block_is_never_cached_and_next_click_resumes_verified_prefix(self):
        self.corrupt=True
        with self.assertRaisesRegex(ValueError,'checksum'):self.download()
        self.assertFalse((self.root/'cache'/(self.sha+'.zip')).exists())
        self.assertEqual((self.root/'cache'/(self.sha+'.part')).stat().st_size,CHUNK_BYTES)
        self.corrupt=False
        self.assertEqual(self.download(),self.raw)
        self.assertEqual(self.requests[-1].get_header('Range'),f'bytes={CHUNK_BYTES}-{len(self.raw)-1}')

    def test_completed_partial_after_crash_is_verified_and_promoted_without_network(self):
        folder=self.root/'cache';folder.mkdir();(folder/(self.sha+'.part')).write_bytes(self.raw)
        with patch.dict('os.environ',{'TB_OFFLINE':'1'}):self.assertEqual(self.download(),self.raw)
        self.assertEqual(self.requests,[])
        self.assertTrue((folder/(self.sha+'.zip')).is_file())

    def test_corrupt_complete_cache_repairs_only_after_rechecking_each_chunk(self):
        self.download();self.requests.clear()
        cached=self.root/'cache'/(self.sha+'.zip')
        with cached.open('r+b')as f:f.seek(CHUNK_BYTES+17);f.write(b'X')
        self.assertEqual(self.download(),self.raw)
        self.assertEqual(self.requests[0].get_header('Range'),f'bytes={CHUNK_BYTES}-{len(self.raw)-1}')

    def test_partial_range_uses_whole_verified_blocks_and_never_claims_whole_cache(self):
        start,end=123456,124000
        self.assertEqual(self.download(start=start,end=end),self.raw[start:end+1])
        self.assertEqual(self.manager.status(self.sha)['verifiedBytes'],2*CHUNK_BYTES)
        self.assertFalse(self.manager.status(self.sha)['cached'])
        self.assertEqual(self.download(),self.raw)
        self.assertEqual(self.requests[-1].get_header('Range'),f'bytes={2*CHUNK_BYTES}-{len(self.raw)-1}')

    def test_canceled_browser_keeps_verified_prefix_and_releases_download_lock(self):
        stream=self.manager.blocks(self.sha);self.assertEqual(next(stream),self.raw[:CHUNK_BYTES]);stream.close()
        self.assertFalse(self.manager.status(self.sha)['downloading'])
        self.assertEqual(self.download(),self.raw)

    def test_concurrent_downloads_share_one_verified_cache_transfer(self):
        with ThreadPoolExecutor(2)as pool:
            futures=[pool.submit(self.download)for _ in range(2)]
            self.assertTrue(all(f.result(5)==self.raw for f in futures))
        self.assertEqual(len(self.requests),1)

    def test_bad_content_range_cannot_append_or_finish_an_archive(self):
        self.wrong_range=True
        with self.assertRaisesRegex(ValueError,'range'):self.download()
        self.assertFalse(self.manager.status(self.sha)['cached'])
        self.assertEqual(self.manager.status(self.sha)['verifiedBytes'],0)

    def test_unknown_identity_and_untrusted_origin_never_start_network(self):
        for sha in ['a'*64,'../file','https://evil.example/data.zip']:
            with self.assertRaises(FileNotFoundError):list(self.manager.blocks(sha))
        with self.assertRaisesRegex(ValueError,'Untrusted'):
            RequiredDownloads(manifest_path=self.manifest,origin='https://untrusted.example')
        self.assertEqual(self.requests,[])

    def test_source_binding_does_not_change_retirement_history_or_completeness(self):
        source={'id':'fixture::required','url':self.source,'markdown':self.markdown,'integrity':{'status':'incomplete'},'statementRetired':True,'samples':[{'input':'native','output':'answer'}]}
        result=attach_statement(source,manager=self.manager)
        self.assertEqual(result['attachments'][self.url]['data'],'/api/required-downloads/'+self.sha)
        for key in source:self.assertEqual(result[key],source[key])
        for changed in [dict(source,markdown=self.markdown+'changed'),dict(source,id='another'),dict(source,url='https://fixture.example/other')]:
            self.assertNotIn('attachments',attach_statement(changed,manager=self.manager))

    def test_source_metadata_read_does_not_construct_a_network_or_cache_client(self):
        source={'id':'fixture::required','url':self.source,'markdown':self.markdown}
        with patch('required_downloads.bundled_manifest',return_value=self.manager.items),patch('required_downloads.default_manager',side_effect=AssertionError('Source read must stay independent of transfer state')):
            self.assertEqual(attach_statement(source)['attachments'][self.url]['data'],'/api/required-downloads/'+self.sha)

    def test_only_manually_reviewed_mandatory_zip_inputs_can_use_this_category(self):
        for key,value in [('manuallyReviewed',False),('optional',True),('requiredForStatement',False),('problemType','standard'),('mime','image/png'),('role','optional-tests'),('bytes',MAX_DOWNLOAD+1)]:
            item=copy.deepcopy(self.item);item[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_manifest({'schema':1,'downloads':[item]})

    def test_ordinary_asset_size_policy_is_unchanged(self):
        self.assertEqual(MAX_ASSET,32*1024*1024)
        with self.assertRaises(ValueError):validate_reference(self.sha,'application/zip',MAX_ASSET+1,PUBLIC_ROOT+self.sha+'.bin')

    def test_non_zip_bytes_never_become_a_complete_cache_even_with_reviewed_hashes(self):
        self.raw=b'nope'+self.raw[4:];self.sha=hashlib.sha256(self.raw).hexdigest()
        item=copy.deepcopy(self.item);item['sha256']=self.sha
        item['chunkSha256']=[hashlib.sha256(self.raw[i:i+CHUNK_BYTES]).hexdigest()for i in range(0,len(self.raw),CHUNK_BYTES)]
        self.manager.items={self.sha:item}
        folder=self.root/'cache';folder.mkdir();(folder/(self.sha+'.zip')).write_bytes(self.raw)
        with self.assertRaisesRegex(ValueError,'not a ZIP'):self.download()
        self.assertFalse((folder/(self.sha+'.zip')).exists())
        self.assertEqual((folder/(self.sha+'.part')).stat().st_size,0)
        self.assertEqual(self.manager.status(self.sha)['verifiedBytes'],0)

    def test_deployment_verifier_requires_origin_transfer_and_checks_offline_cache(self):
        import sys
        scripts=Path(__file__).resolve().parents[1]/'scripts'
        with patch.object(sys,'path',[str(scripts),*sys.path]):
            from verify_required_download_distribution import verify
        with patch('verify_required_download_distribution.RequiredDownloads',return_value=self.manager):
            result=verify(self.manager.cache_root)
            self.assertEqual(result['archives'][0]['sha256'],self.sha)
            self.assertTrue(result['archives'][0]['networkDisabledOfflineReplayVerified'])
            self.assertFalse(result['catalogueRetirementChanged'])
            self.assertEqual(len(self.requests),1)
            with self.assertRaisesRegex(ValueError,'contact the distribution origin'):verify(self.manager.cache_root)

    def test_range_parser_rejects_multiple_ranges_and_out_of_bounds(self):
        self.assertEqual(byte_range('bytes=5-',10),(5,9,True))
        for value in ['bytes=0-1,3-4','bytes=10-','bytes=-5','bytes=7-3','https://evil.example']:
            with self.assertRaises(ValueError):byte_range(value,10)


class RequiredDownloadApiTests(unittest.TestCase):
    tearDown=account_fixtures.AccountTests.tearDown
    start=account_fixtures.AccountTests.start
    stop=account_fixtures.AccountTests.stop
    call=account_fixtures.AccountTests.call
    signup=account_fixtures.AccountTests.signup
    login=account_fixtures.AccountTests.login

    def setUp(self):
        account_fixtures.AccountTests.setUp(self)
        # Reuse only the disposable synthetic archive builder, not its tests.
        self.fixture=RequiredDownloadTests('test_ordinary_asset_size_policy_is_unchanged')
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.server.required_downloads=self.fixture.manager

    def download_request(self,method='GET',headers=None,path=None):
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=15)
        connection.request(method,path or'/api/required-downloads/'+self.fixture.sha,
                           headers={'X-TB-Token':self.server.store.token,**(headers or{})})
        response=connection.getresponse();result=response.status,dict(response.headers),response.read();connection.close()
        return result

    def test_binary_route_keeps_account_origin_identity_and_range_guards(self):
        self.assertEqual(self.download_request()[0],401)
        status,_,body=self.download_request('HEAD');self.assertEqual(status,401);self.assertEqual(body,b'')
        self.assertEqual(self.signup()[0],200);self.assertEqual(self.login()[0],200)
        status,headers,body=self.download_request('HEAD');self.assertEqual(status,200);self.assertEqual(body,b'')
        self.assertEqual(headers['Content-Disposition'],'attachment; filename="down.zip"')
        self.assertEqual(self.download_request()[2],self.fixture.raw)
        status,headers,body=self.download_request(headers={'Range':'bytes=123456-'})
        self.assertEqual(status,206);self.assertEqual(body,self.fixture.raw[123456:])
        self.assertEqual(headers['Content-Range'],f'bytes 123456-{len(self.fixture.raw)-1}/{len(self.fixture.raw)}')
        requests=len(self.fixture.requests)
        self.assertEqual(self.download_request(path='/api/required-downloads/'+'a'*64)[0],404)
        status,_,body=self.download_request('HEAD',path='/api/required-downloads/'+'a'*64);self.assertEqual(status,404);self.assertEqual(body,b'')
        self.assertEqual(self.download_request(path='/api/required-downloads/'+self.fixture.sha+'?url=https://untrusted.example')[0],404)
        self.assertEqual(self.download_request(headers={'Host':'untrusted.example'})[0],403)
        self.assertEqual(self.download_request(headers={'Range':'bytes=0-1,3-4'})[0],416)
        self.assertEqual(len(self.fixture.requests),requests)
        status,value=self.call('/api/required-downloads/'+self.fixture.sha+'/status')
        self.assertEqual(status,200);self.assertTrue(value['cached']);self.assertEqual(value['verifiedBytes'],len(self.fixture.raw))

    def test_public_input_transfer_does_not_hold_the_account_switch_barrier(self):
        self.assertEqual(self.signup()[0],200);self.assertEqual(self.login()[0],200)
        entered,release=threading.Event(),threading.Event();original=self.fixture.manager._open
        def blocked(*args):
            entered.set()
            if not release.wait(8):raise OSError('Synthetic transfer was not released')
            return original(*args)
        with patch.object(self.fixture.manager,'_open',side_effect=blocked),ThreadPoolExecutor(2)as pool:
            download=pool.submit(self.download_request)
            try:
                self.assertTrue(entered.wait(3))
                self.assertEqual(pool.submit(self.call,'/api/account/logout',{}).result(timeout=3)[0],200)
            finally:release.set()
            self.assertEqual(download.result(timeout=5)[2],self.fixture.raw)


if __name__=='__main__':unittest.main()
