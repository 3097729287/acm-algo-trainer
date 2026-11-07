"""Inventory the exact public library and text catalogue before filling gaps."""
import argparse
import collections
import datetime
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from translation import bundled_translation,needs_translation

def audit(library,destination):
    library=library.resolve(strict=True)
    rows=json.loads((ROOT/'data/library/problems.json').read_text('utf8'))
    with sqlite3.connect(library.as_uri()+'?mode=ro',uri=True) as db:
        statements={identity:json.loads(raw) for identity,raw in db.execute('SELECT problem_id,content FROM statements')}
        assert {row['id'] for row in rows}=={identity for identity, in db.execute('SELECT id FROM problems')}
    groups={name:[] for name in ['originals','translations','translation-disabled','translation-invalid','knowledge','difficulty']}
    counts=collections.Counter()
    for row in rows:
        identity=row['id'];encoded=row['encoded'];value=statements.get(identity,{})
        base={'id':identity,'url':row['url'],'title':encoded.get('title'),'platform':encoded.get('platform'),'contest':encoded.get('contestFullName') or encoded.get('contest')}
        if not value or value.get('integrity',{}).get('status')!='complete' or encoded.get('statementRetired'):
            groups['originals'].append(dict(base,issues=value.get('integrity',{}).get('issues') or ['missing-original'],available=bool(value.get('statementAvailable'))))
        else:
            counts['completeOriginals']+=1
        translation=value.get('translation') or {}
        prepared=None
        if translation.get('kind')=='bundled':
            prepared=bundled_translation(value)
            if not prepared:groups['translation-invalid'].append(base)
        elif translation.get('markdown'):prepared=translation
        if prepared:counts['usableChineseTranslations']+=1
        elif value:
            probe=dict(value,translation=None)
            if value.get('translationAvailable') is False:
                groups['translation-disabled'].append(dict(base,reason=value.get('translationUnavailableReason') or value.get('translationError') or 'withheld-unreliable-source-text'))
                probe['translationAvailable']=True
            if needs_translation(probe):groups['translations'].append(base)
        if not encoded.get('tags') or not encoded.get('knowledge') or encoded.get('knowledge') in {'待补充','未分类','未知'}:
            groups['knowledge'].append(dict(base,tags=encoded.get('tags'),knowledge=encoded.get('knowledge')))
        if not encoded.get('difficulty'):
            groups['difficulty'].append(dict(base,reason=encoded.get('difficultySource'),native=encoded.get('nativeDifficulty')))
        if str(encoded.get('source','')).startswith('xcpc') or encoded.get('series')=='XCPC':counts['xcpcProblems']+=1
    destination.mkdir(parents=True,exist_ok=True)
    summary={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceRoot':str(ROOT),'publicLibrary':str(library),'problems':len(rows),'statements':len(statements),**counts,'gaps':{name:len(values) for name,values in groups.items()}}
    for name,values in groups.items():(destination/(name+'.json')).write_text(json.dumps(values,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (destination/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(audit(args.library,args.output),ensure_ascii=False),flush=True)
