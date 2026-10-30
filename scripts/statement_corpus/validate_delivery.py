import os
"""Every statement, source sample and stored asset; only disposable data."""
import base64,collections,datetime,hashlib,json,sqlite3,sys
from pathlib import Path
from contextlib import closing
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2];sys.path[:0]=[str(REPO/'backend'),str(REPO/'backend/common')]
from statement_asset_store import hydrate,references
from statement_integrity import content_complete,ordinary_samples,statement_type
from statement_resources import inspect_resource,resource_references
from statement_cleanup import clean_statement
from contest_policy import apply_visibility
stats=collections.Counter();errors=[]
with closing(sqlite3.connect(ROOT/'baseline.sqlite3')) as before,closing(sqlite3.connect(REPO/'data/library.sqlite3')) as db:
    db.row_factory=sqlite3.Row
    for table in ('solutions','detailed_solutions','lectures','problem_lectures','solution_methods','training_lists'):
        assert sorted(tuple(x) for x in before.execute('select * from '+table))==sorted(tuple(x) for x in db.execute('select * from '+table)),table
        stats['protected_'+table]=db.execute('select count(*) from '+table).fetchone()[0]
    assets={}
    for row in db.execute('select sha256,mime,data from statement_assets'):
        raw=bytes(row['data']);assert hashlib.sha256(raw).hexdigest()==row['sha256']
        info=inspect_resource(raw,'https://archive.invalid/original','attachment')
        assets[row['sha256']]=info;stats['assets']+=1;stats['asset_bytes']+=len(raw)
        if info['mime']=='application/pdf':stats['pdf_assets']+=1;stats['pdf_pages']+=info['pageCount']
        if info['mime']=='image/gif':stats['gif_assets']+=1;stats['gif_frames']+=info['frameCount']
    original={i:json.loads(s) for i,s in before.execute('select problem_id,content from statements')}
    oldids={r[0] for r in before.execute('select id from problems')};newids={r[0] for r in db.execute('select id from problems')};assert oldids<=newids
    for row in db.execute('select p.id,p.url,p.encoded,s.content from problems p left join statements s on s.problem_id=p.id order by p.id'):
        identity=row['id'];meta=json.loads(row['encoded']);value=json.loads(row['content']) if row['content'] else {}
        hidden=apply_visibility(meta).get('catalogHidden');stats['total']+=1
        if value:
            assert references(value)<=set(assets),identity
            value=hydrate(value,db);stats['readable_stored']+=1
            cleanold=clean_statement(original.get(identity) or {})
            if cleanold.get('translation'):
                assert value.get('translation')==cleanold['translation'],identity+' Chinese translation changed'
                stats['translations_exact_after_existing_cleanup']+=1
            audit=value.get('integrity') or {};body=value.get('currentSourceMarkdown') or value.get('markdown') or ''
            assert audit.get('markdownSha256')==hashlib.sha256(body.encode()).hexdigest(),identity
            if audit.get('status')=='complete':
                assert content_complete(value),identity
                assert not value.get('resourceIssues'),identity
                for ref in resource_references(value):
                    payload=value.get('images',{}).get(ref['key']) if ref['kind']=='image' else value.get('attachments',{}).get(ref['key'],{}).get('data')
                    assert payload or ref['key'].startswith('data:'),(identity,ref)
                key=hashlib.sha256(identity.encode()).hexdigest()+'.json'
                path=ROOT/'render-recoveries'/key
                if not path.exists():path=ROOT/'parsed'/key
                if not path.exists() and identity.startswith('xcpc-qoj::'):
                    path=ROOT/'qoj-new'/(identity.split('::')[-1]+'.json')
                if path.exists():
                    parsed=json.loads(path.read_text('utf8'))['statement']
                    pairs=lambda samples:[(s['input'],s['output']) for s in samples]
                    assert pairs(value['samples'])==pairs(parsed['samples']),identity+' source samples differ'
                    stats['all_source_sample_pairs_verified']+=len(value['samples'])
                if value.get('statementPdf'):
                    pdf=value['statementPdf'];raw=base64.b64decode(pdf['data'].split(',',1)[1]);info=inspect_resource(raw,row['url'],'attachment')
                    assert info['pageCount']==pdf['pageCount']
                    stats['native_pdf_statements']+=1
                stats['complete']+=1
            else:assert hidden,identity+' unresolved selectable'
            if statement_type(value)!='standard':assert not ordinary_samples(value),identity
        else:assert hidden,identity+' missing statement selectable'
        if meta.get('statementRetired'):
            assert hidden and meta.get('statementRetirementPolicy')=='public-statement-audit-v1';stats['temporarily_hidden']+=1
        if stats['total']%500==0:print(dict(stats),flush=True)
    stats['retained_original_ids']=len(oldids)
result={'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'counts':dict(stats),'errors':errors,'officialSubmissionsSent':0}
(ROOT/'evidence/delivery-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
print(json.dumps(result,ensure_ascii=False),flush=True)
