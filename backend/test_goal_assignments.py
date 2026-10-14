"""Independent daily goal allocation and legacy upgrade, using disposable state."""
import json
import unittest
from types import SimpleNamespace
import test_training as fixtures
from goals import Goals
from training import TrainingService


class GoalAssignmentTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown
    accept = fixtures.ServiceTests.accept
    completed = fixtures.ServiceTests.completed

    def plans(self):
        planner = Goals(self.service)
        for title in ('第一目标', '第二目标'):
            planner.save({'title': title, 'deadline': '2026-10-09', 'totalProblems': 4})
            self.clock.advance(seconds=1)
        return planner.list()['goals']

    def test_one_goal_finishing_keeps_other_tasks_and_target_through_restart(self):
        first, second = self.plans()
        first_ids = [p['id'] for p in first['dailyTask']['problems']]
        second_ids = [p['id'] for p in second['dailyTask']['problems']]
        self.assertEqual([first['dailyTask']['target'], second['dailyTask']['target']], [2, 2])
        self.assertTrue(set(first_ids).isdisjoint(second_ids))
        self.assertEqual(len(first_ids + second_ids), 4)
        for identity in second_ids:
            self.clock.advance(seconds=1)
            self.accept(identity)
        for restarted in (False, True):
            if restarted:
                self.service.close()
                self.service = TrainingService(self.library, self.db, self.assets, self.judge, self.clock, self.root/'backups')
            goals = {g['id']: g for g in Goals(self.service).list()['goals']}
            self.assertEqual(goals[first['id']]['dailyTask']['progress'], 0)
            self.assertFalse(goals[first['id']]['dailyTask']['completed'])
            self.assertEqual([p['id'] for p in goals[first['id']]['dailyTask']['problems']], first_ids)
            self.assertEqual(goals[second['id']]['dailyTask']['progress'], 2)
            self.assertTrue(goals[second['id']]['dailyTask']['completed'])
            self.assertEqual(goals[second['id']]['dailyTask']['problems'], [])
        self.accept(first_ids[0], verdict='WA')
        self.completed(first_ids[0])  # Local AC is not a completed official task.
        self.assertEqual(Goals(self.service).list()['goals'][0]['dailyTask']['progress'], 0)
        self.accept(first_ids[0]); self.accept(first_ids[0])
        self.assertEqual(Goals(self.service).list()['goals'][0]['dailyTask']['progress'], 1)

    def test_existing_legacy_empty_selection_is_repaired_once_without_undoing_removal(self):
        first, second = self.plans()
        # Simulate v1.0.13's all-AC counter having cleared the first goal.
        self.service.connection.execute('UPDATE goal_daily_assignments SET ids=?,target=NULL WHERE goal_id=?', ('[]', first['id']))
        for row in second['dailyTask']['problems']:
            self.clock.advance(seconds=1); self.accept(row['id'])
        self.service.workspace()
        goal = next(g for g in Goals(self.service).list()['goals'] if g['id'] == first['id'])
        self.assertEqual(goal['dailyTask']['progress'], 0)
        self.assertEqual(len(goal['dailyTask']['problems']), 2)
        self.assertEqual(goal['dailyTask']['target'], 2)
        self.service.clear_training()
        self.assertEqual(self.service.workspace()['training'], [])
        self.assertEqual(Goals(self.service).list()['goals'][0]['dailyTask'], goal['dailyTask'])

    def test_legacy_shared_ids_and_url_aliases_belong_to_only_one_daily_goal(self):
        self.library.rows[-1]['url'] = self.library.rows[0]['url'] = 'https://codeforces.com/contest/123/problem/A'
        first, second = self.plans()
        duplicated = json.dumps([p['id'] for p in first['dailyTask']['problems']])
        self.service.connection.execute('UPDATE goal_daily_assignments SET ids=?,target=NULL', (duplicated,))
        goals = Goals(self.service).list(assign=True)['goals']
        urls = {row['id']: row.get('url', row['id']) for row in self.library.rows}
        keys = [{urls[p['id']] for p in g['dailyTask']['problems']} for g in goals]
        self.assertEqual([len(k) for k in keys], [2, 2])
        self.assertFalse(keys[0] & keys[1])
        for row in goals[0]['dailyTask']['problems']:
            self.clock.advance(seconds=1); self.accept(row['id'])
        self.assertEqual([g['dailyTask']['progress'] for g in Goals(self.service).list()['goals']], [2, 0])

    def test_next_day_allocations_exclude_accepted_and_still_do_not_overlap(self):
        goals = self.plans()
        solved = goals[1]['dailyTask']['problems'][0]['id']
        self.clock.advance(seconds=1); self.accept(solved)
        self.clock.advance(days=1)
        goals = Goals(self.service).list(assign=True)['goals']
        ids = [[p['id'] for p in g['dailyTask']['problems']] for g in goals]
        self.assertFalse(set(ids[0]) & set(ids[1]))
        self.assertNotIn(solved, ids[0] + ids[1])
        self.assertEqual([g['dailyTask']['progress'] for g in goals], [0, 0])

    def test_bundled_roster_replacing_remote_ids_keeps_completed_daily_selection(self):
        for index,row in enumerate(self.library.rows):
            row.update(url=f'https://codeforces.com/contest/123/problem/{chr(65+index)}',source='remote')
        first,second=self.plans()
        for row in second['dailyTask']['problems']:
            self.clock.advance(seconds=1);self.accept(row['id'])
        before=[tuple(row) for row in self.service.connection.execute('SELECT * FROM goal_daily_assignments ORDER BY goal_id')]
        old=[dict(row) for row in self.library.rows]
        self.library.rows=[{**row,'id':'bundled-'+row['id'],'source':'archive'} for row in old]
        self.library.extensions=SimpleNamespace(rows=lambda:old,snapshot=lambda:{})
        for _ in range(2):
            goals=Goals(self.service).list(assign=True)['goals']
            self.assertEqual([g['dailyTask']['progress'] for g in goals],[0,2])
            self.assertTrue(goals[1]['dailyTask']['completed'])
            self.assertEqual(goals[0]['dailyTask']['problems'],first['dailyTask']['problems'])
        self.assertEqual([tuple(row) for row in self.service.connection.execute('SELECT * FROM goal_daily_assignments ORDER BY goal_id')],before)


if __name__ == '__main__':
    unittest.main()
