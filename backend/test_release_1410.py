"""Regressions for uncertainty, translation spans, imports and curated replays."""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from rating_evidence import evidence
from translation import protect
from integrations import PublicClient
from graph_lab import courses, replay_events, replay_rows
from contest_imports import roster


class Release1410Tests(unittest.TestCase):
    def test_math_protection_does_not_swallow_adjacent_prose(self):
        source='Choose $$$a$$$ employees. Count $$$b$$$ groups.'
        masked, tokens=protect(source)
        self.assertIn('employees. Count',masked)
        self.assertEqual(sorted(tokens.values()),['$$$a$$$','$$$b$$$'])

    def test_uncertain_rating_is_not_exact_evidence(self):
        exact=evidence(dict(difficulty=2000,platform='Codeforces',difficultySource='Codeforces 官方 rating'))
        estimated=evidence(dict(difficulty=2000,platform='AtCoder',difficultySource='AtCoder Problems'))
        self.assertEqual((exact['lower'],exact['upper'],exact['weight']),(2000,2000,1))
        self.assertLess(estimated['lower'],2000)
        self.assertLess(estimated['weight'],1)
        self.assertFalse(evidence(dict(difficulty=None))['known'])

    def test_receipt_refresh_bypasses_ttl_and_keeps_owner_filter(self):
        reads=[]
        def transport(url,headers):
            reads.append(url)
            return json.dumps({'owner':[len(reads)],'other':['private']}).encode(),None
        with tempfile.TemporaryDirectory() as directory:
            client=PublicClient(directory,transport=transport,spacing=0)
            url='https://ac.nowcoder.com/acm/contest/rank/submit-list'
            self.assertEqual(client.owner_json(url,'me',lambda p:p['owner']),[1])
            self.assertEqual(client.owner_json(url,'me',lambda p:p['owner']),[2])
            for path in Path(directory).rglob('*.json'):
                self.assertNotIn('private',path.read_text())

    def test_replay_groups_preserve_five_original_identities(self):
        self.assertEqual(set(courses()), {'sequence-0','sequence-1','sequence-2','bfs','dfs','dsu','dijkstra','sorting-basics','divide-sort','bucket-sort'})
        rows=[dict(id=p['url'],url=p['url']) for c in courses().values() for p in c['problems']]
        self.assertTrue(all(event['complete'] for event in replay_events(rows)))
        for course in courses().values():
            selected=replay_rows('算法实验室 · '+course['title'],rows)
            self.assertEqual(len(selected),5)
            self.assertEqual(len({r['id'] for r in selected}),5)

    def test_contest_points_are_not_cf_rating(self):
        client=SimpleNamespace()
        payload={'contest':{'id':726517,'name':'Fixture'},'problems':[{'index':'A','name':'A','points':2000}]}
        with patch('public_platforms.cf_roster',return_value=payload):
            rows=roster(client,dict(id='codeforces:726517',platform='codeforces',title='Fixture',url='https://codeforces.com/gym/726517'))
        self.assertIsNone(rows[0]['difficulty'])
        self.assertEqual(rows[0]['contestProblemCount'],1)

    def test_backfill_resumes_and_keeps_existing_statements(self):
        from statement_backfill import StatementBackfill
        complete={'markdown':'Original public statement','samples':[{'input':'1','output':'2'}]}
        saved={};library=SimpleNamespace(statement=lambda key:saved.get(key),save_statement=lambda key,value:saved.update({key:value}))
        with tempfile.TemporaryDirectory() as directory:
            worker=StatementBackfill(SimpleNamespace(library=library),Path(directory),client=object(),clock=lambda:100)
            worker.pending=lambda:[('new','https://codeforces.com/contest/1/problem/A','New')]
            with patch('public_platforms.statement',return_value=complete) as fetch:
                self.assertTrue(worker.once());self.assertEqual(fetch.call_count,1)
                self.assertEqual(saved['new'],complete)
                self.assertFalse(worker.once())
                self.assertEqual(worker.snapshot()['remaining'],0)
            worker._pending=[('new','https://codeforces.com/contest/1/problem/A','New')]
            with patch('public_platforms.statement',side_effect=AssertionError('Must retain existing content')):
                self.assertTrue(worker.once())

    def test_backfill_rejects_partial_content_and_retries_later(self):
        from statement_backfill import StatementBackfill
        library=SimpleNamespace(statement=lambda key:None,save_statement=lambda *args:self.fail('Partial statement saved'))
        with tempfile.TemporaryDirectory() as directory:
            worker=StatementBackfill(SimpleNamespace(library=library),Path(directory),client=object(),clock=lambda:100)
            worker.pending=lambda:[('new','https://codeforces.com/contest/1/problem/A','New')]
            with patch('public_platforms.statement',return_value={'markdown':'login'}) as fetch:
                self.assertTrue(worker.once());self.assertFalse(worker.once());self.assertEqual(fetch.call_count,1)
                self.assertGreater(worker.failures['new'],100)
