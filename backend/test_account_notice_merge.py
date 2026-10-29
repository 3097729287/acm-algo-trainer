"""Cross-device level notices retain confirmed unseen milestones and acknowledgements."""
import json
import unittest
from account_sync import TABLES,merge_states

def state(ui,stamp):
    tables={name:[] for name in TABLES}
    tables['account_preferences']=[{'key':'ui','value':json.dumps(ui),'updated_at':stamp}]
    return {'tables':tables,'publicAccounts':{}}

class LevelNoticeMergeTests(unittest.TestCase):
    def merged(self,left,right):
        answer=merge_states(state(left,'2026-10-29T00:00:00Z'),state(right,'2026-10-29T01:00:00Z'))
        return json.loads(answer['tables']['account_preferences'][0]['value'])

    def test_unshown_confirmed_checkpoint_survives_a_later_preference_write(self):
        merged=self.merged({'levelNoticeVersion':1,'levelNoticeSeen':3,'levelNoticePending':5},
                           {'levelNoticeVersion':1,'levelNoticeSeen':4,'levelNoticePending':0})
        self.assertEqual((merged['levelNoticeVersion'],merged['levelNoticeSeen'],merged['levelNoticePending']),(1,4,5))

    def test_seen_checkpoint_never_reopens_from_a_late_device(self):
        merged=self.merged({'levelNoticeVersion':1,'levelNoticeSeen':7,'levelNoticePending':0},
                           {'levelNoticeVersion':1,'levelNoticeSeen':3,'levelNoticePending':5})
        self.assertEqual((merged['levelNoticeSeen'],merged['levelNoticePending']),(7,0))

    def test_malformed_checkpoint_does_not_become_a_false_level(self):
        merged=self.merged({'levelNoticeVersion':1,'levelNoticeSeen':4,'levelNoticePending':5},
                           {'levelNoticeVersion':1,'levelNoticeSeen':True,'levelNoticePending':101})
        self.assertEqual((merged['levelNoticeSeen'],merged['levelNoticePending']),(4,5))

if __name__=='__main__':unittest.main()
