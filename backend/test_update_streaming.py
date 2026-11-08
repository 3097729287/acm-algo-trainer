"""Real byte progress and verified resume after an interrupted connection."""
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from software_updates import SoftwareUpdates,DOMESTIC_ROOT

DATA=bytes(range(256))*1000


class Response(io.BytesIO):
    def __init__(self,data,*,status=200,headers=None,before_read=None,fail_after=None):
        super().__init__(data);self.status=status;self.headers=headers or {};self.before_read=before_read;self.fail_after=fail_after

    def read1(self,size):
        if self.before_read:self.before_read(size)
        if self.fail_after is not None and self.tell()>=self.fail_after:raise ConnectionResetError('isolated interrupted response')
        return super().read(min(size,16384))


class UpdateStreamingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.opener=Mock()
        self.service=SoftwareUpdates(self.root/'state',current='1.6.6',opener=self.opener,offline=False)
        self.service.release={'kind':'delta','version':'1.6.8','name':'ToBe-Update-1.6.6-to-1.6.8-win64.zip',
            'url':DOMESTIC_ROOT+'/assets/1.6.8/ToBe-Update-1.6.6-to-1.6.8-win64.zip','size':len(DATA),
            'sha256':hashlib.sha256(DATA).hexdigest(),'notes':'','releaseUrl':DOMESTIC_ROOT+'/stable/release-1.6.8.html'}

    def assert_ready(self):
        self.assertEqual(self.service.snapshot()['status'],'ready')
        self.assertEqual(self.service.installer.read_bytes(),DATA)

    def test_first_real_chunk_updates_progress_before_a_megabyte_arrives(self):
        seen=[]
        def observe(limit):seen.append((limit,self.service.snapshot()['downloadedBytes']))
        self.opener.open.return_value=Response(DATA,before_read=observe)
        self.service._download();self.assert_ready()
        self.assertEqual(seen[1],(65536,16384));self.assertTrue(all(a[1]<=b[1] for a,b in zip(seen,seen[1:])))

    def test_interruption_resumes_at_exact_committed_offset_and_verifies_full_hash(self):
        def open_response(request,**kwargs):
            value=request.get_header('Range')
            if self.opener.open.call_count==1:
                self.assertIsNone(value);return Response(DATA,fail_after=32768)
            self.assertEqual(value,'bytes=32768-')
            return Response(DATA[32768:],status=206,headers={'Content-Range':f'bytes 32768-{len(DATA)-1}/{len(DATA)}'})
        self.opener.open.side_effect=open_response
        self.service._download();self.assert_ready();self.assertEqual(self.opener.open.call_count,2)

    def test_server_ignoring_range_restarts_without_duplicate_or_omitted_bytes(self):
        self.opener.open.side_effect=[Response(DATA,fail_after=32768),Response(DATA)]
        self.service._download();self.assert_ready()
        self.assertEqual(self.opener.open.call_args_list[1].args[0].get_header('Range'),'bytes=32768-')

    def test_restart_reuses_only_partial_bytes_bound_to_this_exact_asset(self):
        folder=self.root/'cache/updates';folder.mkdir(parents=True)
        partial=folder/Path(self.service.release['name']).with_suffix('.download')
        partial.write_bytes(DATA[:49152])
        partial.with_name(partial.name+'.json').write_text(json.dumps({k:self.service.release[k] for k in ('url','size','sha256')}),encoding='utf-8')
        self.opener.open.return_value=Response(DATA[49152:],status=206,headers={'Content-Range':f'bytes 49152-{len(DATA)-1}/{len(DATA)}'})
        self.service._download();self.assert_ready()
        self.assertEqual(self.opener.open.call_args.args[0].get_header('Range'),'bytes=49152-')

    def test_wrong_response_range_is_rejected_before_appending(self):
        self.opener.open.side_effect=[Response(DATA,fail_after=32768),Response(DATA,status=206,headers={'Content-Range':f'bytes 0-{len(DATA)-1}/{len(DATA)}'})]
        self.service._download();self.assertEqual(self.service.snapshot()['status'],'error');self.assertIsNone(self.service.installer)
        self.assertEqual(next((self.root/'cache/updates').glob('*.failed-*')).read_bytes(),DATA[:32768])

    def test_same_size_corrupt_download_cannot_become_an_installer(self):
        self.opener.open.return_value=Response(b'x'*len(DATA))
        self.service._download();self.assertEqual(self.service.snapshot()['status'],'error');self.assertIsNone(self.service.installer)


if __name__=='__main__':unittest.main()
