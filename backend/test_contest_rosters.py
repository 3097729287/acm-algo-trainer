import unittest
from contest_rosters import annotate

class ContestRosterTests(unittest.TestCase):
    def test_reviewed_complete_div3_roster_only_adds_original_count_evidence(self):
        for index in 'ABCDEFG':
            row={'id':'remote:codeforces:2278::'+index,'url':'https://codeforces.com/contest/2278/problem/'+index,'difficulty':None}
            value=annotate(row)
            self.assertEqual(value['contestProblemCount'],7)
            self.assertEqual(value['id'],row['id']);self.assertIsNone(value['difficulty'])
            self.assertNotIn('contestProblemCount',row)
        unknown={'url':'https://codeforces.com/contest/2278/problem/H'}
        self.assertEqual(annotate(unknown),unknown)
