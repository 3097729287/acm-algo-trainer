"""Network interruptions retry; corrupt public bytes never receive a proof."""
from contextlib import closing
import hashlib,json,sqlite3,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'backend'),str(ROOT/'backend/common')]
from verify_public_assets import verify

class Response:
    status=200
    def __init__(self,raw,fail=False):self.raw=raw;self.fail=fail;self.closed=False
    def __enter__(self):return self
    def __exit__(self,*args):self.closed=True
    def read(self,count):
        if self.fail:self.fail=False;raise FileNotFoundError(2,'isolated interrupted SSL read fixture')
        value,self.raw=self.raw[:count],self.raw[count:];return value

class PublicAssetVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.raw=b'%PDF-public-verification-fixture';self.digest=hashlib.sha256(self.raw).hexdigest();self.library=self.root/'library.sqlite3'
        with closing(sqlite3.connect(self.library)) as db,db:
            db.execute('CREATE TABLE remote_statement_assets(sha256 TEXT,mime TEXT,bytes INTEGER,url TEXT)')
            db.execute('INSERT INTO remote_statement_assets VALUES(?,?,?,?)',(self.digest,'application/pdf',len(self.raw),'https://47.82.84.74/updates/library-assets/'+self.digest+'.bin'))
    def test_interrupted_read_closes_response_and_verifies_an_entire_fresh_retry(self):
        first=Response(self.raw,fail=True);second=Response(self.raw);output=self.root/'verified.json'
        with patch('leaderboard.service_opener') as opener,patch('verify_public_assets.time.sleep') as delay:
            opener.return_value.open.side_effect=[first,second]
            self.assertEqual(verify(self.library,output,workers=1),1)
            self.assertEqual(opener.return_value.open.call_count,2);delay.assert_called_once_with(1)
        self.assertTrue(first.closed and second.closed)
        proof=json.loads(output.read_text('utf8'));self.assertEqual(proof['verifiedSha256'],[self.digest])
        self.assertEqual(proof['librarySha256'],hashlib.sha256(self.library.read_bytes()).hexdigest())
    def test_wrong_digest_is_not_retried_and_cannot_issue_a_verification_receipt(self):
        output=self.root/'verified.json'
        with patch('leaderboard.service_opener') as opener,patch('verify_public_assets.time.sleep') as delay:
            opener.return_value.open.return_value=Response(b'!'+self.raw[1:])
            with self.assertRaisesRegex(ValueError,'checksum'):verify(self.library,output,workers=1)
            self.assertEqual(opener.return_value.open.call_count,1);delay.assert_not_called()
        self.assertFalse(output.exists())
if __name__=='__main__':unittest.main()
