import unittest
import test_training as fixtures
from official_verdict import codeforces_detail


class OfficialDetailTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown

    def test_codeforces_failure_index_requires_actual_api_fields(self):
        self.assertEqual(codeforces_detail({'verdict':'WRONG_ANSWER','testset':'TESTS','passedTestCount':0}),'Wrong answer on test 1')
        self.assertEqual(codeforces_detail({'verdict':'TIME_LIMIT_EXCEEDED','testset':'PRETESTS','passedTestCount':2}),'Time limit exceeded on pretest 3')
        for value in ({'verdict':'WRONG_ANSWER'}, {'verdict':'WRONG_ANSWER','testset':'TESTS','passedTestCount':True}):
            self.assertEqual(codeforces_detail(value),'Wrong answer')
        self.assertEqual(codeforces_detail({'verdict':'COMPILATION_ERROR','testset':'TESTS','passedTestCount':0}),'Compilation error')

    def test_detail_backfills_existing_receipt_without_replacing_code(self):
        session={'id':'fixture::A','url':self.assets.problem('fixture::A')['url'],'code':'my private original code'}
        receipt={'status':'finished','verdict':'WA','submissionId':'12345'}
        initial=self.service.record_official(session,receipt)
        result=self.service.record_official({**session,'code':''},{**receipt,'verdictDetail':'Wrong answer on test 1'})
        self.assertEqual(result['id'],initial['id']);self.assertEqual(result['code'],session['code'])
        self.assertEqual(result['verdictDetail'],'Wrong answer on test 1')
        compact=self.service.submissions(compact=True)['submissions'][0]
        self.assertEqual(compact['verdictDetail'],'Wrong answer on test 1');self.assertNotIn('code',compact)
        self.assertEqual(self.service.connection.execute('SELECT COUNT(*) FROM submissions').fetchone()[0],1)


if __name__=='__main__':unittest.main()
