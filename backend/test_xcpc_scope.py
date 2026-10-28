import json
from pathlib import Path
import tempfile
import unittest

from contest_scope import excluded
from library import LibraryDatabase
from store import Store
from test_library import record


class XcpcScopeTests(unittest.TestCase):
    def test_provenance_including_mirrors_and_world_finals(self):
        for name in ('2017 ACM-ICPC World Finals', 'ICPC 2025 全球总决赛',
                     '2017-2018 ACM-ICPC Asia Daejeon Regional Contest',
                     'ICPC 2025 北欧大学生程序设计竞赛', 'ICPC 2024 拉丁美洲总决赛',
                     'ICPC 2023 西南欧区域赛', '2025 ICPC Asia Manila Regional'):
            self.assertTrue(excluded({'contestFullName':name}),name)
        for title in ('[ICPC 2017 WF] Airport Construction','[NEERC 2016] Binary Code',
                      '[ICPC 2011 WF / HNOI2012] 矿场搭建','[ICPC 2001 Taejon R] 相似基因'):
            self.assertTrue(excluded({'contest':'洛谷专题练习','originalTitle':title}),title)

    def test_domestic_and_unrelated_platforms_remain(self):
        for name in ('CCPC 2025 重庆区域赛','ICPC 2024 新疆区域赛',
                     'ICPC 2023 台北新竹区域赛','ICPC 2025 香港区域赛',
                     'ICPC 2023 澳门区域赛','Codeforces Round 1127 (Div.2, Based on Mexican Olympiad)',
                     'ABC 481','AGC 074','蓝桥杯 2025 国赛'):
            self.assertFalse(excluded({'contest':name}),name)
        self.assertFalse(excluded({'contest':'Div.2 1000','title':'World Finals in Moscow',
                                   'knowledge':'德国','statement':'ICPC World Finals'}))

    def test_foreign_event_adjectives_and_original_cyrillic_are_filtered(self):
        for name in ('ICPC 2018 UFBA Practice Session for Brazilian Regionals',
                     '2018 ACM-ICPC Brazilian Regional Contest',
                     'ICPC 2017 Окружной этап Всероссийской олимпиады школьников по информатике - , Самара, II тур (правила)',
                     'ICPC 2017 Samara Regional Contest'):
            self.assertTrue(excluded({'contest':name}),name)
        self.assertFalse(excluded({'contest':'Codeforces Round 123','title':'Brazilian Samara'}))

    def test_domestic_finals_and_online_contests_are_also_retired(self):
        for name in ('CCPC 2021 总决赛','ICPC 2024 亚洲东区决赛','ICPC 2019 亚洲决赛',
                     'ICPC 2020 亚洲网络赛（模拟赛）','ICPC 2023 亚洲东区网络预选赛（第 1 场）',
                     'CCPC 2024 网络赛','ICPC 2024 台湾网络赛',
                     '2024 ICPC Asia East Continent Final','CCPC 2025 Online Contest'):
            self.assertTrue(excluded({'contest':name}),name)
        self.assertTrue(excluded({'contest':'洛谷专题练习','originalTitle':'[ICPC 2019 Asia Final] Moon'}))
        self.assertFalse(excluded({'contest':'CCPC 2022 桂林区域赛','title':'Final Problem',
                                   'originalTitle':'Final Problem','knowledge':'网络流'}))

    def test_old_public_rows_leave_catalogue_but_history_can_still_read_them(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);db=LibraryDatabase(root/'library.sqlite3')
            records=[]
            for identity,name in [('foreign::A','ICPC 2025 日本网络赛'),('world::A','ICPC 2017 全球总决赛'),
                                  ('china::A','CCPC 2025 重庆区域赛')]:
                raw,encoded,solution,statement=record(identity)
                raw['场次']=encoded['contest']=name;records.append((raw,encoded,solution,statement))
            db.import_records(records,{}, {})
            with db.connection() as connection:
                connection.execute('INSERT INTO training_lists VALUES (?,?)',('fixture',json.dumps({'id':'fixture','problems':[
                    {'problemId':identity} for identity in ('foreign::A','world::A','china::A','unknown::A')]})))
            for _ in range(2):
                store=Store(data_file=root/'missing.md',library_file=db.path)
                self.assertEqual({p['id'] for p in store.data()['rows']},{'china::A'})
                self.assertEqual([p['problemId'] for p in store.public_training_lists()[0]['problems']],['china::A','unknown::A'])
                self.assertIsNotNone(store.library.find('foreign::A'))
                self.assertIsNotNone(store.library.solution('world::A'))
                self.assertEqual(store.row('foreign::A')['场次'],'ICPC 2025 日本网络赛')

    def test_shipped_seed_contains_no_excluded_problem(self):
        folder=Path(__file__).resolve().parent.parent/'data/library'
        records=json.loads((folder/'problems.json').read_text('utf8'))
        self.assertFalse([p['id'] for p in records if excluded(p)])
        ids={p['id'] for p in records}
        for name in ('statements.json','solutions.json','detailed_solutions.json','links.json','solution_methods.json'):
            self.assertTrue(all(p['problem_id'] in ids for p in json.loads((folder/name).read_text('utf8'))),name)


if __name__=='__main__':unittest.main()
