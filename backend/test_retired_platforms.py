"""User-retired catalogue sources never return through collection or import."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contest_scope import excluded,retired_platform
from library import LibraryDatabase


class RetiredPlatformsTests(unittest.TestCase):
    def test_primary_identity_only_and_later_policy_overrides_wiki_exemption(self):
        for platform,url in [('HDU','https://acm.hdu.edu.cn/showproblem.php?pid=1'),('LibreOJ','https://loj.ac/p/1'),('POJ','http://poj.org/problem?id=1'),('SPOJ','https://www.spoj.com/problems/TEST/'),('UOJ','https://uoj.ac/problem/1'),('UVa','https://onlinejudge.org/index.php?problem=1')]:
            row={'id':'old','url':url,'platform':platform,'wikiExample':True}
            with self.subTest(platform=platform),patch('contest_scope.requested_wiki_examples',return_value={'old':url}):
                self.assertTrue(excluded(row))
                self.assertTrue(retired_platform(url=url))
        self.assertFalse(retired_platform({'platform':'QOJ','url':'https://qoj.ac/problem/1','title':'HDU reference','verifiedSourceAliases':[{'url':'https://uoj.ac/problem/1'}]}))
        self.assertFalse(retired_platform(url='https://spoj.com.example.org/problems/TEST'))

    def test_new_import_skips_retired_content_without_changing_legacy_record(self):
        with tempfile.TemporaryDirectory(prefix='tb-retired-platforms-') as temporary:
            database=LibraryDatabase(Path(temporary)/'library.sqlite3')
            old={'id':'legacy','platform':'HDU','url':'https://acm.hdu.edu.cn/showproblem.php?pid=1','title':'Old title'}
            with database.connection() as db:
                db.execute('INSERT INTO problems VALUES(?,?,?,?)',('legacy',old['url'],json.dumps({'题名':'Original'}),json.dumps(old)))
            before=database.find('legacy')
            records=[({'题名':'Replacement'},old,{'markdown':'Never replace legacy content'},None),({'题名':'New'},{'id':'new','platform':'POJ','url':'http://poj.org/problem?id=2'},None,None)]
            database.import_records(records,{}, {'new':[('missing-lecture','foundation')]})
            self.assertEqual(database.find('legacy'),before)
            self.assertIsNone(database.find('new'))
            self.assertEqual(database.check()['solutions'],0)
            self.assertTrue(excluded(before))

    def test_public_seed_and_index_contain_only_retained_judges(self):
        root=Path(__file__).resolve().parents[1]
        rows=json.loads((root/'data/library/problems.json').read_text('utf8'))
        self.assertFalse([row['id'] for row in rows if retired_platform(row)])
        manifest=json.loads((root/'backend/resources/wiki-examples.json').read_text('utf8'))
        self.assertEqual(manifest['problemCount'],110)
        self.assertFalse([item['url'] for item in manifest['entries'] if retired_platform(item)])


if __name__=='__main__':unittest.main()
