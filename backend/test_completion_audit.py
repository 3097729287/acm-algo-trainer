"""Missing real statements stay gaps; reviewed nonproblem IDs stay in history."""
from contextlib import closing
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('reviewed_completion_audit',ROOT/'scripts/completion_audit.py')
completion=importlib.util.module_from_spec(spec)
spec.loader.exec_module(completion)


class CompletionAuditTests(unittest.TestCase):
    def reference(self):
        return {'catalogHidden':True,'catalogStatementReady':False,'catalogReplayReady':False,'contestRoster':False,
            'statementRetired':True,'statementRetirementPolicy':'verified-nonproblem-attachment-v1',
            'catalogEntryKind':'reference-attachments','statementRetirementReason':'Public source has only two algorithm lectures, no task or input/output.'}

    def test_an_empty_or_retired_problem_is_not_automatically_a_nonproblem(self):
        self.assertTrue(completion.verified_nonproblem(self.reference()))
        for changes in ({'statementRetirementPolicy':'public-statement-audit-v1'},
                        {'catalogReplayReady':True},{'contestRoster':True},
                        {'catalogEntryKind':'standard'},{'statementRetirementReason':''}):
            with self.subTest(changes=changes):self.assertFalse(completion.verified_nonproblem(dict(self.reference(),**changes)))
        self.assertFalse(completion.verified_nonproblem({'title':'wqs 二分附件'}))

    def test_audit_keeps_real_gaps_and_original_identity_rows_separate(self):
        with tempfile.TemporaryDirectory(prefix='tb-completion-audit-') as temporary:
            root=Path(temporary);(root/'data/library').mkdir(parents=True)
            reference=self.reference();artifact=dict(reference,catalogEntryKind='import-artifact',statementRetirementPolicy='verified-nonproblem-roster-v1')
            values=[('real-complete',{'tags':['模拟'],'knowledge':'模拟','difficulty':800}),
                    ('real-missing',{'statementRetired':True,'statementRetirementPolicy':'public-statement-audit-v1'}),
                    ('reference',reference),('artifact',artifact)]
            rows=[{'id':identity,'url':'https://example.invalid/'+identity,'encoded':dict(encoded,title=identity)} for identity,encoded in values]
            (root/'data/library/problems.json').write_text(json.dumps(rows),encoding='utf8')
            library=root/'public.sqlite3'
            with closing(sqlite3.connect(library)) as db:
                db.execute('CREATE TABLE problems(id TEXT)');db.executemany('INSERT INTO problems VALUES(?)',[(r['id'],) for r in rows])
                db.execute('CREATE TABLE statements(problem_id TEXT,content TEXT)')
                statement={'markdown':'## 题目描述\n\n输出一个整数。','samples':[{'input':'1','output':'1'}],'integrity':{'status':'complete'}}
                db.execute('INSERT INTO statements VALUES(?,?)',('real-complete',json.dumps(statement)))
                db.commit()
            with patch.object(completion,'ROOT',root):result=completion.audit(library,root/'audit')
            self.assertEqual(result['problems'],4)
            self.assertEqual(result['publicProblemEntries'],2)
            self.assertEqual(result['verifiedNonproblemEntries'],2)
            self.assertEqual(result['completeOriginals'],1)
            self.assertEqual(result['gaps']['originals'],1)
            self.assertEqual([x['id'] for x in json.loads((root/'audit/originals.json').read_text())],['real-missing'])
            self.assertEqual({x['id'] for x in json.loads((root/'audit/nonproblems.json').read_text())},{'reference','artifact'})
            with closing(sqlite3.connect(library)) as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM problems').fetchone()[0],4)


if __name__=='__main__':unittest.main()
