import json
import unittest
import test_training as fixtures


class ContestTrainingEditsTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown
    contest=fixtures.ServiceTests.contest

    def test_reading_does_not_join_but_editing_even_to_empty_does(self):
        contest=self.contest()
        first,second=contest['slots'][:2]
        self.assertEqual(self.service.workspace()['training'],[])
        self.service.problem(first['id'],contest['id'])
        self.service.problem(second['id'],contest['id'])
        self.assertEqual(self.service.workspace()['training'],[])
        self.service.save_draft(first['id'],'// changed in contest',contest['id'])
        self.service.save_draft(first['id'],'',contest['id'])
        self.assertEqual([row['id'] for row in self.service.workspace()['training']],[first['id']])
        finished=self.service.finish_contest(contest['id'])
        self.assertEqual(len(finished['contest']['slots']),len(contest['slots']))
        self.assertEqual([row['id'] for row in finished['workspace']['training']],[first['id']])
        self.assertEqual(finished['workspace']['summary']['due'],1)

    def test_legacy_auto_joins_retire_only_with_proof_and_keep_manual_drafts_and_history(self):
        self.service.start_training('fixture::A')
        contest=self.contest()
        by_id={slot['id']:slot for slot in contest['slots']}
        changed=next(identity for identity in by_id if identity!='fixture::A')
        self.service.save_draft(changed,'// keep my contest draft',contest['id'])
        row=self.service.connection.execute('SELECT config FROM contests WHERE id=?',(contest['id'],)).fetchone()
        config=json.loads(row[0]);config.pop('editedTrainingOnly')
        with self.service._write() as db:
            db.execute('UPDATE contests SET config=? WHERE id=?',(json.dumps(config),contest['id']))
            for slot in contest['slots']:self.service._activate(db,slot['id'],contest['startedAt'])
            db.execute("DELETE FROM account_preferences WHERE key='contest-edited-training-v1'")
        self.service._contest_entries_checked=False
        workspace=self.service.workspace()
        self.assertEqual({row['id'] for row in workspace['training']},{'fixture::A',changed})
        self.assertEqual(self.service.problem(changed,contest['id'])['draft'],'// keep my contest draft')
        self.assertEqual(len(workspace['activeContest']['slots']),len(contest['slots']))
        self.assertEqual(self.service.connection.execute('SELECT COUNT(*) FROM training').fetchone()[0],len(set(by_id)|{'fixture::A'}))
        self.assertEqual({row['id'] for row in self.service.workspace()['training']},{'fixture::A',changed})


if __name__=='__main__':unittest.main()
