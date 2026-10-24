"""Record explicitly accepted, individually read editorial packages.

This command does not infer teaching quality from tests or machine signals.
Call it only after reading every selected variant and inspecting its diagrams.
The renderer evidence and current source are checked to avoid stale acceptance.
Dry run is the default; --write records only these explicit package entries.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from audit_editorial_reasoning import ROOT, SOURCE, REPORT, inventory, load, sha

SAVE = ROOT / '.backups/editorial-reasoning-20261022'


def record(files, write=False):
    result = inventory()
    indexed = {row['problemId']: row for row in result['problems']}
    source = {variant: {row['problem_id']: row for row in load(SOURCE / (variant + '.json'))}
              for variant in ['solutions', 'detailed_solutions']}
    accepted = set()
    for file in files:
        package = load(file)
        batch = package['batch']
        assert all(char.isalnum() or char in '_-' for char in batch), batch
        evidence_path = SAVE / 'review-render' / (batch + '-report.json')
        evidence = load(evidence_path)
        assert evidence['batch'] == batch
        assert evidence['packageSha256'] == hashlib.sha256(file.read_bytes()).hexdigest(), batch
        assert evidence['errors'] == [], batch
        for item in package['problems']:
            identity = item['problemId']
            assert identity not in accepted, ('Duplicate acceptance', identity)
            accepted.add(identity)
            assert item['reviewNotes'] and item['validation'], identity
            assert set(item['variants']) == {'solutions', 'detailed_solutions'}, identity
            for variant, article in item['variants'].items():
                current = source[variant][identity]
                assert current['markdown'] == article['markdown'], (identity, variant, 'source drift')
                assert current['images'] == article['images'], (identity, variant, 'image drift')
                digest = sha(article['markdown'])
                frames = [frame for frame in evidence['frames']
                          if frame['problemId'] == identity and frame['variant'] == variant]
                assert len(frames) == 3 and {frame['width'] for frame in frames} == {1440, 1050, 390}, (identity, variant)
                assert all(frame['markdownSha256'] == digest for frame in frames), (identity, variant)
                for frame in frames:
                    for capture in frame['captures']:
                        assert (evidence_path.parent / capture).is_file(), capture
                reviewed = indexed[identity]['variants'][variant]
                reviewed.update(reviewed=True, reviewNotes=item['reviewNotes'], validation={
                    'batch': batch,
                    'individualReadingReview': 'Accepted after reviewing the problem-specific argument and diagrams; existing sufficient explanations may remain unchanged.',
                    'package': str(file.relative_to(ROOT)).replace('\\', '/'),
                    'numericalAndPreservation': item['validation'],
                    'readerEvidence': str(evidence_path.relative_to(ROOT)).replace('\\', '/'),
                    'readerWidths': [1440, 1050, 390],
                    'reviewedMarkdownSha256': digest,
                })
    for row in result['problems']:
        row['reviewStatus'] = 'reviewed' if all(value['reviewed'] for value in row['variants'].values()) else 'pending'
    result['reviewedProblems'] = sum(row['reviewStatus'] == 'reviewed' for row in result['problems'])
    result['reviewedArticles'] = sum(value['reviewed'] for row in result['problems'] for value in row['variants'].values())
    if write:
        backup = SAVE / 'before' / REPORT.relative_to(ROOT)
        backup.parent.mkdir(parents=True, exist_ok=True)
        if REPORT.exists() and not backup.exists():
            shutil.copy2(REPORT, backup)
        REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return dict(explicitlyAcceptedProblems=len(accepted), reviewedProblems=result['reviewedProblems'],
                reviewedArticles=result['reviewedArticles'], pendingProblems=result['problemCount'] - result['reviewedProblems'],
                dryRun=not write)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packages', nargs='+', type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    print(json.dumps(record([file.resolve() for file in args.packages], args.write), indent=2))


if __name__ == '__main__':
    main()
