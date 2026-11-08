"""Merge only validated, explicitly reviewed articles into the portable seed.

No live personal database is opened. Installation/publication are separate.
"""
import argparse
import base64
import copy
import datetime as dt
import hashlib
import json
import mimetypes
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile

from nowcoder_editorials import ROOT, CONTENT, OUT, BASELINE, database, read, write, sha, program, statement

sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/common')]
from difficulty import round_difficulty
TOPIC_ALIASES=json.loads((ROOT/'backend/resources/nowcoder-topic-aliases.json').read_text('utf8'))

TOPICS = {
    '输出': '模拟', '输入输出': '模拟', '分支': '模拟', '循环': '模拟', '格式化输出': '模拟',
    '转义字符': '模拟', '字符编码': '模拟', '浮点输入输出': '模拟', '浮点运算': '数学',
    '四则运算': '整数运算', '整数除法': '整数运算', '取余': '取模与同余',
    '取整': '整数运算', '同余': '取模与同余', '数位': '整数运算', '比较': '模拟',
    '单位换算': '数学', '扫描': '枚举', '统计': '计数', '加权平均': '数学',
    '几何': '计算几何', '物理': '数学', '不变量': '数学', '均值不等式': '数学',
    '方程': '数学', '表达式': '模拟', '字符串解析': '字符串', '日期': '模拟',
    '图案': '模拟', '位置': '模拟', '时间戳': '模拟', '矩阵': '二维数组',
    '有序数组': '数组操作', '最值': '枚举', '查找': '字符串', '大小写转换': '字符串',
    '标记数组': '数组操作', '映射': '模拟', '数列': '数学', '网格': '二维数组',
    '对称': '数学', '归并': '分治', '状态机': '状态建模', '循环关系': '取模与同余',
    '集合交': '集合', '资源兑换': '模拟', '前缀': '字符串', '思维': '数学',
    '等价转化': '数学', '区间': '数学', '区间计数': '计数', '欧几里得算法': '最大公约数',
}


