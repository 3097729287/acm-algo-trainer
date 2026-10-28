import unittest
from official_bridge import submission_target, page_source
from browser_login_memory import site_cookie


class QojBoundaryTests(unittest.TestCase):
    def test_only_normal_first_party_global_problem_pages(self):
        target=submission_target('https://qoj.ac/problem/15032')
        self.assertEqual((target['platform'],target['problem'],target['url'],target['loginUrl']),
                         ('QOJ','15032','https://qoj.ac/problem/15032#tab-submit','https://qoj.ac/login'))
        for value in ('https://contest.ucup.ac/problem/15032','https://jiang.ly/problem/15032',
                      'https://qoj.ac/contest/2693/problem/1','https://qoj.ac.evil.com/problem/15032',
                      'https://qoj.ac/problem/15032?contest_id=2693','http://qoj.ac/problem/15032',
                      'https://qoj.ac:444/problem/15032','https://x@y@qoj.ac/problem/15032'):
            with self.assertRaises(ValueError,msg=value):submission_target(value)

    def test_scoped_adapter_is_bundled_and_cookies_remain_first_party(self):
        source=page_source()
        self.assertNotIn('QOJ_ADAPTER',source)
        self.assertIn("if(ctx.platform==='QOJ')",source)
        self.assertIn('#form-answer',source)
        cookie={'name':'fixture','value':'synthetic','domain':'.qoj.ac','path':'/','secure':True,'httpOnly':True}
        self.assertIsNotNone(site_cookie(cookie))
        self.assertIsNone(site_cookie({**cookie,'domain':'qoj.ac.evil.com'}))
        self.assertIsNone(site_cookie({**cookie,'domain':'jiang.ly'}))


if __name__=='__main__':unittest.main()
