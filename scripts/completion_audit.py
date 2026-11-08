"""Inventory the exact public library and text catalogue before filling gaps."""
import argparse
import collections
import datetime
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from translation import bundled_translation,needs_translation

def display_audit(library, destination):
    """Use the real public projection, including aliases and stored evidence."""
    from store import Store
    from library import LibraryDatabase
    from contestmeta import ContestDates
    store=Store.__new__(Store)
    store.library=LibraryDatabase(library,readonly=True)
    store.lock=threading.RLock();store._identity_lock=threading.RLock()
    store._identity_snapshot=None;store.extensions=None
    store.data_root=str(destination/'public-projection-cache')
    store.contest_dates=ContestDates(store)
    store._refresh_training_membership()
    rows=store._catalog_rows()
    visible=[row for row in rows if not row.get('catalogHidden')]
    groups={'display-knowledge':[],'display-difficulty':[]}
    statuses=collections.Counter()
    for row in visible:
        base={key:row.get(key) for key in ('id','url','title','platform','contest')}
        statuses[(row.get('knowledgeAnalysis') or {}).get('status') or 'unspecified']+=1
        if not row.get('tags') or not row.get('knowledge') or row.get('knowledge') in {'待补充','未分类','未知'}:
            groups['display-knowledge'].append(dict(base,tags=row.get('tags'),knowledge=row.get('knowledge'),analysis=row.get('knowledgeAnalysis')))
        if row.get('difficulty') is None:
            groups['display-difficulty'].append(dict(base,reason=row.get('difficultySource'),native=row.get('nativeDifficulty')))
    for name,values in groups.items():
        (destination/(name+'.json')).write_text(json.dumps(values,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return {'projectedRows':len(rows),'visibleRows':len(visible),'hiddenRows':len(rows)-len(visible),
            'knowledgeStatuses':dict(statuses),'gaps':{name:len(values) for name,values in groups.items()},
            'personalStateRead':False,'publicLibraryReadOnly':True}


def audit(library,destination,display=False):
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
    if display:summary['display']=display_audit(library,destination)
    for name,values in groups.items():(destination/(name+'.json')).write_text(json.dumps(values,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (destination/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--display',action='store_true',help='Audit the real public UI projection without personal state')
    args=parser.parse_args();print(json.dumps(audit(args.library,args.output,args.display),ensure_ascii=False),flush=True)
