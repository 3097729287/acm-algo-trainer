"""Apply reviewed Chinese translations without changing the source or its resources."""
import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/common')]
from statement_seed import checksum, load_statements
from translation import TRANSLATION_FORMAT, bundled_translation


def sha(text):
    return hashlib.sha256(text.encode('utf8')).hexdigest()


def main(folder, packet_prefix):
    assert re.fullmatch(r'z+-[A-Za-z0-9-]+', packet_prefix)
    reviews = json.loads((folder / 'review.json').read_text('utf8'))
    current = {row['problem_id']: row['content'] for row in load_statements(ROOT / 'data/library')}
    applied = []
    for review in reviews:
        identity, slug = review['problemId'], review['slug']
        assert re.fullmatch(r'\d+-[A-Z][0-9]?', slug)
        source = (folder / (slug + '.en.md')).read_text('utf8')
        chinese = (folder / (slug + '.zh.md')).read_text('utf8')
        before = current[identity]
        assert not before.get('statementPdf'), identity
        assert before['markdown'] == source and sha(source) == review['sourceSha256'], identity
        assert before['url'] == review['sourceUrl'] and review['status'] == 'complete'
        assert before['samples'] == review['samples']
        image_names = set(re.findall(r'!\[[^\]]*\]\(([^)]+)\)', source))
        assert image_names == set(re.findall(r'!\[[^\]]*\]\(([^)]+)\)', chinese))
        assert image_names <= set(before.get('images', {})), identity
        target = ROOT / 'data/library/statement-patches' / (packet_prefix + '-' + slug + '.json')
        if target.exists():
            stored = json.loads(target.read_text('utf8'))['statements'][0]['content']
            assert before == stored and stored['translation']['markdown'] == chinese
            assert bundled_translation(stored), identity
            continue
        assert not before.get('translation'), identity
        value = copy.deepcopy(before)
        value['translationAvailable'] = True
        value['translation'] = {
            'kind': 'bundled', 'provider': '核对完整原题的预置中文译文', 'format': TRANSLATION_FORMAT,
            'sourceHash': sha(source), 'sourceLanguage': 'en', 'targetLanguage': 'zh-CN',
            'inputKind': 'markdown', 'markdown': chinese,
        }
        assert bundled_translation(value), identity + ' failed complete immutable-span validation'
        value['translationReview'] = dict(review, method='complete-original-markdown-review', immutableSpansValidated=True)
        for key in before:
            if key != 'translationAvailable':
                assert value[key] == before[key], (identity, key)
        packet = {'schema': 1, 'statements': [{'problem_id': identity, 'beforeSha256': checksum(before), 'content': value}]}
        target.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        applied.append(identity)
    print(json.dumps({'newTranslations': len(applied), 'reviewedTotal': len(reviews), 'problems': applied}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, required=True)
    parser.add_argument('--packet-prefix', required=True)
    args = parser.parse_args()
    main(args.folder.resolve(strict=True), args.packet_prefix)
