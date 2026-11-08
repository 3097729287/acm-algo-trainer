import time,unittest
from types import SimpleNamespace
from accounts import Accounts

class RankingLeaseTests(unittest.TestCase):
    def test_pending_private_merge_does_not_hide_a_valid_owners_ranking_session(self):
        account=SimpleNamespace(session={'userId':'owner','token':'opaque fixture','endpoint':'https://example.com','expiresAt':time.time()+60},state_sync=SimpleNamespace(needs_reconnect=True))
        self.assertEqual(Accounts.credentials(account,'owner')['auth_token'],'opaque fixture')
        self.assertIsNone(Accounts.credentials(account,'another-owner'))
        account.session['expiresAt']=time.time()-1
        self.assertIsNone(Accounts.credentials(account,'owner'))
        account.session=None
        self.assertIsNone(Accounts.credentials(account,'owner'))

if __name__=='__main__':unittest.main()
