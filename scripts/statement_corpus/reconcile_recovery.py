"""Stage and apply source-verified repairs after checking the actual renderer.

Uses an explicit public baseline and isolated GET captures. Existing IDs,
educational content, prior translations and personal facts are never deleted.
"""
import argparse
from collections import Counter,defaultdict
from contextlib import closing
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys

REPO=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(REPO/'backend'),str(REPO/'backend/common')]
from insights import canonical_url
from library import LibraryDatabase
from statement_asset_store import dehydrate,references
from statement_cleanup import clean_statement
from statement_integrity import content_complete,native_submission_supported,statement_type
from statement_seed import checksum,load_statements
from translation import bundled_translation

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def sha(text):return hashlib.sha256(text.encode()).hexdigest()

def equivalents(url):
    result={canonical_url(url)}
    # These identifiers are explicit first-party mirror names, not title guesses.
    match=re.fullmatch(r'https://(?:www\.)?luogu.com.cn/problem/CF(\d+)([A-Z]\d?)',url or '')
    if match and int(match[1])<100000:result.add(f'codeforces.com/contest/{match[1]}/problem/{match[2]}')
    match=re.fullmatch(r'https://(?:www\.)?luogu.com.cn/problem/AT_([a-z0-9]+)_(\w+)',url or '')
    if match:result.add(f'atcoder.jp/contests/{match[1]}/tasks/{match[1]}_{match[2]}')
    return result-{None}

def samples(value):return Counter((' '.join(s['input'].split()),' '.join(s['output'].split())) for s in value.get('samples') or [])

def prepare(work):
    baseline=LibraryDatabase(work/'baseline.sqlite3',readonly=True)
    with baseline.connection() as db:
        problems=[(r['id'],r['url'],json.loads(r['encoded'])) for r in db.execute('SELECT id,url,encoded FROM problems')]
        bodies={r[0]:json.loads(r[1]) for r in db.execute('SELECT problem_id,content FROM statements')}
    healthy=defaultdict(list)
    for identity,url,meta in problems:
        if content_complete(clean_statement(bodies.get(identity) or {})):
            for key in equivalents(url):healthy[key].append(identity)
    inventory=json.loads((work/'initial-audit.json').read_text('utf8'))['missing']
    assets={};candidates=[];render=[];audit=[]
    def save_asset(digest,mime,data):
        assets[digest]={'sha256':digest,'mime':mime,'bytes':len(data),'file':'statement-assets/'+digest+'.bin'}
        target=work/'new-assets'/(digest+'.bin');target.parent.mkdir(exist_ok=True)
        if not target.exists():target.write_bytes(data)
    for row in inventory:
        identity=row['id'];old=baseline.statement(identity) or {};packet=None;binding=None
        path=work/'parsed'/(sha(identity)+'.json')
        if path.exists():
            packet=json.loads(path.read_text('utf8'))
            binding=packet.get('binding')
            if not content_complete(packet['statement']):packet=None;binding=None
        if packet is None:
            aliases=list(dict.fromkeys(other for key in equivalents(row['url']) for other in healthy[key]))
            for other in sorted(aliases,key=lambda other:not bool(bodies[other].get('translation'))):
                value=baseline.statement(other)
                if samples(old)-samples(value):continue
                packet={'statement':value,'sources':(value.get('integrity') or {}).get('sourceDocuments',[])}
                binding={'method':'explicit-original-identity-and-all-existing-samples','originalUrl':row['url'],'mirrorUrl':value.get('url'),'mirrorId':other}
                break
        if packet is None:
            audit.append({'id':identity,'url':row['url'],'status':'unresolved'});continue
        value=clean_statement(dict(packet['statement'],id=identity,url=row['url'],title=row['title']))
        previous=old.get('translation')
        if previous and value.get('markdown')==old.get('markdown') and not value.get('translation'):
            value['translation']=previous
        elif previous and previous!=value.get('translation'):
            value['archivedTranslations']=[*old.get('archivedTranslations',[]),dict(previous,sourceMarkdown=old.get('markdown'))]
        if old.get('markdown') and old['markdown']!=value.get('markdown'):
            value['previousSourceMarkdown']=old['markdown']
        value['images']={**old.get('images',{}),**value.get('images',{})}
        source_documents=[{k:s[k] for k in ('url','sha256','status') if k in s} for s in packet.get('sources',[])]
        evidence=dict(value.get('integrity') or {})
        evidence.update(schema=1,status='complete',sourceVerified=True,sourceDocuments=source_documents,
            checkedAt=dt.datetime.now(dt.timezone.utc).isoformat(),markdownSha256=sha(value.get('markdown') or ''),
            sampleCount=len(value.get('samples') or []),corpusAuditVerifiedSha256=sha(value.get('markdown') or ''))
        if binding:evidence['recoveryBinding']=binding
        value['integrity']=evidence
        value['localJudgeSupported']=statement_type(value)=='standard' and bool(value.get('samples'))
        portable=dehydrate(value,save_asset)
        candidates.append({'id':identity,'content':portable})
        render.append({'id':identity,'markdown':value['markdown'],'samples':value.get('samples',[]),'title':value['title'],'nativePdf':bool(value.get('statementPdf'))})
        translation=value.get('translation') or {}
        if translation.get('markdown'):render.append({'id':identity+'\tzh','markdown':translation['markdown'],'samples':value.get('samples',[]),'title':value['title'],'nativePdf':bool(translation.get('statementPdf'))})
        audit.append({'id':identity,'url':row['url'],'status':'awaiting-render-review','sourceDocuments':source_documents,**({'binding':binding} if binding else {})})
    dump(work/'recovery-candidates.json',candidates);dump(work/'recovery-render.json',render)
    dump(work/'recovery-assets.json',list(assets.values()));dump(work/'recovery-audit.json',audit)
    print(json.dumps({'candidates':len(candidates),'unresolved':len(inventory)-len(candidates),'resources':len(assets)}))

