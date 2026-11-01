import hashlib
import sqlite3
import unittest
from paths import resource
from wiki import read
from errors import APIError

class WikiTests(unittest.TestCase):
    def test_real_snapshot_preserves_sources_math_code_images_and_attribution(self):
        with sqlite3.connect(resource('oi-wiki.sqlite3')) as db:
            rows=db.execute('SELECT id,url,sha256,html,original_html FROM articles').fetchall()
            self.assertEqual(len(rows),41)
            for identity,url,digest,html,original in rows:
                self.assertEqual(hashlib.sha256(original).hexdigest(),digest,identity)
                self.assertIn('本页面贡献者',html)
                self.assertIn('CC BY-SA 4.0',html)
                self.assertIn('SATA',html)
                self.assertNotRegex(html,r'<(?:script|iframe|object|style)\b|\son(?:click|load|error)=')
                self.assertNotRegex(html,r'<img[^>]+src="https?://')
                self.assertTrue(url.startswith('https://oi-wiki.org/'))
            binary=read(identity='basic/binary')['article']['html']
            self.assertIn('<math',binary);self.assertIn('<pre',binary);self.assertIn('data:image/',binary)

    def test_search_no_results_and_unknown_identity(self):
        self.assertTrue(read('二分')['articles'])
        self.assertEqual(read('no-such-wiki-topic-xyz')['articles'],[])
        with self.assertRaises(APIError):read(identity='../../personal')
