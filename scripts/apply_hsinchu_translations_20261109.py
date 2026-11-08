"""Bind four page-reviewed translations and original diagrams to their PDF seed."""
from pathlib import Path
import base64
import copy
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/common')]
from statement_resources import inspect_resource
from statement_seed import checksum, load_statements
from translation import TRANSLATION_FORMAT, bundled_translation


def apply():
    folder = ROOT / 'content-updates/20261109-hsinchu'
    current = {row['problem_id']: row['content'] for row in load_statements(ROOT / 'data/library')}
    reviewed = json.loads((folder / 'review.json').read_text('utf8'))
    updated = []
    for proof in reviewed:
        letter = proof['letter']
        assert letter in 'CFGH'
        identity = f'remote:codeforces:102835::{letter}'
        before = current[identity]
        english = (folder / f'102835-{letter}.en.md').read_text('utf8')
        chinese = (folder / f'102835-{letter}.zh.md').read_text('utf8')
        samples = json.loads((folder / f'102835-{letter}.samples.json').read_text('utf8'))
        assert samples['sourcePdfSha256'] == proof['pdfSha256'] == before['statementPdf']['sha256']
        assert proof['pagesReviewed'] == list(range(1, proof['pageCount'] + 1))
        assert proof['sourcePageNumbers'] == samples['pages'] == before['statementPdf']['sourcePageNumbers']
        assert samples['samples'] == before['samples']
        for sample in before['samples']:
            for text in (english, chinese):
                for key in ('input', 'output'):
                    assert '\n```text\n' + sample[key] + '\n```' in text
        target = ROOT / f'data/library/statement-patches/zzzzzzzzzzzzzzzz-20261109-hsinchu-{letter}.json'
        if target.exists():
            stored = json.loads(target.read_text('utf8'))['statements'][0]['content']
            assert stored == before and stored['sourceText'] == english
            assert stored['translation']['markdown'] == chinese and bundled_translation(stored)
            continue
        assert not before.get('translation')
        value = copy.deepcopy(before)
        old_text = value.get('sourceText', '')
        value.setdefault('sourceTextArchive', []).append({
            'kind': 'unreviewed-pdf-extraction', 'text': old_text,
            'sha256': hashlib.sha256(old_text.encode()).hexdigest(),
        })
        value['sourceText'] = english
        review = {**proof, 'method': 'page-by-page-original-pdf-review',
                  'sourceTextSha256': hashlib.sha256(english.encode()).hexdigest()}
        value['sourceTextReview'] = review
        value.setdefault('translationReviewHistory', []).append({
            key: value[key] for key in ('translationReview', 'translationNotice', 'translationAvailable') if key in value
        })
        value.pop('translationNotice', None)
        value['translationAvailable'] = True
        value['translation'] = {
            'kind': 'bundled', 'provider': '逐页核对原始 PDF 的预置中文译文',
            'format': TRANSLATION_FORMAT, 'sourceLanguage': 'en', 'targetLanguage': 'zh-CN',
            'sourceHash': hashlib.sha256(value['markdown'].encode()).hexdigest(),
            'inputKind': 'pdf-text', 'sourceTextHash': review['sourceTextSha256'],
            'sourcePdfSha256': proof['pdfSha256'], 'markdown': chinese,
        }
        figures = {row['file']: row for row in proof['figures']}
        assert set(re.findall(r'!\[[^\]]*\]\(([^)]+)\)', english)) == set(figures)
        assert set(re.findall(r'!\[[^\]]*\]\(([^)]+)\)', chinese)) == set(figures)
        for name, figure in figures.items():
            assert Path(name).name == name and figure['page'] in proof['pagesReviewed']
            raw = (folder / name).read_bytes()
            entry = inspect_resource(raw, before['statementPdf']['sourceUrl'], 'image')
            entry.update(derivedFromPdfSha256=proof['pdfSha256'], kind='reviewed-original-diagram',
                         sourcePage=figure['page'], clipRect=figure['clipRect'])
            value.setdefault('images', {})[name] = 'data:' + entry['mime'] + ';base64,' + base64.b64encode(raw).decode('ascii')
            value.setdefault('resourceManifest', {})[name] = entry
        assert bundled_translation(value), 'Immutable-span validation failed: ' + identity
        value['translationReview'] = {**review, 'status': 'complete', 'immutableSpansValidated': True}
        assert all(value[key] == before[key] for key in ('id', 'url', 'markdown', 'statementPdf', 'samples', 'limits'))
        target.write_text(json.dumps({'schema': 1, 'statements': [{
            'problem_id': identity, 'beforeSha256': checksum(before), 'content': value,
        }]}, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        updated.append(identity)
    print(json.dumps({'updated': updated, 'reviewedProblems': len(reviewed),
                      'originalPdfsRetained': True, 'samplesRetained': True}, ensure_ascii=False))


if __name__ == '__main__':
    apply()
