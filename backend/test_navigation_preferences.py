import unittest
from unittest.mock import Mock
from preferences import save_preferences,merge_onboarding_unlocked_pages,merge_level_notices
from training import ServiceError

class NavigationPreferencesTests(unittest.TestCase):
    def test_essential_unknown_and_malformed_hidden_pages_rejected_before_write(self):
        for value in (['mine'],['records'],['settings'],['unknown'],'library',[True],['library']*20):
            with self.subTest(value=value),self.assertRaises(ServiceError):
                save_preferences(Mock(),{'preferences':{'hiddenNavPages':value}})
    def test_guide_acknowledgements_merge_only_known_pages(self):
        self.assertEqual(merge_onboarding_unlocked_pages(['mine','paths'],['library','paths','bad',None],None),['library','mine','paths'])
    def test_wiki_and_duel_settings_roundtrip_and_keep_acknowledgements(self):
        from test_training import ServiceTests
        from preferences import read_preferences
        fixture=ServiceTests();fixture.setUp()
        try:
            training=fixture.service
            save_preferences(training,{'preferences':{'hiddenNavPages':['wiki','duel'],'onboardingUnlockedPages':['wiki','duel'],'pageOpacities':{'wiki':80,'duel':90}}})
            saved=read_preferences(training)['preferences']
            self.assertEqual(saved['hiddenNavPages'],['wiki','duel'])
            self.assertEqual(saved['pageOpacities'],{'wiki':80,'duel':90})
            save_preferences(training,{'preferences':{'hiddenNavPages':[],'onboardingUnlockedPages':['library']}})
            self.assertEqual(read_preferences(training)['preferences']['onboardingUnlockedPages'],['duel','library','wiki'])
            self.assertEqual(merge_onboarding_unlocked_pages(['wiki'],['duel','unknown']),['duel','wiki'])
        finally:fixture.tearDown()

    def test_pending_level_is_preserved_until_actually_seen(self):
        pending={'levelNoticeVersion':1,'levelNoticeSeen':3,'levelNoticePending':5}
        shown={'levelNoticeVersion':1,'levelNoticeSeen':4,'levelNoticePending':0}
        self.assertEqual(merge_level_notices(pending,shown),{'levelNoticeVersion':1,'levelNoticeSeen':4,'levelNoticePending':5})
        self.assertEqual(merge_level_notices(pending,{'levelNoticeVersion':1,'levelNoticeSeen':5})['levelNoticePending'],0)
    def test_invalid_notice_numbers_are_rejected_before_write(self):
        for field,value in (('levelNoticeVersion',2),('levelNoticeVersion',True),('levelNoticeSeen',True),('levelNoticeSeen',101),('levelNoticePending',-1)):
            with self.subTest(field=field,value=value),self.assertRaises(ServiceError):save_preferences(Mock(),{'preferences':{field:value}})

if __name__=='__main__':unittest.main()
