"""Export public statements for the application's actual Markdown renderer.

Requires an explicit public seed and refuses personal data. The JSON can be
checked offline with frontend/tests/statement-corpus.mjs; no source is changed.
"""
import argparse
from collections import Counter
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from statement_cleanup import clean_statement
from translation import bundled_translation,needs_translation,validate_translation,TranslationIncomplete


def export(library,directory):
    directory.mkdir(parents=True,exist_ok=True)
    rows=[];counts=Counter();incomplete=[];review=[]
    with closing(sqlite3.connect(library.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if tables&{'accounts','drafts','submissions','training','documents'}:raise ValueError('Use a public seed')
        metadata={r[0]:json.loads(r[1]) for r in db.execute('SELECT id,encoded FROM problems')}
        for identity,raw in db.execute('SELECT problem_id,content FROM statements'):
            meta=metadata[identity];value=clean_statement(json.loads(raw))
            if meta.get('catalogHidden') or meta.get('statementRetired') or not value.get('statementAvailable'):
                counts['unavailableOrHidden']+=1;continue
            counts['visible']+=1
            rows.append({'id':identity,'title':value.get('title'),'markdown':value.get('markdown') or '',
                         'samples':value.get('samples') or [],'nativePdf':bool(value.get('statementPdf'))})
            translation=value.get('translation') or {}
            if translation.get('kind')=='bundled':translation=bundled_translation(value) or {}
            if translation.get('markdown'):
                counts['chinese']+=1
                rows.append({'id':identity+'\tzh','title':value.get('title'),'markdown':translation['markdown'],
                             'samples':value.get('samples') or [],'nativePdf':bool(translation.get('statementPdf'))})
                original=value.get('sourceText') if translation.get('inputKind')=='pdf-text' else value.get('markdown') or ''
                if needs_translation({'markdown':original,'statementAvailable':True,'translationAvailable':True}):
                    try:validate_translation(original,translation['markdown'])
                    except TranslationIncomplete:review.append({'id':identity,'reason':'prose-validator-review','kind':translation.get('kind')})
            elif value.get('statementPdf') and value.get('translationAvailable') is False:
                counts['originalPdfOnly']+=1
            elif needs_translation(dict(value,translation=None,translationAvailable=True)):
                incomplete.append({'id':identity,'reason':'missing-chinese'})
                counts['missingChinese']+=1
    for part in range(3):
        (directory/f'render-{part}.json').write_text(json.dumps(rows[part::3],ensure_ascii=False),encoding='utf8')
    result={'counts':dict(counts),'incomplete':incomplete,'reviewRequired':review}
    (directory/'coverage.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'documents':len(rows),**counts,'incomplete':len(incomplete)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();export(args.library,args.output)
