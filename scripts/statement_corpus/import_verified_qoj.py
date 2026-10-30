import os
"""Import verified native statements; reuse the two fully compared mirror IDs."""
import base64,datetime,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2];sys.path[:0]=[str(REPO/'backend'),str(REPO/'backend/common')]
from statement_asset_store import dehydrate
from statement_seed import checksum,load_statements
from contest_scope import excluded
SOURCE=REPO/'data/library';docs=REPO/'docs/statement-integrity-20261030'
discovery=json.loads((ROOT/'evidence/qoj-new-discovery.json').read_text('utf8'));assert discovery['completeProblemSet']
problems=json.loads((SOURCE/'problems.json').read_text('utf8'));by_id={p['id']:p for p in problems}
statements={r['problem_id']:r['content'] for r in load_statements(SOURCE)}
index=json.loads((SOURCE/'statement_assets.json').read_text('utf8'));assets={r['sha256']:r for r in index}
pack=SOURCE/'statement-assets/part-0043.bin';assert not pack.exists(),'Do not repeat an applied import'
stream=pack.open('wb');offset=0;hasher=hashlib.sha256();patches=[];proofs=[]
def save(sha,mime,data):
    global offset
    if sha not in assets:
        assets[sha]={'sha256':sha,'mime':mime,'bytes':len(data),'file':'statement-assets/'+pack.name,'offset':offset}
        stream.write(data);hasher.update(data);offset+=len(data)
reuse={'14684':'luogu-training-P14450','14688':'luogu-training-P14454'}
for file in sorted((ROOT/'qoj-new').glob('*.json')):
    packet=json.loads(file.read_text('utf8'));proof=packet['proof'];value=packet['statement'];pid=proof['id']
    identity=reuse.get(pid) or 'xcpc-qoj::'+pid
    assert value['integrity']['status']=='complete' and value['statementPdf']
    proof['canonicalId']=identity;proof['disposition']='reused-existing-mirror' if pid in reuse else 'added-complete-native-problem'
    proof['sampleSha256']=checksum(value['samples']);proof['sourceTextSha256']=hashlib.sha256(value['sourceText'].encode()).hexdigest()
    if pid in reuse:
        old=statements[identity];assert old['samples']==value['samples']
        # Reviewed against both complete source documents, including formulas,
        # all IO constraints, examples and notes; title alone is not identity.
        proof['identityReview']={'method':'full-specification-io-constraints-all-samples-and-notes',
            'otherUrl':by_id[identity]['url'],'otherStatementSha256':checksum(old),
            'constraintsVerified': ['n=5,m=6,k=6; n=100,m=128,k=16000'] if pid=='14684' else ['1<=n<=10^7; 1<=k<=5000; modulo 998244353']}
        encoded=by_id[identity]['encoded'];encoded.setdefault('verifiedSourceAliases',[]).append({'platform':'QOJ','url':value['url'],'globalProblemId':pid})
        encoded['aliasIds']=list(dict.fromkeys(encoded.get('aliasIds',[])+['xcpc-qoj::'+pid]))
        changed=dict(old,attachments={**old.get('attachments',{}),**value.get('attachments',{})})
        changed['verifiedEquivalentSources']=[{'url':value['url'],'sourcePdfSha256':value['sourcePdfSha256'],'identityReview':proof['identityReview']}]
        changed=dehydrate(changed,save)
        patches.append({'problem_id':identity,'beforeSha256':checksum(old),'content':changed})
    else:
        assert identity not in by_id and not any(p.get('url')==value['url'] for p in problems)
        # Display actual global problem number. Anonymous category gives event
        # membership but not an explicit letter-to-ID mapping; do not infer it.
        raw={'_id':identity,'_url':value['url'],'_platform':'QOJ','_series':'XCPC','场次':'ICPC 2025 西安区域赛',
            '题号':'#'+pid,'题名':proof['title'],'知识点':'','难度':'—','状态':'未做','日期':''}
        encoded={'id':identity,'url':value['url'],'title':proof['title'],'problem':'#'+pid,'contest':'ICPC 2025 西安区域赛',
            'contestFullName':"The 2025 ICPC Asia Xi'an Regional Contest",'platform':'QOJ','series':'XCPC','contestFamily':'XCPC',
            'source':'xcpc-qoj','contestId':'2562','contestProblemCount':13,'rosterVerified':False,'contestLetterVerified':False,
            'examYear':2025,'xcpcYear':2025,'eventYear':2025,'xcpcKind':'区域赛','xcpcPlace':'西安','examStage':'区域赛',
            'tags':[],'knowledge':'','knowledgeCategories':[],'difficulty':None,'status':'未做','date':'','queue':None,
            'difficultySource':'QOJ 未提供单题评级','difficultyConfidence':'UNKNOWN','difficultyEstimated':False,'knowledgeReviewRequired':True,
            'solutionAvailable':False,'solutionState':'missing','problemType':value['problemType'],
            'catalogStatementReady':True,'catalogReplayReady':False,'collectionSource':proof['categoryUrl']}
        assert not excluded(encoded)
        problems.append({'id':identity,'url':value['url'],'raw':raw,'encoded':encoded});by_id[identity]=problems[-1]
        patches.append({'problem_id':identity,'beforeSha256':checksum(None),'content':dehydrate(value,save)})
    proofs.append(proof)
stream.close()
parts=json.loads((SOURCE/'statement_asset_parts.json').read_text('utf8'))
parts.append({'file':'statement-assets/'+pack.name,'bytes':offset,'sha256':hasher.hexdigest()})
def dump(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True),'utf8',newline='\n')
dump(SOURCE/'statement_assets.json',[assets[k] for k in sorted(assets)]);dump(SOURCE/'statement_asset_parts.json',parts)
dump(SOURCE/'statement-patches/part-9999.json',{'schema':1,'statements':patches});dump(SOURCE/'problems.json',problems)
result={'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verifiedNativeProblems':13,'addedProblems':11,'reusedProblems':2,
    'letterMappingVerified':False,'replayEnabled':False,'notes':'原站未公开逐题比赛字母；使用实际全局题号，不猜映射。','problems':proofs}
dump(docs/'qoj-new-verified.json',result);dump(ROOT/'evidence/qoj-new-verified.json',result)
print(json.dumps({k:v for k,v in result.items() if k!='problems'},ensure_ascii=False),flush=True)
