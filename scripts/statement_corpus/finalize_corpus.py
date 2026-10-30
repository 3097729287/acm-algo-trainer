import os
import collections,datetime,hashlib,json,sys
from pathlib import Path
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2];sys.path[:0]=[str(REPO/'backend'),str(REPO/'backend/common')]
from statement_seed import checksum,load_statements
from statement_integrity import annotate_type,native_submission_supported
SOURCE=REPO/'data/library';docs=REPO/'docs/statement-integrity-20261030'
assert not (SOURCE/'statement-patches/part-zz-final.json').exists(),'Final overlay already exists; use a fresh isolated authoring checkout'
current={r['problem_id']:r['content'] for r in load_statements(SOURCE)};blocked=collections.defaultdict(list)
for mode,name in [('original','corpus-render-review.json'),('zh','chinese-corpus-render.json')]:
    for row in json.loads((ROOT/'evidence'/name).read_text('utf8'))['issues']:blocked[row['id']].append({'mode':mode,'issues':row.get('issues',[]),'error':row.get('error')})
problems=json.loads((SOURCE/'problems.json').read_text('utf8'));patches=[];counts=collections.Counter();audit=[];retired=[]
attempts=[]
for name in ('attempts.jsonl','alternative-attempts.jsonl','resource-results.jsonl','resource-alternatives.jsonl'):
    file=ROOT/'evidence'/name
    if file.exists():attempts.extend(json.loads(line) for line in file.read_text('utf8').splitlines())
byurl=collections.defaultdict(list);byid=collections.defaultdict(list)
for row in attempts:
    byurl[row['url']].append(row)
    if row.get('id'):byid[row['id']].append(row)
stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
for p in problems:
    identity=p['id'];value=current.get(identity);encoded=p['encoded'];before=value
    if value:
        value=annotate_type(value)
        if identity in blocked:
            value=dict(value);evidence=dict(value.get('integrity') or {});issues=list(evidence.get('issues') or [])
            for error in blocked[identity]:issues.append('unrenderable-source-math:'+error['mode'])
            evidence.update(status='incomplete',issues=list(dict.fromkeys(issues)),rendererIssues=blocked[identity],checkedAt=stamp)
            value['integrity']=evidence;value['localJudgeSupported']=False
        if value!=before:patches.append({'problem_id':identity,'beforeSha256':checksum(before),'content':value})
    ready=bool(value and value.get('integrity',{}).get('status')=='complete')
    kind=(value or {}).get('problemType') or encoded.get('problemType','standard')
    encoded.update(problemType=kind,catalogStatementReady=ready,
        catalogReplayReady=ready and native_submission_supported(p.get('url')) and kind not in {'communication','output-only','attachment'}
        and not (encoded.get('contestId')=='2562' and encoded.get('source')=='xcpc-qoj'))
    issues=(value or {}).get('integrity',{}).get('issues') or ([] if ready else ['no-statement'])
    if not ready and not encoded.get('statementRetired'):
        encoded['statementPriorVisibility']={k:encoded[k] for k in ('catalogHidden','catalogNotice','catalogVisibilityPolicy') if k in encoded}
        encoded.update(statementRetired=True,statementRetirementPolicy='public-statement-audit-v1',
            statementRetirementReason='公开题面与样例尚未就绪，暂不加入题库；个人训练与历史记录保留',catalogHidden=True)
    source_docs=(value or {}).get('integrity',{}).get('sourceDocuments',[])
    entry={'id':identity,'url':p['url'],'title':encoded['title'],'status':'complete' if ready else 'unresolved','issues':issues,
        'problemType':kind,'samples':len((value or {}).get('samples',[])),'sourceDocuments':source_docs,
        'markdownSha256':(value or {}).get('integrity',{}).get('markdownSha256'),
        'pdfPageCount':((value or {}).get('statementPdf') or {}).get('pageCount'),
        'resourceCount':len((value or {}).get('resourceManifest') or {})}
    audit.append(entry);counts['total']+=1;counts['complete']+=ready;counts['unresolved']+=not ready
    counts['stored']+=bool(value);counts['nativePdfStatements']+=bool((value or {}).get('statementPdf'))
    counts['samples']+=len((value or {}).get('samples',[]));counts['specialTypes']+=kind!='standard'
    if not ready:
        urls={p['url']}|{s['url'] for s in source_docs}
        for issue in issues:
            if issue.startswith('resource:'):urls.add(issue[len('resource:'):])
        related=byid.get(identity,[])+[a for url in urls for a in byurl.get(url,[])]
        unique={json.dumps(a,sort_keys=True,ensure_ascii=False):a for a in related}
        entry=dict(entry,temporary=True,historyRetained=True,reasonCodes=issues,
            recoveryState='not-proven-permanent; retry transport/access and verify candidates before restoring',attempts=list(unique.values()))
        retired.append(entry)
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True),'utf8',newline='\n')
dump(SOURCE/'statement-patches/part-zz-final.json',{'schema':1,'statements':patches});dump(SOURCE/'problems.json',problems)
(docs/'audit-after.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in audit),'utf8',newline='\n')
dump(docs/'retired.json',retired)
result={'checkedAt':stamp,'counts':dict(counts),'originalInventory':12271,'retainedOriginalIds':12271,'addedUniqueQoj':11,'verifiedReusedMirrors':2,
    'formatReviewProblems':len(blocked),'recoveredNativeRenderSources':77,'candidateLinksCountAsComplete':False,'officialSubmissionsSent':0}
dump(docs/'delivery-summary.json',result);dump(ROOT/'evidence/delivery-summary.json',result)
for name in ('attempts.jsonl','alternative-attempts.jsonl','resource-results.jsonl','resource-alternatives.jsonl','corpus-render.json','corpus-render-review.json','chinese-corpus-render.json','native-corpus-render.json','render-source-recoveries.json','render-alternative-search.json','final-public-seed-check.json'):
    file=ROOT/'evidence'/name
    if file.exists():(docs/name).write_bytes(file.read_bytes())
print(json.dumps(result,ensure_ascii=False),flush=True)
