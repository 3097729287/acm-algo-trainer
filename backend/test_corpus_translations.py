"""Public corpus translation checkpoints preserve originals and survive retries."""
from contextlib import closing
import json,sqlite3,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts import translate_public_library as corpus
from statement_seed import load_statements

class Provider:
    name='fixture'
    calls=0
    def __init__(self,**kwargs):pass
    def __call__(self,text):
        type(self).calls+=1
        if text.startswith('Translate into Simplified Chinese:'):return '给定一个整数，输出它的值。'
        return text.replace('Given a positive integer','给定一个正整数').replace('print twice its value.','输出它的两倍。')

class CorpusTranslationTests(unittest.TestCase):
    def test_resume_and_guarded_export_preserve_samples_originals_and_resources(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'library.sqlite3';work=root/'work'
            original={'id':'fixture','url':'https://atcoder.jp/fixture','markdown':'# Integer\n\nGiven a positive integer $N$, print twice its value.\n',
                      'samples':[{'input':'3\n','output':'6\n'}],'statementAvailable':True,'images':{'figure':'tb-asset:'+'a'*64}}
            with closing(sqlite3.connect(source)) as db,db:
                db.execute('CREATE TABLE statements(problem_id TEXT PRIMARY KEY,content TEXT)')
                db.execute('INSERT INTO statements VALUES(?,?)',('fixture',json.dumps(original)))
            self.assertEqual(corpus.seed(source,work)['pending'],1)
            self.assertEqual(corpus.seed(source,work)['pending'],1)
            Provider.calls=0
            with patch.object(corpus,'DeepSeekProvider',Provider):corpus.run(work,root/'settings',2,None)
            count=Provider.calls;self.assertGreaterEqual(count,2)
            with patch.object(corpus,'DeepSeekProvider',side_effect=AssertionError('Completed checkpoint must not call provider')):corpus.run(work,root/'settings',2,None)
            self.assertEqual(Provider.calls,count);self.assertEqual(corpus.stats(work),{'done':1})
            seed=root/'seed';seed.mkdir();(seed/'statements.json').write_text(json.dumps([{'problem_id':'fixture','content':original}]),encoding='utf8')
            self.assertEqual(corpus.export(work,seed/'statement-patches')['exported'],1)
            updated=load_statements(seed)[0]['content']
            self.assertEqual({k:v for k,v in updated.items() if k!='translation'},original)
            self.assertIsNotNone(corpus.bundled_translation(updated))
            original['markdown']+=' source update'
            (seed/'statements.json').write_text(json.dumps([{'problem_id':'fixture','content':original}]),encoding='utf8')
            with self.assertRaisesRegex(ValueError,'conflicts'):load_statements(seed)

    def test_personal_database_is_never_used_as_a_public_translation_source(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'private.sqlite3'
            with closing(sqlite3.connect(source)) as db,db:db.execute('CREATE TABLE drafts(code TEXT)')
            with self.assertRaisesRegex(ValueError,'public seed'):corpus.seed(source,root/'work')

    def test_public_cache_reuse_requires_exact_url_format_and_source_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'public.sqlite3';work=root/'work'
            original={'id':'fixture','url':'https://atcoder.jp/fixture','markdown':'Given a positive integer $N$, print twice its value.','statementAvailable':True}
            with closing(sqlite3.connect(source)) as db,db:
                db.execute('CREATE TABLE statements(problem_id TEXT PRIMARY KEY,content TEXT)')
                db.execute('INSERT INTO statements VALUES(?,?)',('fixture',json.dumps(original)))
            corpus.seed(source,work)
            cache=root/'cache.json';record={'source_url':original['url'],'source_format':corpus.TRANSLATION_FORMAT,'source_hash':'wrong','target_language':'zh-CN','markdown':'给定一个正整数 $N$，输出它的两倍。'}
            cache.write_text(json.dumps([record]),encoding='utf8')
            self.assertEqual(corpus.reuse(work,[],[],shared_files=[cache])['reused'],0)
            record['source_hash']=corpus.sha(corpus.TRANSLATION_FORMAT+'\n'+original['markdown'])
            cache.write_text(json.dumps([record]),encoding='utf8')
            self.assertEqual(corpus.reuse(work,[],[],shared_files=[cache])['reused'],1)
