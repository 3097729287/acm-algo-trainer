"""Inventory every existing editorial; static signals never certify teaching.

Only an individually authored, hash-matched review can set reviewed=True. The
queue deliberately retains articles without machine flags: absence of a regex
match does not establish that a beginner can follow the proof.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/library'
REPORT = ROOT / 'data/editorial-reasoning-review.json'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def authored_text(markdown):
    return re.sub(r'<!-- reusable-foundations:start -->.*?<!-- reusable-foundations:end -->',
                  '', markdown, flags=re.S)


def main_reasoning(markdown):
    text = authored_text(markdown)
    text = re.sub(r'^(`{3,}|~{3,})[^\n]*\n.*?^\1\s*$', '', text, flags=re.S | re.M)
    # Exclude introductory independent lessons from the proof assessment.
    sections = re.split(r'(?=^#{2,6} )', text, flags=re.M)
    result = []
    excluded_level = None
    for section in sections:
        heading = re.match(r'^(#{2,6})\s+([^\n]+)', section)
        if not heading:
            continue
        level, title = len(heading[1]), heading[2]
        if excluded_level and level > excluded_level:
            continue
        excluded_level = None
        if level == 2:
            continue
        if re.search(r'从零讲|^题意|^原题|^参考代码|^代码实现|^代码$', title):
            excluded_level = level
            continue
        result.append(section.strip())
    return '\n\n'.join(result)


def reference_programs(markdown):
    return re.findall(r'^```(?:cpp|c\+\+)\s*\n(.*?)^```\s*$', markdown, re.S | re.M)


def inventory():
    problems = {row['id']: row['encoded'] for row in load(SOURCE / 'problems.json')}
    old = {row['problemId']: row for row in load(REPORT)['problems']} if REPORT.exists() else {}
    variants = {name: {row['problem_id']: row for row in load(SOURCE / (name + '.json'))}
                for name in ['solutions', 'detailed_solutions']}
    assert variants['solutions'].keys() == variants['detailed_solutions'].keys()
    items = []
    for identity in variants['solutions']:
        problem = problems[identity]
        results = {}
        for variant, rows in variants.items():
            row = rows[identity]
            markdown = row['markdown']
            proof = main_reasoning(markdown)
            programs = reference_programs(markdown)
            code = '\n'.join(programs)
            # Comments/string contents are not executable branches.
            code = re.sub(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', ' ', code, flags=re.S)
            updates = [line.strip() for line in code.splitlines()
                       if re.search(r'\b(?:ans|answer|res|cnt)\s*(?:\+\+|\+=)|\+\+\s*(?:ans|answer|res|cnt)\b', line)]
            compound = [line.strip() for line in code.splitlines() if re.search(r'\bif\b', line) and re.search(r'&&|\|\|', line)]
            figures = [key for key in row.get('images', {}) if key in authored_text(markdown)]
            signals = []
            if updates:
                signals.append('answer-update-needs-object-and-counting-proof')
            if compound:
                signals.append('compound-condition-needs-term-by-term-explanation')
            if len(proof) < 650:
                signals.append('short-main-reasoning-check-for-missing-steps')
            if not re.search(r'例如|比如|举例|样例|手算|取\s*\$|\[[0-9,， ]+\]', proof):
                signals.append('check-for-problem-specific-worked-example')
            previous = old.get(identity, {}).get('variants', {}).get(variant, {})
            digest = sha(markdown)
            reviewed = bool(previous.get('reviewed') and previous.get('markdownSha256') == digest)
            results[variant] = dict(markdownSha256=digest, referenceSha256=sha('\n'.join(programs)),
                                   mainReasoningCharacters=len(proof), mainFigureKeys=figures,
                                   answerUpdates=updates, compoundConditions=compound,
                                   machineSignals=signals, reviewed=reviewed)
            if reviewed:
                for key in ['reviewNotes', 'validation']:
                    results[variant][key] = previous[key]
        items.append(dict(problemId=identity, title=problem.get('title'), difficulty=problem.get('difficulty'),
                          url=problem.get('url'), variants=results,
                          reviewStatus='reviewed' if all(v['reviewed'] for v in results.values()) else 'pending'))
    items.sort(key=lambda item: (item['reviewStatus'] == 'reviewed',
                                not any(v['answerUpdates'] for v in item['variants'].values()),
                                -sum(len(v['compoundConditions']) for v in item['variants'].values()),
                                item['problemId']))
    return dict(version=1, scope='All existing default and detailed editorials; no personal databases or original archive.',
                criteria='Each decisive condition/update has a problem-specific derivation, concrete trace or diagram, and proof of what is counted/optimized. Machine signals only order review.',
                problemCount=len(items), articleCount=2 * len(items),
                reviewedProblems=sum(item['reviewStatus'] == 'reviewed' for item in items),
                reviewedArticles=sum(v['reviewed'] for item in items for v in item['variants'].values()),
                machineSignalCounts=dict(Counter(s for item in items for v in item['variants'].values() for s in v['machineSignals'])),
                problems=items)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    report = inventory()
    if args.write:
        if REPORT.exists():
            import shutil
            backup = ROOT / '.backups/editorial-reasoning-20261022/before' / REPORT.relative_to(ROOT)
            backup.parent.mkdir(parents=True, exist_ok=True)
            if not backup.exists():
                shutil.copy2(REPORT, backup)
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key != 'problems'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
