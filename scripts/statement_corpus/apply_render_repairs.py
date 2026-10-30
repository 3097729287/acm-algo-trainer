import os
import datetime,hashlib,json,sys
from pathlib import Path
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2];sys.path[:0]=[str(Path(__file__).resolve().parent),str(REPO/'backend'),str(REPO/'backend/common')]
from library import LibraryDatabase
from prepare_corpus import preserve,Resources
from statement_resources import archive_resources
from statement_asset_store import dehydrate
from statement_seed import checksum,load_statements
SOURCE=REPO/'data/library';current={r['problem_id']:r['content'] for r in load_statements(SOURCE)}
db=LibraryDatabase(REPO/'data/library.sqlite3',readonly=True)
index=json.loads((SOURCE/'statement_assets.json').read_text('utf8'));assets={r['sha256']:r for r in index}
pack=SOURCE/'statement-assets/part-0044.bin';assert not pack.exists();stream=pack.open('wb');offset=0;hasher=hashlib.sha256();patches=[]
def save(sha,mime,data):
    global offset
    if sha not in assets:
        assets[sha]={'sha256':sha,'mime':mime,'bytes':len(data),'file':'statement-assets/'+pack.name,'offset':offset}
        stream.write(data);hasher.update(data);offset+=len(data)
for file in sorted((ROOT/'render-recoveries').glob('*.json')):
    packet=json.loads(file.read_text('utf8'));identity=packet['statement']['id'];old=db.statement(identity)
    value=preserve(old,packet['statement']);value['url']=old['url'];value=archive_resources(value,Resources(packet['sources']))
    assert not value['resourceIssues'],identity
    value['integrity']=dict(value['integrity'],status='complete',sourceVerified=True,
        markdownSha256=hashlib.sha256((value.get('currentSourceMarkdown') or value['markdown']).encode()).hexdigest(),
        checkedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),sourceDocuments=[{'url':r['url'],'sha256':r['sha256']} for r in packet['sources']])
    value['sourceBinding']=packet['binding']
    patches.append({'problem_id':identity,'beforeSha256':checksum(current[identity]),'content':dehydrate(value,save)})
stream.close();parts=json.loads((SOURCE/'statement_asset_parts.json').read_text('utf8'))
parts.append({'file':'statement-assets/'+pack.name,'bytes':offset,'sha256':hasher.hexdigest()})
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True),'utf8',newline='\n')
dump(SOURCE/'statement_assets.json',[assets[k] for k in sorted(assets)]);dump(SOURCE/'statement_asset_parts.json',parts)
dump(SOURCE/'statement-patches/part-9998.json',{'schema':1,'statements':patches})
problems=json.loads((SOURCE/'problems.json').read_text('utf8'))
for p in problems:
    if p['id'].startswith('xcpc-qoj::') and p['encoded'].get('contestId')=='2562':
        p['encoded'].update(difficultySource='QOJ 未提供单题评级',difficultyConfidence='UNKNOWN',difficultyEstimated=False,knowledgeReviewRequired=True)
dump(SOURCE/'problems.json',problems)
# The new batch keeps source hashes and native PDF bytes, without authoring
# any missing prose, formula, translation or sample.
file=SOURCE/'statement-patches/part-9999.json';new=json.loads(file.read_text('utf8'))
for patch in new['statements']:
    if patch['problem_id'].startswith('xcpc-qoj::'):
        value=patch['content'];value['integrity'].update(schema=1,
            markdownSha256=hashlib.sha256(value['markdown'].encode()).hexdigest())
dump(file,new)
print({'recoveredNativeRenderSources':len(patches),'additionalOriginalAssetBytes':offset},flush=True)
rows=[];issues={r['id'] for r in json.loads((ROOT/'evidence/corpus-render.json').read_text('utf8'))['issues']}
for item in load_statements(SOURCE):
    s=item['content'];identity=item['problem_id']
    if identity not in issues:continue
    rows.append({'id':identity,'title':s['title'],'markdown':s.get('currentSourceMarkdown') or s['markdown'],'samples':s['samples'],'nativePdf':bool(s.get('statementPdf'))})
dump(ROOT/'render-review.json',rows)