def apply(work):
    if (REPO/'data/library/statement-patches/zzzzz-20261107-recovery.json').exists():
        raise ValueError('Recovery already exported; preserve it and rebase against the preceding source before rerunning')
    source=REPO/'data/library';current={r['problem_id']:r['content'] for r in load_statements(source)}
    problems=json.loads((source/'problems.json').read_text('utf8'));by_id={p['id']:p for p in problems}
    review=json.loads((work/'recovery-render-review.json').read_text('utf8'))['issues']
    bad={row['id'] for row in review if '\t' not in row['id']}
    bad_chinese={row['id'].split('\t',1)[0] for row in review if row['id'].endswith('\tzh')}
    candidates={row['id']:row['content'] for row in json.loads((work/'recovery-candidates.json').read_text('utf8'))}
    inventory=json.loads((work/'initial-audit.json').read_text('utf8'))['missing'];patches=[];counts=Counter();audit=[]
    for row in inventory:
        identity=row['id'];meta=by_id[identity]['encoded'];old=current.get(identity);incoming=candidates.get(identity)
        if incoming and identity in bad_chinese:
            previous=incoming.pop('translation',None)
            if previous:incoming.setdefault('archivedTranslations',[]).append(dict(previous,sourceMarkdown=incoming.get('markdown')))
            counts['incompleteTranslationsArchived']+=1
        if incoming and identity in bad and identity not in bad_chinese and (incoming.get('translation') or {}).get('kind')=='site':
            # A complete, verified native Chinese mirror is a readable source
            # when its English export contains broken TeX. Keep both snapshots.
            translated=incoming.pop('translation');previous=incoming['markdown'];incoming['markdown']=translated['markdown']
            incoming['previousSourceMarkdown']=previous;incoming['statementLanguage']='zh'
            incoming['statementSource']=translated.get('provider','原站中文题面');incoming.pop('currentSourceMarkdown',None)
            incoming['integrity'].update(markdownSha256=sha(incoming['markdown']),corpusAuditVerifiedSha256=sha(incoming['markdown']))
            bad.remove(identity);counts['nativeChineseSourcesRestored']+=1
        ready=bool(incoming and identity not in bad)
        if ready:
            if old and old.get('translation') and old.get('translation')!=incoming.get('translation'):
                previous=old['translation']
                authenticated=bundled_translation(clean_statement(dict(incoming,translation=previous))) if previous.get('kind')=='bundled' else None
                if identity not in bad_chinese and (authenticated or incoming.get('markdown')==old.get('markdown') and previous.get('kind')!='bundled'):incoming['translation']=authenticated or previous
                else:
                    archived=incoming.setdefault('archivedTranslations',[]);item=dict(previous,sourceMarkdown=old.get('markdown'))
                    if item not in archived:archived.append(item)
            patches.append({'problem_id':identity,'beforeSha256':checksum(old),'content':incoming})
            if meta.get('statementRetirementPolicy')=='public-statement-audit-v1':
                prior=meta.get('statementPriorVisibility') or {}
                for key in ('catalogHidden','catalogNotice','catalogVisibilityPolicy'):
                    if key in prior:meta[key]=prior[key]
                    else:meta.pop(key,None)
                for key in ('statementRetired','statementRetirementPolicy','statementRetirementReason','statementPriorVisibility'):meta.pop(key,None)
            kind=statement_type(incoming)
            meta.update(problemType=kind,catalogStatementReady=True,catalogReplayReady=native_submission_supported(row['url']) and kind not in {'communication','output-only','attachment'})
            counts['restored']+=1
        else:
            if not meta.get('statementRetired'):
                meta['statementPriorVisibility']={k:meta[k] for k in ('catalogHidden','catalogNotice','catalogVisibilityPolicy') if k in meta}
                meta.update(statementRetired=True,statementRetirementPolicy='public-statement-audit-v1',statementRetirementReason='公开题面尚未核实完整，暂不可打开；原题身份与历史记录保留',catalogHidden=True)
            meta.update(catalogStatementReady=False,catalogReplayReady=False);counts['unresolved']+=1
        audit.append({'id':identity,'url':row['url'],'title':row['title'],'restored':ready,'rendererIssues':identity in bad})
    manifest=json.loads((source/'statement_assets.json').read_text('utf8'));known={a['sha256'] for a in manifest}
    needed=set().union(*(references(patch['content']) for patch in patches))
    for asset in json.loads((work/'recovery-assets.json').read_text('utf8')):
        if asset['sha256'] in known or asset['sha256'] not in needed:continue
        target=source/asset['file'];target.parent.mkdir(exist_ok=True)
        shutil.copy2(work/'new-assets'/(asset['sha256']+'.bin'),target);manifest.append(asset);known.add(asset['sha256']);counts['newResources']+=1
    dump(source/'statement_assets.json',sorted(manifest,key=lambda a:a['sha256']))
    dump(source/'statement-patches/zzzzz-20261107-recovery.json',{'schema':1,'statements':patches})
    dump(source/'problems.json',problems)
    dump(REPO/'docs/statement-repairs-20261107/recovery.json',{'counts':dict(counts),'problems':audit})
    print(json.dumps(dict(counts)))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare','apply']);parser.add_argument('--work',type=Path,required=True)
    args=parser.parse_args();globals()[args.action](args.work.resolve())
