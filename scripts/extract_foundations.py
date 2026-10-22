"""Extract reviewed foundations from public editorials, without authoring prose.

Dry run by default. --write appends lessons and exact source relationships to
data/library, backs up changed sources, and never opens a personal database or
writes to the original educational archive.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/common')]
from knowledge import canonical_tag, category_path
from lecture_curation import code_hashes, parse_document, plain_text, quality


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def extract(source, manifest):
    """Return additions only; keep every existing lesson and source byte."""
    source = Path(source)
    problems = {row['id']: row['encoded'] for row in load(source / 'problems.json')}
    editorials = {row['problem_id']: row for row in load(source / (manifest['sourceVariant'] + '.json'))}
    existing = load(source / 'lectures.json')
    existing_ids = {row['id'] for row in existing}
    links = load(source / 'links.json')
    owned = {(row['problem_id'], row['lecture_id']) for row in links}
    additions, new_links = [], []
    selected = set()
    for specification in manifest['lessons']:
        problem_id = specification['problemId']
        row, problem = editorials[problem_id], problems[problem_id]
        difficulty = problem.get('difficulty')
        if isinstance(difficulty, bool) or not isinstance(difficulty, (int, float)) or difficulty > 2200:
            raise ValueError('Unknown/out-of-scope difficulty: ' + problem_id)
        knowledge = specification['knowledgeName']
        if canonical_tag(knowledge) != knowledge:
            raise ValueError('Noncanonical knowledge name: ' + knowledge)
        if (problem_id, knowledge) in selected:
            raise ValueError('Duplicate extraction: ' + problem_id)
        selected.add((problem_id, knowledge))
        headings = parse_document(row['markdown'])['headings']
        idea = next(h for h in headings if h['level'] == 3 and h['title'] == '思路')
        statement = next(h for h in headings if h['level'] == 3 and h['title'] == '题意')
        if len(idea['body']) < 300 or not statement['body']:
            raise ValueError('A self-contained derivation and problem context are required: ' + problem_id)
        identity = 'lecture:' + hashlib.sha256(('editorial-foundation-v1\n' + problem_id + '\n' + knowledge).encode()).hexdigest()[:24]
        topic = specification['topic']
        concept = knowledge + '：' + topic
        tags = list(dict.fromkeys([knowledge] + [tag for tag in problem.get('tags', []) if canonical_tag(tag) == tag]))
        # Include images as portable data, retaining the editorial's exact keys.
        # Source metadata contains only portable relative public paths.
        path = Path(row['source_path'])
        if path.is_absolute() or ':' in row['source_path'] or '..' in path.parts:
            raise ValueError('Nonportable source path: ' + row['source_path'])
        markdown = '# ' + concept + '\n\n## 题目中的问题\n\n' + statement['body'] + '\n\n## 从零讲\n\n' + idea['body'] + '\n'
        content = {
            'id': identity, 'available': True, 'title': '从零讲：' + topic,
            'concept': concept, 'displayTitle': concept, 'knowledgeName': knowledge,
            'topic': topic, 'category': category_path(knowledge),
            'categories': list(dict.fromkeys(category_path(tag) for tag in tags)),
            'tags': tags, 'sourceTags': problem.get('tags', []), 'catalogTags': problem.get('tags', []),
            'sourceProblemIds': [problem_id], 'sourceContest': problem.get('contest') or problem_id.split('::')[0],
            'sourceProblem': problem.get('problem'), 'sourceTitle': problem.get('title'),
            'sourcePath': row['source_path'], 'sourceVariant': manifest['sourceVariant'],
            'sourceHeading': idea['title'], 'originalTitle': idea['title'], 'originalConcept': topic,
            'editorialVersion': manifest['version'], 'curationVersion': 'lectures-v1.1',
            'conceptSource': 'reviewed-editorial-extraction',
            'sourceMarkdown': idea['markdown'], 'sourceHash': hashlib.sha256(idea['markdown'].encode()).hexdigest(),
            'sourceCodeHashes': code_hashes(idea['markdown']), 'markdown': markdown,
            'images': row.get('images', {}), 'excerpt': plain_text(idea['body'])[:180],
            'quality': {'original': quality(idea['body'], knowledge), 'normalized': True,
                        'supplemented': False, 'sourceAlgorithmReverified': False,
                        'catalogClassificationChanged': knowledge not in problem.get('tags', [])},
        }
        if identity not in existing_ids:
            additions.append({'id': identity, 'content': content})
            existing_ids.add(identity)
        if (problem_id, identity) not in owned:
            positions = [link['position'] for link in links + new_links if link['problem_id'] == problem_id]
            new_links.append({'problem_id': problem_id, 'lecture_id': identity, 'kind': 'own', 'position': max(positions, default=-1) + 1})
            owned.add((problem_id, identity))
    return additions, new_links


def apply(source, manifest):
    source = Path(source)
    additions, new_links = extract(source, manifest)
    report = {'version': manifest['version'], 'reviewed': len(manifest['lessons']), 'added': len(additions), 'linksAdded': len(new_links)}
    if not additions and not new_links:
        return report
    backup = ROOT / '.backups' / ('foundation-extraction-' + dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    backup.mkdir(parents=True)
    for name in ('lectures', 'links', 'meta'):
        shutil.copy2(source / (name + '.json'), backup / (name + '.json'))
    lessons = load(source / 'lectures.json') + additions
    links = load(source / 'links.json') + new_links
    meta = load(source / 'meta.json')
    audit = json.loads(meta.get('lectureAudit', '{}'))
    audit['lectureCount'] = len(lessons)
    audit['normalizedLectureCount'] = sum(bool(row['content'].get('quality', {}).get('normalized')) for row in lessons)
    audit['extractedEditorialFoundations'] = [row['id'] for row in lessons if row['content'].get('conceptSource') == 'reviewed-editorial-extraction']
    meta['lectureAudit'] = json.dumps(audit, ensure_ascii=False)
    meta['foundationExtractionVersion'] = manifest['version']
    for name, content in (('lectures', sorted(lessons, key=lambda row: row['id'])), ('links', sorted(links, key=lambda row: (row['problem_id'], row['position']))), ('meta', meta)):
        (source / (name + '.json')).write_text(json.dumps(content, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8', newline='\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'data/library')
    parser.add_argument('--manifest', type=Path, default=ROOT / 'data/foundation_extractions.json')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    manifest = load(args.manifest)
    if args.write:
        print(json.dumps(apply(args.source, manifest), ensure_ascii=False))
    else:
        lessons, links = extract(args.source, manifest)
        print(json.dumps({'reviewed': len(manifest['lessons']), 'missingLessons': len(lessons), 'missingLinks': len(links), 'topics': [row['content']['displayTitle'] for row in lessons]}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
