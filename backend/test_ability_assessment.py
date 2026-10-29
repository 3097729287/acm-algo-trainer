"""Behavioral checks for evidence direction, alias locking and uncertainty."""
import datetime as dt
from contextlib import closing
import hashlib
import json
import sqlite3
import unittest
from unittest.mock import patch
from ability_assessment import assess,from_records,from_successes
from submission_evidence import annotate_sources

NOW=dt.datetime(2026,10,29,tzinfo=dt.timezone.utc)
def facts(count=6,difficulty=1800):
    return [{'id':str(i),'difficulty':difficulty,'rated':True,'solved':True,'weight':1,
             'date':f'2026-10-{i+1:02d}T00:00:00Z','firstPass':True,'topics':['图论']} for i in range(count)]

class AbilityAssessmentTests(unittest.TestCase):
    def test_failures_retries_and_uncertainty_change_result(self):
        good=facts(6,1800)
        clean=assess(good,NOW)
        failed=assess(good+[{**facts()[0],'id':'failure-'+str(i),'solved':False,'difficulty':1000} for i in range(8)],NOW)
        self.assertLess(failed['abilityScore'],clean['abilityScore'])
        retried=assess([{**x,'weight':.25} for x in good],NOW)
        self.assertLess(retried['abilityScore'],clean['abilityScore'])
        self.assertGreater(retried['posteriorInterval'][1]-retried['posteriorInterval'][0],clean['posteriorInterval'][1]-clean['posteriorInterval'][0])
        self.assertEqual(clean,assess(good*20,NOW))
        self.assertLessEqual(clean['abilityInterval'][0],clean['abilityScore'])

    def test_easy_volume_and_one_exceptional_success_do_not_support_high_score(self):
        easy=[{**facts(1,800)[0],'id':str(i)} for i in range(500)]
        hard={**facts(1,3600)[0],'id':'hard'}
        result=assess(easy+[hard],NOW)
        self.assertLessEqual(result['abilityScore'],800)
        self.assertLessEqual(result['effectiveEvidence'],9)
        self.assertEqual(result['abilityScore'],assess(easy+[hard],NOW+dt.timedelta(days=180))['abilityScore'])
        self.assertEqual(result['recentPerformance']['attempted'],501)

    def test_actual_new_attempts_change_window_but_repeats_cannot(self):
        previous=facts(6,2400)
        recent=[{**facts(1,1000)[0],'id':f'n{i:03d}','date':'2026-10-28T00:00:00Z','solved':i<30} for i in range(60)]
        self.assertLess(assess(previous+recent,NOW)['abilityScore'],assess(previous,NOW)['abilityScore'])
        self.assertEqual(assess(previous*40,NOW)['attemptedCount'],6)

    def test_exact_aliases_assistance_and_nonofficial_results(self):
        rows=[{'id':'a','url':'https://codeforces.com/contest/100/problem/A','difficulty':1800,'platform':'Codeforces',
              'difficultySource':'Codeforces 官方 rating','difficultyEstimated':False,'aliasIds':['old-a']}]
        def record(verdict='AC',**extra):
            return {'id':'r','problem_id':'a','mode':'submit','scope':'official','verdict':verdict,
                    'submitted_at':'2026-10-01T00:00:00Z','finished_at':'2026-10-01T00:01:00Z',
                    'code':'verified source','solution_seen':0,**extra}
        clean=from_records(rows,[record(),record(problem_id='old-a')],NOW)
        self.assertEqual(len(clean),1);self.assertTrue(clean[0]['solved'])
        assisted=record(solution_seen=1)
        later=record(id='later',submitted_at='2026-10-02T00:00:00Z',finished_at='2026-10-02T00:01:00Z')
        self.assertEqual(from_records(rows,[assisted,later],NOW),[])
        wrong=record('WA',submitted_at='2026-09-30T00:00:00Z',finished_at='2026-09-30T00:01:00Z')
        self.assertFalse(from_records(rows,[wrong,assisted,later],NOW)[0]['solved'])
        for changes in ({'scope':'local'},{'verdict':'SAMPLE_PASS'},{'verdict':'CE'},{'code':''},{'solution_seen':None}):
            self.assertEqual(from_records(rows,[record(**changes)],NOW),[])
        unknown=from_records([{**rows[0],'difficulty':None}],[record()],NOW)
        self.assertIsNone(assess(unknown,NOW)['abilityScore'])

    def test_unrated_attempts_do_not_displace_known_evidence_or_create_scores(self):
        known=facts(6,1800)
        unknown=[{**facts(1)[0],'id':'unknown-'+str(i),'date':'2026-10-28T00:00:00Z','rated':False,'difficulty':None,'weight':0} for i in range(80)]
        baseline=assess(known,NOW);extended=assess(known+unknown,NOW)
        for key in ('abilityScore','posteriorInterval','evidenceCount','effectiveEvidence','lastEvidenceAt'):
            self.assertEqual(extended[key],baseline[key],key)
        self.assertEqual(extended['unratedAttemptedCount'],80)
        self.assertEqual(extended['lifetimeAttemptedCount'],86)
        self.assertEqual(extended['recentPerformance']['attempted'],86)
        self.assertFalse(assess([{**item,'weight':0} for item in known],NOW)['qualified'])

    def test_first_ac_and_window_compare_instants_with_conservative_ties(self):
        row={'id':'a','url':'https://codeforces.com/contest/100/problem/A','difficulty':1800,'platform':'Codeforces',
             'difficultySource':'Codeforces 官方 rating','difficultyEstimated':False}
        def receipt(stamp,finish,**fields):
            return {'id':'r','problem_id':'a','mode':'submit','scope':'official','verdict':'AC','code':'saved source',
                    'solution_seen':0,'submitted_at':stamp,'finished_at':finish,**fields}
        assisted=receipt('2026-10-02T01:00:00+08:00','2026-10-02T01:01:00+08:00',solution_seen=1)
        later=receipt('2026-10-01T18:00:00Z','2026-10-01T18:01:00Z')
        self.assertEqual(from_records([row],[later,assisted],NOW),[])
        uncertain=receipt('2026-10-02T02:00:00+08:00','2026-10-02T02:01:00+08:00',id='z',code='')
        self.assertEqual(from_records([row],[later,uncertain],NOW),[])
        evidence=[{**facts(1)[0],'id':'one','date':'2026-10-02T01:00:00+08:00'},
                  {**facts(1)[0],'id':'two','date':'2026-10-01T18:00:00Z'}]
        value=assess(evidence,NOW)
        self.assertEqual([item['id'] for item in value['evidence']],['one','two'])
        self.assertEqual(value['lastEvidenceAt'],'2026-10-01T18:00:00.000000Z')
        normalized=[{'key':'a','scope':'official','independent':False,'independentKnown':True,'difficulty':1800,'acceptedAt':assisted['submitted_at']},
                    {'key':'a','scope':'official','independent':True,'independentKnown':True,'difficulty':1800,'acceptedAt':later['submitted_at']}]
        self.assertEqual(from_successes(normalized,NOW),[])

    def test_lazy_private_source_reference_counts_without_downloading_code(self):
        from account_chunks import CODE_PREFIX
        reference=CODE_PREFIX+json.dumps({'root':'a'*64,'sha256':hashlib.sha256(b'saved source').hexdigest(),'bytes':12})
        with closing(sqlite3.connect(':memory:')) as db:
            db.execute('CREATE TABLE account_sync_code_refs(submission_id TEXT PRIMARY KEY,reference TEXT)')
            db.executemany('INSERT INTO account_sync_code_refs VALUES(?,?)', [('private',reference),('invalid',CODE_PREFIX+'corrupt'),('empty',CODE_PREFIX+json.dumps({'root':'a'*64,'sha256':'b'*64,'bytes':0}))])
            rows=[{'id':name,'problem_id':name,'mode':'submit','scope':'official','verdict':'AC','code':'','solution_seen':0,
                   'submitted_at':'2026-10-01T00:00:00Z','finished_at':'2026-10-01T00:01:00Z','sourcePresent':True}
                  for name in ('private','public','invalid','empty')]
            with patch('account_chunks.ChunkTransport.read_blob',side_effect=AssertionError('assessment must not download private source')):
                annotated=annotate_sources(rows,db)
                library=[{'id':item['id'],'url':'https://codeforces.com/contest/100/problem/'+chr(65+i),'difficulty':1800,
                          'platform':'Codeforces','difficultySource':'Codeforces 官方 rating','difficultyEstimated':False} for i,item in enumerate(rows)]
                result=from_records(library,annotated,NOW)
            self.assertEqual(len(result),1)
            self.assertEqual(result[0]['problemId'],'private')
            self.assertTrue(result[0]['solved'])
            self.assertTrue(all(not row['code'] for row in annotated))
            self.assertFalse(next(row for row in annotated if row['id']=='public').get('sourcePresent',False))

if __name__=='__main__':unittest.main()
