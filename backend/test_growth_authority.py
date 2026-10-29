"""Confirmed growth ordering without another full insights pass during claims."""
import unittest
import test_training as fixtures

class GrowthAuthorityTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown
    accept=fixtures.ServiceTests.accept

    def test_committed_claim_and_read_have_same_owner_ordered_versions(self):
        self.accept()
        initial=self.service.insights()['growth']
        task=next(task for task in self.service.daily_tasks()['tasks'] if task['completed'] and not task['claimed'])
        result=self.service.claim_daily_task(task['id'])
        self.assertEqual(result['growthAuthority']['owner'],initial['authority']['owner'])
        self.assertEqual(result['growthAuthority']['epoch'],initial['authority']['epoch'])
        self.assertGreater(result['growthAuthority']['revision'],initial['authority']['revision'])
        self.assertEqual(result['confirmedMissionXp'],result['awardedXp'])
        repeated=self.service.claim_daily_task(task['id'])
        self.assertEqual(repeated['awardedXp'],0)
        self.assertEqual(repeated['confirmedMissionXp'],result['confirmedMissionXp'])
        refreshed=self.service.insights()['growth']
        self.assertGreater(refreshed['authority']['revision'],repeated['growthAuthority']['revision'])
        self.assertEqual(refreshed['totalXp']-initial['totalXp'],result['awardedXp']+refreshed['achievementXp']-initial['achievementXp'])

if __name__=='__main__':unittest.main()
