"""Personal skill estimates stay independent from the size of the catalog."""
import datetime as dt
import unittest

from insights import build_insights


class KnowledgeMasteryTests(unittest.TestCase):
    def test_cf2300_reference_and_low_difficulty_evidence(self):
        from mastery_scale import benchmark_score, estimate
        self.assertEqual(benchmark_score(2300), 100)
        self.assertLess(benchmark_score(1400), 50)
        simple = [dict(id=str(i), rated=True, difficulty=900, solved=True, weight=1) for i in range(5)]
        self.assertLess(estimate(simple)['value'], 50)

    def rows(self, count=5, difficulty=1400):
        return [dict(id=f'p{i}', title=f'Problem {i}', tags=['sorting', 'greedy'], difficulty=difficulty,
                     url=f'https://codeforces.com/contest/123/problem/{chr(65+i)}') for i in range(count)]

    def record(self, identity, verdict='AC', **extra):
        return dict(problem_id=identity, mode='submit', scope='official', verdict=verdict,
                    submitted_at='2026-10-08T09:00:00Z', finished_at='2026-10-08T09:01:00Z',
                    code='independent source '+identity, solution_seen=0, **extra)

    def estimate(self, rows, records):
        return build_insights(rows, records, [], {'training': [], 'contests': []}, {},
                              dt.datetime(2026, 10, 8, 12, tzinfo=dt.timezone.utc))

    def topic(self, value):
        return next(item for item in value['knowledge'] if item['name']=='sorting')

    def test_unattempted_catalog_growth_cannot_change_mastery(self):
        rows=self.rows()
        records=[self.record(row['id']) for row in rows]
        before=self.topic(self.estimate(rows,records))
        after=self.topic(self.estimate(rows+self.rows(30)[5:],records))
        self.assertIsNotNone(before['mastery'])
        self.assertEqual(before['mastery'],after['mastery'])
        self.assertEqual(before['evidenceCount'],5)
        self.assertGreater(after['available'],before['available'])

    def test_sparse_rated_samples_are_estimated_with_uncertainty(self):
        rows=self.rows(4)
        low=self.topic(self.estimate(rows,[self.record(row['id']) for row in rows]))
        self.assertIsNotNone(low['mastery'])
        self.assertGreater(low['masteryInterval'][1]-low['masteryInterval'][0], 25)
        rows=self.rows(5,None)
        low=self.topic(self.estimate(rows,[self.record(row['id']) for row in rows]))
        self.assertIsNone(low['mastery'])
        self.assertEqual(low['ratedEvidenceCount'],0)

    def test_failure_difficulty_and_assistance_influence_estimate(self):
        rows=self.rows()
        records=[self.record(row['id']) for row in rows]
        clean=self.topic(self.estimate(rows,records))['mastery']
        harder=self.topic(self.estimate(self.rows(difficulty=2200),records))['mastery']
        self.assertGreater(harder,clean)
        failed=self.topic(self.estimate(rows,records[:3]+[self.record('p3','WA'),self.record('p4','TLE')]))['mastery']
        self.assertLess(failed,clean)
        assisted=self.topic(self.estimate(rows,[dict(record,solution_seen=1) for record in records]))['mastery']
        self.assertLess(assisted,clean)
        retries=[dict(self.record(row['id'],'WA'),submitted_at='2026-10-08T08:00:00Z') for row in rows]+records
        self.assertLess(self.topic(self.estimate(rows,retries))['mastery'],clean)

    def test_samples_compile_errors_and_aliases_do_not_inflate_evidence(self):
        rows=self.rows(4)
        alias=dict(rows[0],id='remote-alias',source='remote')
        records=[self.record(row['id']) for row in rows]+[self.record(alias['id'])]
        rows += [alias]+self.rows(7)[4:]
        records += [dict(self.record('p4'),mode='run'),dict(self.record('p5'),scope='samples'),self.record('p6','CE')]
        value=self.estimate(rows,records)
        self.assertEqual(self.topic(value)['evidenceCount'],4)
        self.assertIsNotNone(self.topic(value)['mastery'])
        self.assertEqual(len(value['knowledgeEvidence']),4)

    def test_public_receipts_do_not_claim_independent_source(self):
        rows=self.rows()
        records=[dict(self.record(row['id']),code='') for row in rows]
        value=self.estimate(rows,records)
        self.assertTrue(all(item['independence']<1 for item in value['knowledgeEvidence']))

    def test_training_list_aliases_keep_knowledge_and_count_official_receipts_once(self):
        row=dict(self.rows(1)[0],tags=['输入输出'],trainingListMember=True,
                 url='https://www.luogu.com.cn/problem/B2002',aliasIds=['old-training::B2002'])
        alias=dict(row,id='list-copy',tags=['顺序结构'],source='remote',aliasIds=[])
        records=[self.record('old-training::B2002'),self.record('list-copy')]
        result=self.estimate([row,alias],records)
        for name in ('输入输出','顺序结构'):
            knowledge=next(item for item in result['knowledge'] if item['name']==name)
            self.assertEqual(knowledge['evidenceCount'],1)
            self.assertEqual(knowledge['officialAccepted'],1)
            self.assertIsNotNone(knowledge['mastery'])
        self.assertEqual(len(result['knowledgeEvidence']),1)
        samples=self.estimate([row], [dict(self.record(row['id']),scope='samples',verdict='SAMPLE_PASS')])
        self.assertEqual(samples['knowledgeEvidence'],[])

    def test_quantity_and_difficulty_prevent_inflated_small_sample_scores(self):
        small=self.rows(5,800)
        five=self.topic(self.estimate(small,[self.record(row['id']) for row in small]))['mastery']
        self.assertLess(five,70)
        large=self.rows(25,800)
        twenty_five=self.topic(self.estimate(large,[self.record(row['id']) for row in large]))['mastery']
        self.assertGreater(twenty_five,five)
        difficult=self.rows(25,2200)
        self.assertGreater(self.topic(self.estimate(difficult,[self.record(row['id']) for row in difficult]))['mastery'],twenty_five)

    def test_one_question_is_an_estimate_and_duplicates_add_no_certainty(self):
        from knowledge_mastery import estimate
        item = {'id': 'one', 'difficulty': 1600, 'rated': True, 'weight': 1, 'solved': True}
        single = estimate([item])
        self.assertIsNotNone(single['value'])
        self.assertGreater(single['interval'][1]-single['interval'][0], 50)
        self.assertEqual(single, estimate([item]*100))
        many = estimate([dict(item,id=f'p{i}') for i in range(30)])
        self.assertLess(many['interval'][1]-many['interval'][0], single['interval'][1]-single['interval'][0])

    def test_same_problem_difficulty_and_outcome_have_expected_directions(self):
        from knowledge_mastery import estimate
        item = {'id': 'one', 'difficulty': 1600, 'rated': True, 'weight': 1, 'solved': True}
        self.assertGreater(estimate([item])['value'], estimate([dict(item,solved=False)])['value'])
        self.assertGreater(estimate([dict(item,difficulty=2200)])['value'], estimate([dict(item,difficulty=800)])['value'])
        self.assertIsNone(estimate([dict(item,difficulty=None,rated=False)])['value'])
        self.assertIsNone(estimate([])['value'])


if __name__=='__main__':
    unittest.main()