def source_dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def file_digest(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def public_artifact_only(path):
    db = database(path)
    try:
        tables = {x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        db.close()
    assert not tables & {'submissions', 'drafts', 'documents', 'accounts', 'private_fixture'}, path


def checked_entries():
    ledger = read(CONTENT / 'reviewed.json')
    receipts = {x['id']: x for x in read(OUT / 'validation.json')}
    for identity, entry in ledger.items():
        proof = receipts.get(identity)
        assert proof and proof['ok'], 'Unvalidated reference: ' + identity
        assert entry['programSha256'] == proof['programSha256']
        for variant, file in entry['articles'].items():
            assert sha((ROOT / file).read_bytes()) == proof['articleSha256'][variant], identity
    return ledger


def article(entry, variant):
    path = ROOT / entry['articles'][variant]
    markdown = path.read_text(encoding='utf-8')
    assert sha(program(markdown)) == entry['programSha256']
    images = {}
    for reference in re.findall(r'!\[[^\]]*\]\(([^)]+)\)', markdown):
        if reference.startswith(('data:', 'https:')):
            continue
        asset = (path.parent / reference).resolve()
        assert asset.is_relative_to(CONTENT.resolve()) and asset.is_file(), reference
        mime = mimetypes.guess_type(asset.name)[0]
        assert mime and mime.startswith('image/'), asset
        images[reference] = 'data:' + mime + ';base64,' + base64.b64encode(asset.read_bytes()).decode('ascii')
    return {'problem_id': entry['id'], 'markdown': markdown, 'source_path': entry['articles'][variant],
            'images': images}


def inventory(ledger):
    scope = read(ROOT / 'data/next-local/nowcoder-training-coverage.json')
    original_ids = {x['id'] for x in scope['problems']}
    assert set(ledger) <= original_ids, sorted(set(ledger) - original_ids)
    ratings = read(CONTENT / 'ratings.json') if (CONTENT / 'ratings.json').exists() else {}
    assert set(ratings) <= original_ids
    result = []
    with database() as db:
        for identity in sorted(original_ids):
            row = json.loads(db.execute('SELECT encoded FROM problems WHERE id=?', (identity,)).fetchone()[0])
            done = ledger.get(identity)
            review = done or ratings.get(identity)
            rating = review['difficulty'] if review else row.get('difficulty')
            status = ('supplemental-above-2300' if done and rating and rating > 2300 else
                      'validated' if done else 'excluded-above-2300' if rating and rating > 2300
                      else 'editorial-pending' if rating else 'difficulty-review-pending')
            result.append({'id': identity, 'title': row['title'], 'url': row['url'],
                           'status': status, 'difficulty': rating,
                           'difficultyEstimated': review.get('difficultyEstimated') if review else None,
                           'articles': list(done['articles']) if done else []})
    unknown = sum(x['status'] == 'difficulty-review-pending' for x in result)
    pending = sum(x['status'] == 'editorial-pending' for x in result)
    excluded = sum(x['status'] == 'excluded-above-2300' for x in result)
    audit = {'scope': 'All unique original problems in the Nowcoder training lists; <=2300 inclusive',
             'updatedAt': dt.datetime.now(dt.timezone.utc).isoformat(),
             'uniqueOriginalProblems': len(original_ids), 'validatedProblems': len(ledger),
             'difficultyReviewPending': unknown, 'editorialsPending': pending,
             'excludedAbove2300': excluded,
             'supplementalAbove2300': sum(x['status'] == 'supplemental-above-2300' for x in result),
             'eligibleProblems': sum(x['status'] == 'validated' for x in result) + pending,
             'allComplete': unknown == 0 and pending == 0, 'officialSubmissionsSent': 0,
             'problems': result}
    write(CONTENT / 'progress.json', audit)
    return audit


def materialize():
    from knowledge import enrich_row
    from library import LibraryDatabase
    ledger = checked_entries()
    ratings = read(CONTENT / 'ratings.json') if (CONTENT / 'ratings.json').exists() else {}
    reviews = {**ratings, **ledger}
    audit = inventory(ledger)
    source = ROOT / 'data/library'
    names = ['problems', 'solutions', 'detailed_solutions', 'meta']
    before = {name: read(source / (name + '.json')) for name in names}
    for name in names:
        destination = OUT / 'source-before' / (name + '.json')
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / (name + '.json'), destination)
    after = copy.deepcopy(before)
    by_id = {row['id']: row for row in after['problems']}
    for identity, entry in reviews.items():
        row = by_id[identity]
        original_statement = statement(identity)
        assert sha(original_statement['markdown']) == entry['statementSha256'], identity
        original = row['encoded']
        tags = list(dict.fromkeys(tag for x in entry['knowledge'] if x.strip()
                                 for tag in TOPIC_ALIASES.get(x,[TOPICS.get(x,x)])))
        encoded = (enrich_row(original, algorithm_evidence={
            'source': entry.get('articles', {}).get('default', entry['url']), 'tags': tags, 'verified': True})
                   if tags else copy.deepcopy(original))
        estimated = entry.get('difficultyEstimated', True)
        evidence = [entry['url'], entry['difficultyReason'],
                    'ToBe training reference estimate; not a Nowcoder official rating.' if estimated
                    else 'Verified original-platform rating for the explicitly matched task.']
        origin = entry.get('ratingOrigin') or entry.get('origin')
        if origin:
            evidence.extend([origin['url'], 'Verified identical task: ' + origin.get('id', origin.get('platform', 'original source')),
                             str(origin.get('difficultySource') or '')])
        encoded.update(difficulty=entry['difficulty'], difficultyEstimated=estimated,
                       difficultySource=('ToBe 同题复核估算' if origin else 'ToBe 题面与算法复核估算')
                                        if estimated else ('牛客公开题库数值评级' if (origin or {}).get('platform') == 'Nowcoder'
                                                           else (origin or {}).get('platform', '原站') + ' 同题官方评级'),
                       difficultyConfidence='MEDIUM' if estimated else 'HIGH',
                       difficultyBand=[max(800, entry['difficulty'] - 200), entry['difficulty'] + 200]
                                      if estimated else [entry['difficulty'], entry['difficulty']],
                       difficultyEvidence=evidence, difficultyCheckedAt='2026-11-08',
                       **({'solutionAvailable': True,
                           'detailedSolutionAvailable': 'detailed' in entry['articles'],
                           'editorialVariants': list(entry['articles']),
                           'solutionState': 'available',
                           'editorialTopics': entry['knowledge']} if identity in ledger else {}))
        encoded=round_difficulty(encoded)
        encoded['knowledgeReviewRequired']=not bool(encoded.get('tags') or encoded.get('knowledgeCategories'))
        row['encoded'] = encoded
        row['raw']['难度'] = str(encoded['difficulty'])
        row['raw']['知识点'] = encoded['knowledge']
    for table, variant in [('solutions', 'default'), ('detailed_solutions', 'detailed')]:
        updated = {row['problem_id']: row for row in after[table]}
        for identity, entry in ledger.items():
            if variant not in entry['articles']:
                continue
            current = updated.get(identity)
            incoming = article(entry, variant)
            if current and not current['source_path'].startswith('data/nowcoder-editorials/'):
                assert current == incoming, 'Preserve an existing independent editorial: ' + identity
            updated[identity] = incoming
        after[table] = sorted(updated.values(), key=lambda row: row['problem_id'])
    after['meta']['nowcoderEditorialRevision'] = str(len(ledger))
    after['meta']['revision'] = str(int(before['meta'].get('revision', '0')) + 1)
    for name in ['problems', 'solutions', 'detailed_solutions']:
        key = 'id' if name == 'problems' else 'problem_id'
        original = {x[key]: x for x in before[name]}
        actual = {x[key]: x for x in after[name]}
        assert set(original) <= set(actual)
        mutable = reviews if name == 'problems' else ledger
        assert all(row == actual[identity] for identity, row in original.items() if identity not in mutable), name
    for name in names:
        if after[name] != before[name]:
            source_dump(source / (name + '.json'), after[name])
    destination = ROOT / 'data/library.sqlite3'
    # Build on the system temporary drive: E: may not have room for SQLite's
    # transaction journal beside a second gigabyte-sized public seed.
    stage_dir = Path(tempfile.mkdtemp(prefix='tobe-nowcoder-build-')).resolve()
    assert stage_dir.is_relative_to(Path(tempfile.gettempdir()).resolve())
    assert stage_dir.name.startswith('tobe-nowcoder-build-')
    stage = stage_dir / 'candidate.sqlite3'
    print(json.dumps({'temporaryBuildDirectory': str(stage_dir)}), flush=True)
    built = LibraryDatabase.from_source(source, stage)
    counts = built.check()
    incoming = destination.with_name('library.nowcoder-incoming.sqlite3')
    if incoming.exists():
        public_artifact_only(incoming)
        incoming.unlink()
    retired = False
    backup = stage_dir / 'previous-public-seed.sqlite3'
    if destination.exists() and shutil.disk_usage(destination.parent).free < stage.stat().st_size + 32 * 1024 * 1024:
        public_artifact_only(destination)
        shutil.copy2(destination, backup)
        assert file_digest(destination) == file_digest(backup)
        destination.unlink()
        retired = True
    try:
        shutil.copy2(stage, incoming)
        assert file_digest(stage) == file_digest(incoming)
        incoming.replace(destination)
    except Exception:
        if incoming.exists():
            incoming.unlink()
        if retired and not destination.exists():
            shutil.copy2(backup, destination)
        raise
    report = {'reviewedProblems': len(ledger), 'defaultArticles': sum('default' in x['articles'] for x in ledger.values()),
               'detailedArticles': sum('detailed' in x['articles'] for x in ledger.values()),
               'scopeProblems': audit['uniqueOriginalProblems'],
               'pending': audit['difficultyReviewPending'] + audit['editorialsPending'],
               'excludedAbove2300': audit['excludedAbove2300'],
               'counts': counts, 'unrelatedSourceRowsPreserved': True, 'personalDatabasesOpened': False}
    write(OUT / 'materialization.json', report)
    assert stage_dir.is_relative_to(Path(tempfile.gettempdir()).resolve())
    assert stage_dir.name.startswith('tobe-nowcoder-build-')
    shutil.rmtree(stage_dir)
    print(json.dumps(report, ensure_ascii=False))


def readers():
    from library import LibraryDatabase
    from store import Store
    ledger = checked_entries()
    os_state = OUT / 'reader-state'
    store = Store(data_file=os_state / 'absent.md', library_file=ROOT / 'data/library.sqlite3',
                  history_file=os_state / 'history.jsonl')
    assets = 0
    for identity, entry in ledger.items():
        value = store.solution(identity)
        assert value['markdown'] == (ROOT / entry['articles']['default']).read_text(encoding='utf-8')
        assert sha(program(value['markdown'])) == entry['programSha256']
        if 'detailed' in entry['articles']:
            assert value['detailedSolution']['markdown'] == (ROOT / entry['articles']['detailed']).read_text(encoding='utf-8')
        for reference, data in value['images'].items():
            assert reference in value['markdown'] and data.startswith('data:image/')
            assets += 1
        assert store.library.find(identity)['encoded']['difficulty'] == entry['difficulty']
    repaired = list((CONTENT / 'statements').glob('NC*.json'))
    for path in repaired:
        expected = read(path)
        assert store.library.statement(expected['id'])['markdown'] == expected['markdown']
    fixture_context = tempfile.TemporaryDirectory(prefix='tobe-nowcoder-reader-')
    fixture = Path(fixture_context.name).resolve()
    assert fixture.is_relative_to(Path(tempfile.gettempdir()).resolve())
    assert fixture.name.startswith('tobe-nowcoder-reader-')
    old = LibraryDatabase(fixture / 'old-seed.sqlite3')
    with old.connection() as target, database() as baseline:
        fixture_ids = list(dict.fromkeys(['ABC 469::A', next(iter(ledger)), *[read(path)['id'] for path in repaired]]))
        for identity in fixture_ids:
            row = baseline.execute('SELECT * FROM problems WHERE id=?', (identity,)).fetchone()
            target.execute('INSERT OR REPLACE INTO problems VALUES(?,?,?,?)', tuple(row))
        for path in repaired:
            row = baseline.execute('SELECT * FROM statements WHERE problem_id=?', (read(path)['id'],)).fetchone()
            target.execute('INSERT OR REPLACE INTO statements VALUES(?,?)', tuple(row))
        for table in ['solutions', 'detailed_solutions']:
            row = baseline.execute('SELECT * FROM ' + table + ' WHERE problem_id=?', ('ABC 469::A',)).fetchone()
            target.execute('INSERT OR REPLACE INTO ' + table + ' VALUES(?,?,?,?,?)', tuple(row))
    upgraded = LibraryDatabase(fixture / 'upgrade-reader.sqlite3')
    upgraded.merge_seed(old.path)
    note = 'Private editorial annotation retained.'
    with upgraded.connection() as db:
        db.execute('UPDATE solutions SET markdown=?,digest=? WHERE problem_id=?', (note, sha(note), 'ABC 469::A'))
        db.execute('CREATE TABLE IF NOT EXISTS private_fixture(key TEXT PRIMARY KEY,value TEXT)')
        for key, value in [('draft', 'int main() { return 7; }'), ('submission', 'prior official receipt'),
                           ('training', 'prior original training state')]:
            db.execute('INSERT OR REPLACE INTO private_fixture VALUES(?,?)', (key, value))
    upgraded.merge_seed(ROOT / 'data/library.sqlite3')
    assert upgraded.solution('ABC 469::A')['markdown'] == note
    for identity in ledger:
        assert upgraded.solution(identity)['markdown'] == store.solution(identity)['markdown']
    for path in repaired:
        expected = read(path)
        assert upgraded.statement(expected['id'])['markdown'] == expected['markdown']
    with upgraded.connection() as db:
        assert dict(db.execute('SELECT * FROM private_fixture')) == {
            'draft': 'int main() { return 7; }', 'submission': 'prior official receipt',
            'training': 'prior original training state'}
    report = {'readerProblems': len(ledger), 'embeddedAssets': assets, 'repairedPdfStatements': len(repaired), 'storeReaderPassed': True,
               'seedUpgradePassed': True, 'privateAnnotationAndRecordsPreserved': True,
               'livePersonalDatabasesOpened': False}
    write(OUT / 'readers.json', report)
    fixture_context.cleanup()
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['materialize', 'readers', 'inventory'])
    args = parser.parse_args()
    if args.action == 'materialize':
        materialize()
    elif args.action == 'readers':
        readers()
    else:
        result = inventory(read(CONTENT / 'reviewed.json'))
        print(json.dumps({k: v for k, v in result.items() if k != 'problems'}, ensure_ascii=False))
