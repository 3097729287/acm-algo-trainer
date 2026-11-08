"""Import the isolated native-source review, preserving all earlier snapshots.

Requires actual Markdown and native PDF UI receipts. Runtime/library builds use
the resulting guarded source packets and asset parts, never this authoring cache.
"""
import argparse
import copy
import datetime
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/common')]
from codeforces_pdf import normalized
from contest_scope import excluded
from statement_asset_store import dehydrate
from statement_integrity import annotate_type, content_complete, native_submission_supported
from statement_seed import checksum, load_statements


def read(path):
    return json.loads(path.read_text('utf8'))


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n',
                    encoding='utf8', newline='\n')


def main(stage):
    source = ROOT / 'data/library'
    target = source / 'statement-patches/zzzzzzzzzz-20261108-native-originals.json'
    receipt_path = ROOT / 'docs/verification/native-originals-20261108.json'
    if target.exists():
        current = {r['problem_id']: r['content'] for r in load_statements(source)}
        for entry in read(target)['statements']:
            assert current[entry['problem_id']] == entry['content'], 'A later repair needs a new guarded packet'
        print('Existing native-source packet verified; no files changed.')
        return
    rendered = read(stage / 'original-render-result.json')
    assert not rendered['issues']
    native = read(stage / 'original-native-result.json')
    assert native['externalRequests'] == 0
    pdf_ui = {r['id']: r for r in native['verified']}
    new_rows = read(stage / 'new-xcpc-rosters.json')['newProblems']
    recovered = [r for r in read(stage / 'original-recovery-progress.json')['results'] if r['ready']]
    assert len(new_rows) == 63 and len(recovered) == 33
    problems = read(source / 'problems.json')
    by_id = {r['id']: r for r in problems}
    statements = {r['problem_id']: r['content'] for r in load_statements(source)}
    assets = {r['sha256']: r for r in read(source / 'statement_assets.json')}
    parts = read(source / 'statement_asset_parts.json')
    new_assets = {}
    patches = []
    proofs = []
    corrections = {r['id']: r for r in (read(p) for p in
        (ROOT / 'content-updates/20261108-xcpc').glob('*.samples.json'))}

    def save(sha, mime, data):
        assert hashlib.sha256(data).hexdigest() == sha
        if sha in assets:
            assert assets[sha]['bytes'] == len(data)
        elif sha in new_assets:
            assert new_assets[sha][1] == data
        else:
            new_assets[sha] = (mime, data)

    incoming = []
    for row in new_rows:
        assert row['id'] not in by_id and not excluded(row)
        assert not any(r['url'] == row['url'] for r in problems)
        raw = {'_id': row['id'], '_url': row['url'], '_platform': row['platform'], '_series': row['series'],
               '场次': row['contest'], '题号': row['problem'], '题名': row['title'],
               '知识点': row.get('knowledge', ''), '难度': '—', '状态': '未做', '日期': ''}
        record = {'id': row['id'], 'url': row['url'], 'raw': raw, 'encoded': copy.deepcopy(row)}
        record['encoded'].update(difficultyEstimated=False, difficultyConfidence='UNKNOWN', knowledgeReviewRequired=True)
        problems.append(record);by_id[row['id']] = record
        incoming.append((row['id'], 'new', stage / 'new-xcpc-statements'))
    incoming += [(row['id'], 'recovered', stage / 'original-recovery') for row in recovered]

    for identity, disposition, directory in incoming:
        value = read(directory / (identity.replace(':', '-') + '.json'))
        record = by_id[identity];encoded = record['encoded']
        assert value['id'] == identity and value['url'] == record['url']
        assert value['integrity']['status'] == 'complete' and content_complete(value)
        proof = {'id': identity, 'url': value['url'], 'disposition': disposition,
                 'method': 'native-source-identity-resource-and-render-verification'}
        if value.get('statementPdf'):
            pdf = value['statementPdf'];actual = pdf_ui[identity]
            assert actual['sha256'] == pdf['sha256'] and actual['pages'] == pdf['pageCount']
            if disposition == 'recovered':
                assert normalized(value['title']) in normalized(value['sourceText'][:1500])
            proof.update(pdfSha256=pdf['sha256'], pages=pdf['pageCount'], allPagesRendered=True,
                         sourcePdfSha256=value['sourcePdfSha256'], sourcePdfUrl=value['sourcePdfUrl'])
        if identity in corrections:
            correction = corrections[identity]
            assert correction['sourcePdfSha256'] == value['statementPdf']['sha256']
            value.setdefault('sampleExtractionHistory', []).append({
                'samples': value['samples'], 'extraction': value.get('sampleExtraction')})
            value['samples'] = correction['samples']
            value['sampleExtraction'] = {k: v for k, v in correction.items() if k != 'samples'}
            proof['sampleCorrection'] = value['sampleExtraction']
        # These eleven native documents are Chinese; the compact Markdown only
        # contains the PDF link and cannot itself identify the original language.
        if re.fullmatch(r'xcpc-qoj::229(?:1[0-9]|20)', identity):
            assert len(re.findall(r'[\u3400-\u9fff]', value['sourceText'])) > 100
            value['statementLanguage'] = 'zh-CN'
        value = annotate_type(value)
        if not value['samples']:
            assert value['problemType'] in {'interactive', 'communication'}, identity
        previous = statements.get(identity)
        if previous:
            # Preserve the exact earlier educational snapshot, including notices
            # and original resources. No personal records exist in this seed.
            value.setdefault('previousStatementSnapshots', []).append({
                'sha256': checksum(previous), 'content': previous})
            if previous.get('translation') and not value.get('translation'):
                raise ValueError('A reviewed translation needs explicit source reconciliation: ' + identity)
        value['integrity']['corpusAuditVerifiedSha256'] = hashlib.sha256(
            (value.get('currentSourceMarkdown') or value['markdown']).encode()).hexdigest()
        value['nativeSourceReview'] = proof
        if encoded.get('statementRetirementPolicy') == 'public-statement-audit-v1':
            prior = encoded.get('statementPriorVisibility') or {}
            for key in ('catalogHidden', 'catalogNotice', 'catalogVisibilityPolicy'):
                if key in prior:
                    encoded[key] = prior[key]
                else:
                    encoded.pop(key, None)
            for key in ('statementRetired', 'statementRetirementPolicy', 'statementRetirementReason', 'statementPriorVisibility'):
                encoded.pop(key, None)
        encoded.update(problemType=value['problemType'], catalogStatementReady=True,
                       catalogReplayReady=native_submission_supported(encoded['url'])
                       and value['problemType'] not in {'communication', 'output-only', 'attachment'}
                       and encoded.get('contestLetterVerified') is not False)
        proof.update(problemType=value['problemType'], samplePairs=len(value['samples']),
                     samplesSha256=checksum(value['samples']))
        patches.append({'problem_id': identity, 'beforeSha256': checksum(previous),
                        'content': dehydrate(value, save)})
        proofs.append(proof)

    # New content parts are additive. Every original part and asset stays intact.
    number = max((int(re.search(r'part-(\d+)', p['file'])[1]) for p in parts), default=0) + 1
    blob = bytearray();pending = []

    def flush():
        nonlocal blob, pending, number
        if not blob:
            return
        name = f'statement-assets/part-{number:04d}.bin'
        destination = source / name
        assert not destination.exists(), 'Refusing to overwrite an existing resource part'
        destination.write_bytes(blob)
        parts.append({'file': name, 'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()})
        for sha, mime, size, offset in pending:
            assets[sha] = {'sha256': sha, 'mime': mime, 'bytes': size, 'file': name, 'offset': offset}
        number += 1;blob = bytearray();pending = []

    for sha, (mime, data) in sorted(new_assets.items()):
        if len(blob) + len(data) > 24 * 1024 * 1024:
            flush()
        pending.append((sha, mime, len(data), len(blob)));blob.extend(data)
    flush()
    dump(source / 'statement_assets.json', list(assets.values()))
    dump(source / 'statement_asset_parts.json', parts)
    dump(source / 'problems.json', problems)
    dump(target, {'schema': 1, 'statements': sorted(patches, key=lambda row: row['problem_id'])})
    result = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'addedIdentities': len(new_rows), 'restoredOriginals': len(recovered),
              'newContests': len({r['contestId'] for r in new_rows}),
              'newResources': len(new_assets), 'newResourceBytes': sum(len(v[1]) for v in new_assets.values()),
              'markdownRenderIssues': 0, 'nativePdfsAllPagesRendered': len(pdf_ui),
              'externalUiRequests': 0, 'personalDatabasesChanged': 0, 'installed': False,
              'translationComplete': False, 'problems': proofs}
    dump(receipt_path, result)
    print(json.dumps({k: v for k, v in result.items() if k != 'problems'}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, required=True)
    main(parser.parse_args().stage.resolve(strict=True))
