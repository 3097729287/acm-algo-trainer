"""Evidence, rank compatibility and private metrics in disposable state."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import unittest
from urllib.parse import quote
import test_training as fixtures
from admin import controls
from knowledge import analyze_problem,category_path,dictionary,normalize_tags
from tb_rank import TIERS,RANK_THRESHOLDS,rank_index
from training import ServiceError
from usage import record,snapshot

class PrivateMetricsTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown
    accept=fixtures.ServiceTests.accept
    session='11111111-1111-4111-8111-111111111111'
    def tick(self,sequence,seconds=30):return record(self.service,{'sessionId':self.session,'sequence':sequence,'seconds':seconds})
    def test_usage_is_idempotent_and_overlapping_windows_do_not_double_count(self):
        self.tick(1);self.tick(1)
        self.assertEqual(snapshot(self.service)['totalSeconds'],30)
        self.clock.advance(seconds=10);self.tick(2)
        self.assertEqual(snapshot(self.service)['totalSeconds'],40)
        self.session='22222222-2222-4222-8222-222222222222';self.tick(1)
        self.assertEqual(snapshot(self.service)['totalSeconds'],40)
        for seconds in (-1,0,61,float('nan'),True):
            with self.assertRaises(ServiceError):self.tick(3,seconds)
    def test_usage_splits_beijing_midnight_and_is_read_only_on_query(self):
        self.clock.value=dt.datetime(2026,10,23,16,0,10,tzinfo=dt.timezone.utc)
        self.tick(1,30)
        self.assertEqual(snapshot(self.service)['days'],[{'date':'2026-10-23','seconds':20},{'date':'2026-10-24','seconds':10}])
        before=self.service.connection.total_changes;snapshot(self.service)
        self.assertEqual(self.service.connection.total_changes,before)
        self.clock.advance(seconds=70);self.tick(2,30)
        self.assertEqual(snapshot(self.service)['totalSeconds'],60)
    def test_metrics_use_real_official_ac_and_deduplicate_repeat_ac_same_day(self):
        self.accept();self.accept();self.accept('fixture::B')
        self.clock.advance(days=1);self.accept('fixture::C')
        value=self.service.insights()['personalStatistics']
        self.assertEqual(value['maxDailyAc'],2)
        self.assertEqual(value['longestAcStreak'],2)
        self.assertEqual(value['hardestSolved']['id'],'fixture::C')
    def test_broad_subject_counts_and_filters_keep_unknown_children_unknown(self):
        row=self.library.rows[0];row.update(tags=[],knowledgeCategories=['动态规划'])
        self.accept()
        entries={item['name']:item for item in self.service.insights()['knowledge']}
        self.assertEqual(entries['动态规划']['available'],1)
        self.assertEqual(entries['动态规划']['officialAccepted'],1)
        options={'platform':'','tags':['动态规划'],'excludeSolved':False,'reviewedOnly':False}
        self.assertTrue(self.service._eligible_contest_row(row,options,0,10000,set()))
        self.assertFalse(self.service._eligible_contest_row(row,{**options,'tags':['线性 DP']},0,10000,set()))
    def test_old_admin_rank_indexes_read_without_rewriting_and_new_save_is_stable(self):
        self.service.admin_mode=True
        with self.service._write() as connection:
            connection.execute("INSERT INTO account_preferences VALUES('admin-controls',?,?)",(json.dumps({'level':10,'tier':9,'allAchievements':False}),'2026-10-01'))
        before=self.service.connection.total_changes
        self.assertEqual(controls(self.service)['tier'],8)
        self.assertEqual(self.service.connection.total_changes,before)
        controls(self.service,{'level':10,'tier':4,'allAchievements':False})
        self.assertEqual(controls(self.service)['tier'],4)

class ReviewedKnowledgeTests(unittest.TestCase):
    def test_interactive_is_a_real_leaf_and_generic_title_is_not_algorithmic_evidence(self):
        self.assertEqual(normalize_tags(['interactive'],official=True)['tags'],['交互题'])
        self.assertNotIn('交互题',analyze_problem({'title':'交互题'},'给定数组，输出所有元素的 MEX。')['tags'])
        self.assertIn('交互题',analyze_problem({},'This is an interactive problem. Print a query and flush your output.')['tags'])
    def test_geometry_topics_have_the_same_parent_in_every_filter_tree(self):
        for name in ('平面向量','点积与叉积','线段相交','圆与切线','凸包','旋转卡壳','几何重心','半平面交','三维几何'):
            self.assertIn(name,dictionary()['names'])
            self.assertTrue(category_path(name).startswith('计算几何'),(name,category_path(name)))
    def test_every_targeted_annotation_binds_to_the_exact_public_solution(self):
        root=Path(__file__).resolve().parents[1]
        review=json.loads((root/'backend/resources/knowledge_topic_review.json').read_text(encoding='utf-8'))
        solutions={p['problem_id']:p['markdown'] for p in json.loads((root/'data/library/solutions.json').read_text(encoding='utf-8'))}
        audit=json.loads((root/'backend/resources/metadata-review-1423.json').read_text(encoding='utf8'))
        external={item['id']:item for item in audit['estimated'] if item['id'].startswith('remote:atcoder:')}
        published={item['id']:item for item in audit.get('knowledgeReviews',[])}
        for rule in review['problems'].values():
            for source in rule['sources']:
                if source.get('kind')=='self-reviewed-statement':
                    item=published[source['problemId']]
                    self.assertEqual(source['reference'],item['source'])
                    self.assertEqual(source['sha256'],item['statementSha256'])
                    self.assertEqual(source['sha256'],item['editorialSha256'])
                    self.assertIn(source['problemId'],rule['problemIds'])
                    continue
                if source.get('kind')=='published-reference':
                    item=published[source['problemId']]
                    self.assertEqual(source['reference'],item['source'])
                    self.assertEqual(source['sha256'],item['editorialSha256'])
                    if source['reference'].startswith('https://acmicpc-pacnw.org/ProblemSet/2018/PacNW2018_sols_and_io.zip#'):
                        references={
                            'H':('RepeatingGoldbachs','RepeatingGoldbach_tgr.cpp','0847288eb8de459c8f2fe449d6c4276077545084833f533ee25996bc394e1ff0'),
                            'I':('Inversions','Inversions_tgr.cpp','5da3af7cc9bdbaf1f5dfcf102a0c67a6100500765454161f005615426c27e825'),
                            'L':('Liars','Liars_tgr.cpp','65f607f6426b0536a83a5b30d0028a1279ea59f6a1abeefa158cfe491712cb59'),
                        }
                        letter=source['problemId'].rsplit('::',1)[1]
                        key,filename,digest=references[letter]
                        self.assertEqual(source['problemId'],f'remote:codeforces:101982::{letter}')
                        self.assertEqual(source['reference'],f'https://acmicpc-pacnw.org/ProblemSet/2018/PacNW2018_sols_and_io.zip#sols/{key}/submissions/{filename}')
                        self.assertEqual(source['archivePath'],f'sols/{key}/submissions/{filename}')
                        self.assertEqual(source['archiveSha256'],'b88511983da6d7129f8f6e488b28532766d6729146d33335d25e77e7342afb78')
                        self.assertEqual(source['sha256'],digest)
                        self.assertEqual(source['originalSource'],'https://pnw.na.icpc.global/results/')
                        self.assertIn(source['problemId'],rule['problemIds'])
                        continue
                    if source['reference'].startswith('https://raw.githubusercontent.com/iagorrr/competitive-programming-solutions/'):
                        references={
                            'A':('fiding-maximal-non-trivial-monotones.cpp','9eb7844ea2fb6f77086ad56138d22719d76db287c5955a70fbf16e411ae25f79'),
                            'C':('Cutting with Lasers.cpp','288ee13035b327f0b97172a2345f39e174b02ce7d3b29fec2d1f3318c08bdad1'),
                            'E':('eliminating-ballons.cpp','140213b20c9afa5afa8dd5aa7fc86793259ff72f8c9a60341e1e6ac93047dd0e'),
                            'F':('multidimensional-hangman.cpp','5d101d9535aaec08f957924f79f56e2615814dccc41aca086dd9cf25522da49f'),
                            'I':('intercepting-information.py','d8641e393957a4522994395d5af685e5d62da41f4dff0938dad968b10b75ba6a'),
                            'J':('playing-23.cpp','cfa83e0426291b148672e27596a7c8d1b873fbb6acbc494519e3052f53a3f456'),
                            'N':('N. Number on Both Sides.cpp','58839fd1a7e08846c977bf667825676607b9aee58e64d77da9ee6a8b5965ba17'),
                        }
                        cid=source['problemId'].split(':')[2]
                        if cid=='104555':
                            references={
                                'A':('Amusement Park Adventure.cpp','a26795f4b4c484d1036b318cd9b0d726fd67b4c2aa772d71ec7a22e65174eeb3'),
                                'B':('Best Fair Shuffles.cpp','96c398993fbc9de8277a17e61bd3d5c5780a687c73631fa2125a47ab3cc06270'),
                                'C':('Challenging Hike.cpp','e391ff60a5bb27072a066ff060e21913415d0504ebc976332b797c5e8631e584'),
                                'E':('Extracting Pollen.cpp','b2357ccb347efe298f772413aa756a4b3807495f51f86c9ca59bdc2621f76196'),
                                'F':('Fatigue-Fighting Vacation.cpp','ba401cd26ee9a7692637f071832ad6a23f831d9833c7a5cc9aa7f655d0ae3df8'),
                                'G':('Great Treaty of Byteland.cpp','7fc9929d4c8d267669d5eec56fc91b2044879627d9ec1bd764ca0c0091638c66'),
                                'H':('Honest Worker.cpp','76fbb4bafa5d7d0c7faa502124edb3efec0664722cad1d68e6770fb74382e12f'),
                                'I':('Investigating Zeroes and Ones.cpp','61c5c546973fa70c6fbc25e74a9f9c9ce2bbb348b7a058ff51c0a6dbd3bf1a85'),
                                'K':('K for More, K for Less.cpp','9a19ccfd4cb55cd6e874371ceb3085511e44e2c02151926e89b28255c29320b1'),
                                'L':('Lexicographical Challenge.cpp','46379749ff7ae0075bd4cde87c05f3a6b12c12efa1c59acef8c001888180f8f4'),
                                'M':('Maximizing Flight Efficiency.cpp','57ef93c8a9ffffa3475f4bc29ae4820c1556c4df520c02ae680dd2af9d02ef61'),
                            }
                        self.assertIn(cid,('103960','104555'))
                        letter=source['problemId'].rsplit('::',1)[-1];filename,digest=references[letter]
                        season={'103960':'2022-2023','104555':'2023-2024'}[cid]
                        path=f'submissions/ICPC/{season} ICPC Brazil Subregional Programming Contest/'+filename
                        self.assertEqual(source['reference'],'https://raw.githubusercontent.com/iagorrr/competitive-programming-solutions/f0979af77af00556da9cdd4f5b7a38c3dfacd5b4/'+quote(path))
                        self.assertEqual(source['originalSource'],f'https://codeforces.com/gym/{cid}/problem/'+letter)
                        self.assertEqual(source['sha256'],digest)
                        self.assertIn(source['problemId'],rule['problemIds'])
                        continue
                    if source['reference'].startswith('https://raw.githubusercontent.com/sukhoeing/aoapc-bac2nd-keys/'):
                        references={
                            '10824':('ch10','8c91aea69489e76b5cf8a6156ae27df449b5841c3b8ca41fff8d06e57fa9eafe'),
                            '11895':('ch10','406a92d21518ca224162222c31edfada0ef575ce4c8c6f17ecedbb310f44e480'),
                            '11982':('ch10','8711523e0290b302e98c4d80ff94e5af905488a23c00c51ee599f77d8921f025'),
                            '12508':('ch10','8fbf50473f4428c6ece62f0e6a4ab7303e74a37543548b7c19bd8c0c99f30bd2'),
                            '12520':('ch10','72f087a38438b027a19d8dc16e75ca63ed87597c29128c2d0c85848c227b0954'),
                            '12535':('ch10','f7c093941caa518c498eebf1be9dc9763c71f88d869351b75b7628cdf9be8385'),
                            '1654':('ch10','4ce2652e846ffcf3ecbcbfa3dbcbe5c73fb0d2c84509fa5ce0f56460a2b44ee8'),
                            '1656':('ch10','df2d607444ba7cf5b0b6a237847ae7a2f635350b0b313be00fd64c6e0e9e6541'),
                            '10757':('03_regional','73fec1c268fc6ed82d1e550164dd03f969528dbf3346ef7ba8d3992654751d17'),
                            '12264':('ch11','ee36fcf9a08c3d2f534955b79483ee1946d143b82ac71dc6ed6afff489936488'),
                            '12306':('ch12','85be5f8b2e1633bbb1a1afa325570567e60e695a8f23dbdad0180263e8422738'),
                            '12566':('ch12','2af97a87118df3ad54a8cca76f6db145a26f2de6c5fcdfb874af901d15da7cc0'),
                            '1634':('ch09','f5eb8173433e699b57ff839a581461a2ad6ded1fcc961a4036037caa7ef163a0'),
                            '1662':('ch11','bf0f8ee819e1a7c0da7154ab4bc1831e2aa2dc37d896c37b3d0b31959e428601'),
                            '1667':('ch11','35ef7187f3f0380a857c5b1450571c960ac25a5c49e78eb688cabe1590078d55'),
                            '1670':('ch11','967c78d14d11e79dc6ccd1512ca30766adfcfcd62ce485bd72f8b379acbca23e'),
                        }
                        number=source['problemId'].removeprefix('luogu-training-UVA')
                        folder,digest=references[number]
                        self.assertEqual(source['reference'],f'https://raw.githubusercontent.com/sukhoeing/aoapc-bac2nd-keys/edd03c3cf9932bcc0edd497e5e46e9756d377a39/{folder}/UVa{number}.cc')
                        self.assertEqual(source['originalSource'],f'https://www.luogu.com.cn/problem/UVA{number}')
                        self.assertEqual(source['sha256'],digest)
                        self.assertIn(source['problemId'],rule['problemIds'])
                        continue
                    if source['reference'].startswith('https://contest.felk.cvut.cz/19cerc/solved/'):
                        references={
                            'https://contest.felk.cvut.cz/19cerc/solved/deep-solutions.zip#accepted/vysilacka.py':('efbef38f248166d30a754fda095d7c2f40e0a677bf39f5365e458e4d9299224f','7de23238bd0dc7caa04bfdcf26a38ee61bf3c5fdf62ee9fa40b101355d3c2298'),
                            'https://contest.felk.cvut.cz/19cerc/solved/screamers-solutions.zip#accepted/screamers.java':('becd2a368c22f29c5046589d08fb5713861b5e412bfac082d6d910e35983490e','09970c3d9ef7ae5f77d16a87748adf076eb7e20c8e5b52680144061f6ad93798'),
                        }
                        self.assertIn(source['reference'],references)
                        self.assertEqual((source['archiveSha256'],source['sha256']),references[source['reference']])
                    elif source['reference'].startswith('https://icpc-ecna.ysu.edu/PastResults/2020/'):
                        references={
                            "allinthefamily":("A","aitf-bobk.py","37633102148ca5306fa4082594897a0716475a3ff5aaa1fc0bea905bedcd3624","607ecc2cfe9c3cd1b9f982b23476c7cbd847f515e0d90cc39d153ea343b1a6ab"),
                            "kinkywordsearch":("B","kinky-sean.cpp","9e4ad8581138c7649552b2fc2e230a6a62d9807b88f08c8db73729d0af014762","3f47ee5b854662ec51e1e0bd0dff756b9e0274af8ec7c3986e4bdda2848dc16a"),
                            "mathtrade":("C","math-sean.cpp","50cac8886e657926e807c126bf0551b0863825cc8f50f9d18283fb47c60f9fe0","bd42a7445c198a7a0e1ddc00209e8d6805e2f869e12a557a45c25f58c04697cd"),
                            "oreperationsresearch":("D","ore_john.cpp","9fcac21f985f68f5de7a0159e3b87c14aa24cd9e9d858df5b9f4716db3838152","3b883917c52f52bf77916da575d668710f91496f26c76b2883371b712422af2b"),
                            "overthehill1":("E","overthehill1_bobk.py","e7e891887dd98f4dea438bab82323c7e4f45abf43ef2de1bb4524be9049be863","3ab7f96da6618d9caee97e8000196c07f2c730bad27fe60f94cefdabdcb40537"),
                            "overthehill2":("F","main.py","adef91e575b6c42d74903b98224f6a9abedf5f0282b32ad7e58c0deccd97dddd","3547b5573b1e2c15a914b03b0c93b0505b46f2693c9fab9ec324051c02ddc9f4"),
                            "rankproblem":("G","rank-bobk.py","a125c7f1f43bf977d314ce3a27f5098983851124746def9138dadc76aea91d12","9be8682afe183fe2c62da5742d178b9d916753c2304962bf7dceaa48ef7913d5"),
                            "restroommonitor":("H","restroom-bobk.py","503d62343f9adf68cc8a51d0c8b19534785dfcf625d006e74690980e452a937b","e69174c2ed3345a2858fca1cb3d71a4a945176e3c6a200bec1d15b31278c9f45"),
                            "simplysudoku":("J","simplysudoku_bobk.py","39f45396cabb6d07bc9ff61ee73a18a75325218fe64a5f51d3e0a0d85192bc52","924e17a17bb42bdf45c99f8208125ddff1037c52112c1d592b20f9e8a859c918"),
                            "weightytomes":("K","weighty_john.cpp","24dadcea8cbea3c7201567051c586cdbf31d5a4a8de255b3e66b5ada10daa090","46cf110eead83721e708c53960ddd0f21af1fe5519661bf39f909f703967fdef"),
                            "scholarslawn":("I","scholars_pq_john.cpp","05bc590eefa0fe150bc38920decd770957a50f817dee6bfad45671bae7a52def","a867edee917a5a7bbd358af3e67b2c8638d563654d0fb2514323fa314a59e153"),
                            "workers":("L","main.py","4363fce555b14410e7c08cfb0f9b54aff49dffe662e336894ddb714a670b5a97","4dc399d455347997b077c7158663fdcc4258b746d5325bc7401d21f2e7e067e9"),
                        }
                        key=source['archivePath'].split('/',1)[0]
                        letter,filename,archive_digest,program_digest=references[key]
                        self.assertEqual(source['problemId'],f'remote:codeforces:104587::{letter}')
                        self.assertEqual(source['reference'],f'https://icpc-ecna.ysu.edu/PastResults/2020/{key}.zip#{key}/submissions/accepted/{filename}')
                        self.assertEqual(source['originalSource'],'https://icpc-ecna.ysu.edu/PastResults/2020/problemset.html')
                        self.assertEqual((source['archiveSha256'],source['sha256']),(archive_digest,program_digest))
                    elif source['reference'].startswith('https://icpc-ecna.ysu.edu/PastResults/2019/'):
                        references={
                            'retribution':('A','retribution_n3_john.cpp','4a6c1a4fc9acf77dd9585cf1d65804959c1e7e6c15650263e46d4c32fcea3d00','d7f67a57204660225c6213e22313f43dd64dc9cc48067c35a8b99cbd3482dfa2'),
                            'biotrip':('B','biotrip_bobk.py','84d73d632f8508c664a6ae8c5c4ad3b1fa659221d11b4cfc86e98fe8b43a0611','f8727702c26de3a4d0cc1e04f0853e9bd1c534e174bf9f396a5dc5ca3d6f99fd'),
                            'cheeseifyouplease':('C','cheese_bobk.py','bfad944ea3cd08af8eab50d2e75b8e615c7f46e2bdd29613b2cf323d55978e0a','2a6ace215abbeec9d35e0b2ed0db59edabbd069b6e0cf5ce0d3295f7a1a8e720'),
                            'followthebouncingball':('D','follow_bobk.py','9defd220b9fdd377ef0941c0ee2d3cd23beb34ddb7e14fe90c63091d89c16930','99b057426ce487c70e4a509abcbefb803031138114e1e6939e9988a1b81bb154'),
                            'justpassingthrough':('E','jpt_bobk.py','01d31be7940368e676a1aa5f153515ffc5c0f693b55bc0b42020cdcf9afb3fa0','41f1027dd7fc9daf53778a0e487935ef949d53d582d38266b33ef7c8d8aeab82'),
                            'musicalchairs':('F','musical_bobk.py','1f383e71ef91f01bd4999c55d61eacd29f74a936fa702e9fc0759a1b67ecd00b','202df653e1e6f91afe7f41aa4a812d9f0fc81cf5ed9e6317861d6027579189f4'),
                            'outofsorts':('G','bbotch_john.cpp','63381a303e16b582b6e0068c928612183c85e2d1c92d0e3e737eab8e1535ba44','95673ec445bf7fe661faf65622c695b8c4f03f0f9f24755c7207dae0dec1a42c'),
                            'remainderreminder':('H','rr_bobk.py','a724bccb8a74a15c5b2e49f67bc8daefdbfb80083b1f6bb14f45edfd5ad91a40','bba933fe29f8e97f9e826a0b129ec96f2c591cf11fad9b5b9021c43389ca88ea'),
                            'squarerooms':('I','squares_bobk.py','84388fe8e6df14e18cbb809e6fe1859106af8d078d343c1d7199ffaf00a7aa7b','87ec792b22113ca7ff1189fe3fe3508f73928cbf9f5286d8361d27f9aef5c709'),
                            'taxededitor':('J','TaxedRSR.java','cad7a5a7be67ae35ff7d12a6c3e94cece7b3650b1f4129e8cebe5c7c86a6c68b','b8f2cd86811274ca3d9ba71f313e2e816bd79e3d40727277af47335a642a399e'),
                            'wherehaveyoubin':('K','bin_bobk.py','258afbac37787cea2e41a9fea901fb647edcc89b4a662ff924343e9925d393f2','e48e281d0c6286eb5482e8a5afc37769dd7214d4b46f89cc91c77b1b1271c2d4'),
                        }
                        key=source['archivePath'].split('/',1)[0]
                        letter,filename,archive_digest,program_digest=references[key]
                        self.assertEqual(source['problemId'],f'remote:codeforces:104596::{letter}')
                        self.assertEqual(source['reference'],f'https://icpc-ecna.ysu.edu/PastResults/2019/{key}.zip#{key}/submissions/accepted/{filename}')
                        self.assertEqual(source['originalSource'],'https://icpc-ecna.ysu.edu/PastResults/2019/problemset.html')
                        self.assertEqual((source['archiveSha256'],source['sha256']),(archive_digest,program_digest))
                    elif source['reference'].startswith('https://icpc-ecna.ysu.edu/PastResults/2017/'):
                        references={
                            'abstractart':('A','apoly3.cpp','80ed588b6b50014ec807ef1b7e920930212470bb5f6659fda488e92da2ef1811','997d27208f16a7dfe40d32ca41150b2ddb9a21dea7eac7ce51be1a8625f9493e'),
                            'craters':('B','johncraters.cpp','66598672620a961bef9c54ddcc4aca7ba2a8a0dd7064482c6b07941571c5624c','b475e3fb4743591c95935cad0b9498d371bf65ee04a444ca5910cc6e82c8e1fb'),
                            'drmmessages':('C','bobkDRM.py','2e7b9f406bc87daa88e31c75dc091b92c91997a16844e8e0167fe5749d8973e0','acc2dc7fbd64ee6fa178e063cd3feb11280400f010449f6875924c5498da1f06'),
                            'throwns':('D','bobkGoT.py','eb34f2a207462b89c99e69e9930bb8777b265a10f2595388f8dd94b492a82113','e5d6f6c1093459562f2ebd24546d186d8dc7b9062cc71cd081a70198918324ff'),
                            'isahasa':('E','bryce_tc.cc','28fd0ce6f2e9e545659e5efb5204ec11f1769d8ec5b511991b14978544fca46f','21563d5638f14c73b7aa2cb4a7bb178382fb57859f781400dfc76bbb3110cc59'),
                            'ontrack':('F','tracks.cpp','8b19990d3e833cc294c0c1ad6e9e37e8b7aafa7ed33d68dcda651ccd5af7bed5','4c51ce43a41aabc1d63ede794c218d06fa50ec60033f05c993261d575dddb594'),
                            'ingestion':('G','ingestionsean.cpp','de504243b43d165b22f19a939410e5f3cae797d48c5db217da708602ce5bca4e','8900b51a5bff7571c0ce733d91d31a000012762213d3b39ee4f08573930a84c7'),
                            'amoebas':('H','bobkAmoebas.py','aeb81bd00120bce6d309b8280d02c539cc0a58ddbbe80c62ef71770c0660a961','defde519df7bd9f32bed11198a815a868948f5fd43e3e015b2f86fecabf698f2'),
                            'twentyfour':('I','john24.cpp','be605458f9033112588f15a1e5aea14649f63dcb685b7d253307c1b4bb097e3e','532258271e492a0cb9bf8b330ddb498e07c5fa4b41787694624afebe7bb0bcd2'),
                            'workout':('J','JohnWorkout.java','3b82ce10a700204b74193cfd932b6a3db0313cd5fd5fe5da2582a9b626ab3a00','8eedc8db6c542c4444c2678524f364f1c10b808c1fe6facea6378aaef35afcf8'),
                        }
                        key=source['archivePath'].split('/',1)[0]
                        letter,filename,archive_digest,program_digest=references[key]
                        self.assertEqual(source['problemId'],f'remote:codeforces:101673::{letter}')
                        self.assertEqual(source['reference'],f'https://icpc-ecna.ysu.edu/PastResults/2017/{key}.zip#{key}/submissions/accepted/{filename}')
                        self.assertEqual(source['originalSource'],'https://icpc-ecna.ysu.edu/PastResults/2017/problemset.html')
                        self.assertEqual((source['archiveSha256'],source['sha256']),(archive_digest,program_digest))
                    elif source['reference'].startswith('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2022-2023/'):
                        references={
                            'A':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2022-2023/amazingpuzzle.zip#amazingpuzzle/submissions/accepted/Amazing_bobk.java','39db813856babeda319441afdd0b0780fba61e31b30e8b07f99e6873b0a0a462','4f40d73ce521274f79a630991ffe2384f71e78ceb0716d24a017afdd0300666c'),
                            'B':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2022-2023/amusicalquestion.zip#amusicalquestion/submissions/accepted/musical-bobk.py','d2ec7763eb6586a8e0f5912c10ed4f57c36e2fc722740b946df7b8a8bd206621','8451363b5f5d903ea050d148b8fc37632cf84aa90faeb9a4d39720f6a95bd310'),
                            'C':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2022-2023/cribbageonsteroids.zip#cribbageonsteroids/submissions/accepted/cos-bobk.py','8256faf57b6540d37b18c87df361f4c3c23b90bba255d5d15e0e6a097b08a20b','bf2c5b2676bbd30a10f98c8ac6705bd8a89a2ffe8211c3d5a946f22f166a9664'),
                            'D':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2022-2023/nucleotides.zip#nucleotides/submissions/accepted/dna-bobk.cpp','81354dc35a5f5bd0502606f5c84715dc44087944ffa5c1b748f1ab9cc7c7baaf','66c7e4392e5e5f669f4018fdf9983124f3e092b33048096f7bdb63573a27895e'),
                            'E':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2022-2023/hilbertshedgemaze.zip#hilbertshedgemaze/submissions/accepted/HilbertHedge_John.java','9f3d373ab39b1b584b80ced82ed9c9a1bbeafd647fcaf4b026268264e97a0727','1084b74cce41afb0b2a1698d355885b0bc1db00cad54c3152ea6c2282a1ff030'),
                            'F':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2022-2023/itsabouttime.zip#itsabouttime/submissions/accepted/aboutTime-bobk.py','e1ba6256325f7c18b57a33b822f38466164aa6963e749adcda487a6584a770fe','031225109bb464b995ee64085954aeb20187183f1e99101812bd503b8bf13bd4'),
                            'G':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2022-2023/peapattern.zip#peapattern/submissions/accepted/peapattern-bobk.py','1d89d9dc28687e47598120390acef4e7210ba7bf3965721a088b6d21b9b92f7f','9e9fed5ed38d63c87318f1720042137b57def44a56be155e45ace9c062660fce'),
                            'H':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2022-2023/pickingupsteam.zip#pickingupsteam/submissions/accepted/steam-bobk.cpp','35d9a9e101b066c8835036d443aa973e27d11893b3f0805e93bdada1f1c71df7','8592bc2d83708fb417787f224053d743ab6db30ce6fb02de765b0256a5a21d06'),
                            'I':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2022-2023/roadtosavings.zip#roadtosavings/submissions/accepted/savings-bobk.py','8d3f7ceb9a3f86922aa1b2425b902e4b16ebf2216d15a4861d54b30af17bbc79','d91d2c25790f83fe1875e2de09960f563cd9c762cebf2a63fa634e79cbcd23c1'),
                            'J':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2022-2023/simplesolitaire.zip#simplesolitaire/submissions/accepted/SimpleSolitaire_John.cpp','eae638d7697070507463bc2fe225ec05886ca0c76d6dca1bcdf4ceedc974e2cf','5007de0e5886440abf7c54064b3a2a68366aba32315953ea8f89742853e149c3'),
                            'K':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2022-2023/twochartsbecomeone.zip#twochartsbecomeone/submissions/accepted/TwoCharts_John.java','a5c10b0b52a63ddadfdbf4470b46173d8bc40d467c0c3f71bd2cd80ca0b5dac7','ab9af3d910d44a564818c5aec81f00d0f5e3228ade675dc1f334a978ad2868a4'),
                            'L':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2022-2023/whichwarehouse.zip#whichwarehouse/submissions/accepted/warehouse-bobk.cpp','74d29998a8f4a4755614263910e7342089472c28a735d968690c6eb1d0cb81c6','cb4cd298f1a5934f140d5d06982c9969aa9d810bf46dbbb0d87f1a71b355a4f7'),
                        }
                        letter=source['problemId'].rsplit('::',1)[1]
                        self.assertEqual(source['problemId'],f'remote:codeforces:104614::{letter}')
                        self.assertEqual(source['originalSource'],'https://ec.na.icpc.global/archives/')
                        self.assertEqual((source['reference'],source['archiveSha256'],source['sha256']),references[letter])
                    elif source['reference'].startswith('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2023-2024/'):
                        references={
                            'A':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2023-2024/apivotalquestion.zip#apivotalquestion/submissions/accepted/RSRpivotal.py','8ce983266e60add77c71a434a7bd0acdc859ed21f3a63768c45f4d32b474af4f','92807ae0d93b852213dd867192df80fa3d7824ed365edc521844f5ee48705919'),
                            'B':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2023-2024/broadband.zip#broadband/submissions/accepted/broadband_tmt_n2k.cpp','b2cd1bbde9bff0667cae84532b6309556c27dfee7e084d66438cb0ebdf2630d0','c95fa32ef7df531ecaa835e79826c063d55f9f2eb3d1a8481205023d67542583'),
                            'C':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2023-2024/convexhullextension.zip#convexhullextension/submissions/accepted/convex_tmt.cpp','74a9f2527073211341ac477bad42543b4f77654c13b5cebb940b625cb89d8476','a474e4b9a31294db2d606db136aa49bb90eb6fffd41ddf3b865fe8385ab42152'),
                            'D':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2023-2024/cornhusker.zip#cornhusker/submissions/accepted/corn_tmt.cpp','2faa17a62464e0a006ace581507ae12fbdc6d194b4ab53504703c52a65cc1882','17bf289e5cd9989f96f25104b7914cad19777ff2362699d58f89512decb2d424'),
                            'E':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2023-2024/coltype.zip#coltype/submissions/accepted/Collatz_JPB.java','295445fe2a3e7b172fc6149d609bb51efb132d69aa17bb9979e931037e454c76','7f98252ef806b061942dea80d8513e10431a496f4d57efc13d9bcd93d2de8d74'),
                            'F':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2023-2024/doubleup.zip#doubleup/submissions/accepted/DoubleUp_JPB.java','8c5e0e1397801fcd93438d3f72c3dcd9ee8668075efbf612dea78f447aef8a43','ede85a3ca6e26102e74a129076e93043006c1d067cb14d9e7bc09a713e027c16'),
                            'G':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2023-2024/forestforthetrees.zip#forestforthetrees/submissions/accepted/forest-zack.py','b922ba14eccd867d9034a2db9a3d8c6b4f0df239fe29c3034d18acdd2271fd92','2d337f1919233d0b3a07b65c9982d863a8281484dc6e997d9a58b4f3eed73dff'),
                            'H':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2023-2024/impartialstrings.zip#impartialstrings/submissions/accepted/theorem_python_in.py','3a76de8c57fbf1150d570506a995866cb5db1d414d65b7af310e0996d50219fc','589f57c94ea46651c3c2eeb88c465f4d7438d90cfa3473e3255c9cf307ef5bdf'),
                            'I':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2023-2024/isbnconversion.zip#isbnconversion/submissions/accepted/isbn_jbgny.c','02e1b498dd67007ae71e017ec4bf32ccaf325ec780b6240053d6c3be00a6fa15','6be8eacf57f7029a8c81c426104ef6739091f462036d0187604ef1f47992a9df'),
                            'J':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2023-2024/pearls.zip#pearls/submissions/accepted/Pearls_JPB.java','235aefcdc7a333a81efc596138dc634b19e27b2bdfaf7e7edcb4f32f5dffc701','539cd0eea81cdb9ce7e6b39b900cb46ef85945b848df32ce2cb1880c1263a19d'),
                            'K':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2023-2024/splitdecisions.zip#splitdecisions/submissions/accepted/RSRSplitDecisions.java','b6a6ea6447ee67ba2439b1205900604243012dc23e284692610b1872a08cf66d','a44cdd99e249b8eaeb3f90b077dc6409ca71cdf848975ab0604133329613df1d'),
                            'L':('https://raw.githubusercontent.com/icpc/na-ecna-archive/a6e190a1be63971cc5137b39188a9e5cae39f565/2023-2024/walkinthewoods.zip#walkinthewoods/submissions/accepted/walk_finn_v2.py','2c46068708479a1b4a58d5011e3592648dcc96b40079878e8b5f7012ee7dfe2a','89f5d4a80e5f3cb53740917c0b7bc0d083810d16e14ab4c43fd5057ae198ee31'),
                        }
                        letter=source['problemId'].rsplit('::',1)[1]
                        self.assertEqual(source['problemId'],f'remote:codeforces:104757::{letter}')
                        self.assertEqual(source['originalSource'],'https://ec.na.icpc.global/archives/')
                        self.assertEqual((source['reference'],source['archiveSha256'],source['sha256']),references[letter])
                    elif source['reference'].startswith('https://icpc-ecna.ysu.edu/PastResults/2021/'):
                        self.assertRegex(source['reference'],r'^https://icpc-ecna\.ysu\.edu/PastResults/2021/([a-z0-9]+)\.zip#\1/submissions/accepted/[A-Za-z0-9_.-]+\.(py|cpp|java)$')
                        self.assertEqual(source['originalSource'],'https://icpc-ecna.ysu.edu/PastResults/2021/problemset.html')
                        references={
                            '1sforall':('7a8ef2b6edd058ee2ae4a7ea79da61e7296fe7c0860a229e277ccb26832278cf','3a0215c66f1d7933ebfdbd9e65eee41dadc6c31425f0c97937d9d9095fc44439'),
                            'abridgedreading':('e4cc23b6ca82dffe0dc92c15afc9667ae9460a1591de4255149d7ea834ccdac0','9a2fe462d42e540261a94069924280708519a13cd411da0e45cf7cc3e3206af4'),
                            'ballofwhacks':('2d8760d3d3a0b99273984ceb525382f1115b181ba5f458a5b3195104f98041bc','ae1a7fe91b624ec20fd7a48bccfce73fc5138be8c1be7281d462009b21783230'),
                            'downsizing':('a41e3a189e00f28d84a49ca852a368b5dddb58cd2e489e870e1bc181305d4139','01c97742590d74c20f4f14417c4e4728486e5f4d7c899540ce012e40711a96ab'),
                            'gamblinggame':('c70255d37345f4a12e67bea0c943b1ad2ada880b3db9a70f30dc4881b8875af8','7af02cd8e472d2aeb02d7b7fbb7a72d3ef9f906049442606df8a1ec217ecf8a8'),
                            'growingsomeoobleck':('71286e29c90c8e9f9f47692c25676b58719a7e66beae01f30e35afa5fe36c797','9dbdf6287f71c48f7ebe019839c2690f319020fe53b9afcb7fa83e8a04ecc8a5'),
                            'noonerizedspumbers':('45ccefd75b35e4cbc961db831fd162bc01be3d57a042243b301c8b3e694f3350','c25ede259ff5ee719d42b9105e471fbeb01829d96400aa373e23bdabb0062380'),
                            'numble':('1254a5279ec0eaf784fd67322cfa9e1c2088e1c6e9c3254099e81b1561cc486e','ec8d1dd9119acee91e75ec9b32a890f211a246e3324d770e02285320b000cccc'),
                            'pinnedfiles':('de1bf9d28b50c4cccf35773fc60e8bcfa1b0bbc817e5f9975a9d750d700715a7','3e1a6359cde4fac0a436f703032d353f3fe460c7382024299dcf9e5907939bc5'),
                            'recycling':('cd7db7239f4b36fe233501b47d9e517404236266fb830d70ac1fbcc8d5d5434f','3477f903dc4c6c59e2480bfda929c875208e2cd24426f3a13afbb4c1cd24882a'),
                            'stabletable':('3d9eea5e0948c5a10a401ee1f7f06d9cd2045691cbef7cb1e80b4c87661b377c','7744027a7e6a6e63f1cec333e8f26e8139b73c724f6ab1a68059536f43879565'),
                            'statues':('2442cf9fe779c5c6b6c592a33262421a7ae3291c36c6bcfd64eac8a2922cc1f5','323af41dd866da2e6677e3b44c45c8a854fdd5e44d6dee496d2db425c92b06fb'),
                            'tombhater':('32f1afe5dce592228ab460a51f812adf511a4ad6e4db92a26d488964bf58c7b3','74c174348fac6e52d6d39b4b38e7f3c1c5eafa8e2aa8fdcc1a9192d790be301c'),
                        }
                        key=source['archivePath'].split('/',1)[0]
                        self.assertEqual((source['archiveSha256'],source['sha256']),references[key])
                    else:
                        self.assertRegex(source['reference'],r'^https://swerc\.eu/2020/theme/problems/swerc\.zip#swerc/[A-Za-z0-9]+/submissions/accepted/[A-Za-z0-9_.-]+\.(py|cpp|cc)$')
                    self.assertEqual(source['archivePath'],source['reference'].split('#',1)[1])
                    self.assertEqual(source['archivePath'],item['archivePath'])
                    self.assertEqual(source['archiveSha256'],item['archiveSha256'])
                    self.assertRegex(source['archiveSha256'],r'^[0-9a-f]{64}$')
                    self.assertEqual(source.get('additionalPrograms',[]),item.get('additionalPrograms',[]))
                    for program in source.get('additionalPrograms',[]):
                        self.assertRegex(program['path'],r'^swerc/[A-Za-z0-9]+/submissions/accepted/[A-Za-z0-9_.-]+\.(py|cpp|cc)$')
                        self.assertRegex(program['sha256'],r'^[0-9a-f]{64}$')
                    self.assertIn(source['problemId'],rule['problemIds'])
                    continue
                if source.get('kind')=='published-editorial':
                    item=published[source['problemId']]
                    self.assertEqual(source['reference'],item['source'])
                    self.assertEqual(source['sha256'],item['editorialSha256'])
                    if source['reference']=='https://codeforces.com/blog/entry/114211':
                        self.assertRegex(source['problemId'],r'^remote:codeforces:104252::[A-M]$')
                        self.assertEqual(source['sha256'],'d972446641aefd7412fc1af6439bab8243f83e3f68c428e565af36453e6d0ed2')
                        self.assertEqual(source['captureKind'],'web-prose')
                        self.assertIn(source['problemId'],rule['problemIds'])
                        continue
                    if source['reference']=='https://codeforces.com/blog/entry/101550':
                        self.assertRegex(source['problemId'],r'^remote:codeforces:103640::[BCDEFHIJKLM]$')
                        self.assertEqual(source['sha256'],'c62055aada10acc69280c864d2cc8b0e2bf759ba7301db99bf8886cb810ab051')
                        self.assertEqual(source['captureKind'],'web-prose')
                        self.assertIn(source['problemId'],rule['problemIds'])
                        continue
                    if source['reference']=='https://pnw.na.icpc.global/wp-content/uploads/2024/10/2017alled.pdf':
                        self.assertRegex(source['problemId'],r'^remote:codeforces:(101615::[A-M]|101652::[N-Z])$')
                        self.assertEqual(source['sha256'],'d61a37aa444085a8a140764fdc422a358fd22c48546a4da2222c2db2a0ba8c47')
                        self.assertIn(source['problemId'],rule['problemIds'])
                        continue
                    if source['reference']=='https://pnw.na.icpc.global/wp-content/uploads/2024/10/2018editorial.pdf':
                        self.assertRegex(source['problemId'],r'^remote:codeforces:101982::[A-GJKM]$')
                        self.assertEqual(source['sha256'],'80eac3f4275057f11110232e95e9f0cdf6ba79bb2e0a8fc4af3f5f3c5b79a10a')
                        self.assertIn(source['problemId'],rule['problemIds'])
                        continue
                    if source['reference']=='https://acmicpc-pacnw.org/ProblemSet/2019/editorial.zip#editorial/editorials.pdf':
                        self.assertRegex(source['problemId'],r'^remote:codeforces:102433::[A-M]$')
                        self.assertEqual(source['sha256'],'c93a0a560a030e362c8846546f5e553764f5811ea7aaf9bb607286e4b35ced02')
                        self.assertEqual(source['archivePath'],'editorial/editorials.pdf')
                        self.assertEqual(source['archiveSha256'],'137a4963b14b3de94d5796258022a39593000653c517511d568c9f18ddeb95bd')
                        self.assertEqual(source['originalSource'],'https://pnw.na.icpc.global/results/')
                        self.assertIn(source['problemId'],rule['problemIds'])
                        continue
                    organizer_pdfs=(
                        'https://codeforces.com/gym/104053/attachments/download/17869/2022CCPC%E5%B9%BF%E5%B7%9E%E9%A2%98%E8%A7%A3.pptx',
                        'https://cerc2021.acm.si/res/CERC2021-solutions.pdf',
                        'https://drive.google.com/uc?export=download&id=13WApgof_TR5W-pokndhBQiqdny9wggVw',
                        'https://drive.google.com/uc?export=download&id=1RoVMWSp_QrB7G2rHo5sU7Hkixz0iz6TF',
                        'https://drive.google.com/uc?export=download&id=1MS0R9gT6XGpM_R1DIslzvhQ-MCMR4tIV',
                        'https://2017.gcpc.nwerc.eu/solution_2017.pdf',
                        'https://archive.algo.is/icpc/nwerc/2018/nwerc2018slides-handout.pdf',
                        'https://github.com/icpc/ncpc-web/releases/download/ncpc2017-data/ncpc17slides.pdf',
                        'https://github.com/icpc/ncpc-web/releases/download/ncpc2018-data/ncpc18slides.pdf',
                        'https://cerc.hsin.hr/tasks/cerc2017_presentation.pdf',
                        'https://2020.nwerc.eu/files/nwerc2020slides.pdf',
                        'https://swerc.eu/2017/theme/slides/problemanalysis.pdf',
                        'https://swerc.eu/2018/theme/slides/problemanalysis.pdf',
                        'https://swerc.eu/2019/theme/problems/swerc-analysis.pdf',
                        'https://swerc.eu/2021/problemset/solutions_swerc2021_2022.pdf',
                        'https://swerc.eu/2023/problemset/contest-solutions.pdf',
                    )
                    if source['reference'].endswith('/2022CCPC%E5%B9%BF%E5%B7%9E%E9%A2%98%E8%A7%A3.pptx'):
                        self.assertEqual(source['sha256'],'bbf752b1fdcef7a134ac8fbf03080e3440c4d0a555de23a3b8c163083f205d7d')
                    if source['reference']=='https://archive.algo.is/icpc/nwerc/2018/nwerc2018slides-handout.pdf':
                        self.assertEqual(source['originalSource'],'https://2018.nwerc.eu/files/nwerc2018slides-handout.pdf')
                        self.assertEqual(source['sha256'],'cf399a9f35e96a18d88e7cdcd9abc97ac3ba0076a97dbad005bda9d71c949a8b')
                    if source['reference'].startswith('https://drive.google.com/uc?export=download&id='):
                        drive_documents={
                            '13WApgof_TR5W-pokndhBQiqdny9wggVw':'0c9429d53df960b024ca6f3f7dee7949cf5054d7dfc42762e5061bedca6ae0d3',
                            '1RoVMWSp_QrB7G2rHo5sU7Hkixz0iz6TF':'d49f713701393549a6e6a49efb2348a49748df8778ff0b5808fd25ff168cf1d2',
                            '1MS0R9gT6XGpM_R1DIslzvhQ-MCMR4tIV':'0fa3c667d2000a086976cc91e8a1896819dee2c41585fdc6cee24db39d7e60d4',
                        }
                        file_id=source['reference'].split('id=',1)[1]
                        self.assertEqual(source['originalSource'],f'https://drive.google.com/file/d/{file_id}/view')
                        self.assertEqual(source['sha256'],drive_documents[file_id])
                    authored_latin=source['reference'].startswith('https://raw.githubusercontent.com/Diego1149/ICPC-Latam-2020/')
                    if authored_latin:
                        letter=source['problemId'].rsplit('::',1)[1]
                        self.assertEqual(source['reference'],f'https://raw.githubusercontent.com/Diego1149/ICPC-Latam-2020/80c06207d5df7bcf55f53284201796307565983b/{letter}/Source.cpp')
                        self.assertEqual(source['originalSource'],'https://codeforces.com/gym/103185')
                        self.assertTrue(source['problemId'].startswith('remote:codeforces:103185::'))
                    if not authored_latin and not source['reference'].startswith('https://raw.githubusercontent.com/xcpcio/upload-file/') and source['reference'] not in organizer_pdfs:
                        self.assertRegex(source['reference'],r'^https://codeforces\.com/gym/[0-9]+/attachments/download/[0-9]+/.+\.pdf$')
                    self.assertIn(source['problemId'],rule['problemIds'])
                    continue
                if source.get('kind')=='official-editorial':
                    item=external[source['problemId']]
                    self.assertEqual(source['reference'],item['source'])
                    self.assertEqual(source['sha256'],item['editorialSha256'])
                    self.assertTrue(source['reference'].startswith(('https://atcoder.jp/','https://img.atcoder.jp/')))
                    self.assertIn(source['problemId'],rule['problemIds'])
                    continue
                identity=source['reference'].split('#')[-1]
                self.assertEqual(hashlib.sha256(solutions[identity].encode()).hexdigest(),source['sha256'],identity)
    def test_current_rank_ladder_has_nine_names_and_preserves_threshold_meanings(self):
        self.assertEqual(TIERS,('黑铁','青铜','白银','黄金','翡翠','钻石','大师','宗师','王者'))
        for index,boundary in enumerate(RANK_THRESHOLDS):self.assertEqual(rank_index(boundary),index)
