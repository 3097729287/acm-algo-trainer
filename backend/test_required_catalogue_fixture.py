"""Strict public-catalogue fixture gates; disposable authoring source only."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from verify_required_downloads_e2e import registered_fixture
from statement_seed import checksum


class RequiredCatalogueFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='tb-required-catalogue-');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.source=self.root/'data/library';(self.source/'statement-patches').mkdir(parents=True)
        self.identity='luogu-training-P7351';self.url='https://www.luogu.com.cn/problem/P7351'
        self.download='https://gitee.com/w33z8kqrqk8zzzx33/dream-oi-extra/raw/master/down.zip'
        self.markdown='# Dream SMP\n\nComplete output-only fixture with [inputs]('+self.download+').\n'
        self.item={'problemId':self.identity,'sourceUrl':self.url,'originalDownloadUrl':self.download,'statementSha256':[hashlib.sha256(self.markdown.encode()).hexdigest()]}
        self.content={'id':self.identity,'url':self.url,'markdown':self.markdown,'samples':[{'input':'5 1\n0 0 1 1','output':'23333'}],
            'limits':{'timeMs':5000,'memoryMb':512},'problemType':'output-only','localJudgeSupported':False,'statementAvailable':True,
            'integrity':{'status':'complete','sourceVerified':True},'attachments':{},'images':{}}
        self.row={'id':self.identity,'url':self.url,'raw':{'_id':self.identity,'状态':'未做','日期':''},'encoded':{'id':self.identity,'url':self.url,'problemType':'output-only','catalogStatementReady':True,'catalogReplayReady':False}}
        self.write()

    def write(self,row=None,content=None):
        old={'id':self.identity,'markdown':'Old source body'}
        (self.source/'problems.json').write_text(json.dumps([row or self.row]),'utf8')
        (self.source/'statements.json').write_text(json.dumps([{'problem_id':self.identity,'content':old}]),'utf8')
        packet={'schema':1,'statements':[{'problem_id':self.identity,'beforeSha256':checksum(old),'content':content or self.content}]}
        (self.source/'statement-patches/reviewed.json').write_text(json.dumps(packet),'utf8')

    def test_guarded_final_source_is_copied_exactly_without_synthetic_solution_or_changed_limits(self):
        catalogue=(self.source/'problems.json').read_bytes()
        record,evidence=registered_fixture(self.item,self.root)
        self.assertEqual(record,(self.row['raw'],self.row['encoded'],None,self.content))
        self.assertEqual(record[3]['limits'],{'timeMs':5000,'memoryMb':512})
        self.assertEqual(evidence['mode'],'registered-catalogue-source');self.assertTrue(evidence['realRegisteredSourceRead'])
        self.assertTrue(evidence['guardedLoadStatementsUsed']);self.assertFalse(evidence['catalogueRetirementChanged'])
        self.assertEqual((self.source/'problems.json').read_bytes(),catalogue)

    def test_hidden_retired_not_ready_or_replayable_catalogue_fails_before_loading_statements(self):
        for field,value in [('statementRetired',True),('catalogHidden',True),('catalogStatementReady',False),('catalogReplayReady',True),('problemType','standard')]:
            row=copy.deepcopy(self.row);row['encoded'][field]=value;self.write(row=row)
            with self.subTest(field=field),patch('statement_seed.load_statements',side_effect=AssertionError('Must reject inactive catalogue before corpus read')),self.assertRaises(ValueError):
                registered_fixture(self.item,self.root)

    def test_incomplete_wrong_original_or_unapproved_body_cannot_be_used_as_registered_source(self):
        changes=[{'integrity':{'status':'incomplete','sourceVerified':True}},
            {'localJudgeSupported':True},{'statementAvailable':False},{'problemType':'standard'},
            {'url':'https://www.luogu.com.cn/problem/P7352'},{'markdown':self.markdown+'Unapproved edit.'},
            {'samples':[{'input':'x','output':None}]}]
        for changed in changes:
            self.write(content=dict(self.content,**changed))
            with self.subTest(change=list(changed)),self.assertRaises(ValueError):registered_fixture(self.item,self.root)

    def test_missing_ordinary_assets_are_not_silently_omitted_from_the_single_task_fixture(self):
        changed=dict(self.content,attachments={'https://source.example/proof.pdf':{'data':'tb-asset:'+'a'*64}})
        self.write(content=changed)
        with self.assertRaisesRegex(ValueError,'silently dropped'):registered_fixture(self.item,self.root)


if __name__=='__main__':unittest.main()
