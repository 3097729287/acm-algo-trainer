"""Validate exact public source receipts and finite independent topic derivations.

No network, account records, original judge submissions or large seed build.
Optional --library opens the supplied public database read-only and checks
that all 152 original sample pairs and bundled statement identities are bound.
"""
import argparse
import hashlib
from itertools import permutations
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from knowledge import canonical_tag,normalize_tags,enrich_row
from library import LibraryDatabase
from statement_seed import checksum

FOLDER=ROOT/'content-updates/20261109-native-metadata-next'
read=lambda path:json.loads(path.read_text('utf8'))
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def source_checks(library=None,check_base=False):
    plan=read(FOLDER/'review.json');captures=read(FOLDER/'captures.json')
    rows=read(ROOT/'data/library/problems.json');byid={r['id']:r for r in rows}
    before=json.loads(subprocess.check_output(['git','show',plan['baseCommit']+':data/library/problems.json'],cwd=ROOT))
    before_byid={r['id']:r for r in before}
    assert set(before_byid)<=set(byid), 'Original public IDs must remain preserved'
    targeted={item['id'] for item in plan['items']}
    assert len(targeted)==len(plan['items'])==91
    if check_base:
        assert [r['id'] for r in before]==[r['id'] for r in rows]
        assert {r['id'] for r,old in zip(rows,before) if r!=old}==targeted
    for identity in set(before_byid) if check_base else targeted:
        row,old=byid[identity],before_byid[identity]
        assert row['url']==old['url']
        assert {k:v for k,v in row['raw'].items() if k!='知识点'}=={k:v for k,v in old['raw'].items() if k!='知识点'}
        allowed={'tags','knowledge','sourceTags','knowledgeCategories','knowledgeAnalysis','knowledgeReviewRequired','knowledgeReview'}
        assert {k:v for k,v in row['encoded'].items() if k not in allowed}=={k:v for k,v in old['encoded'].items() if k not in allowed}
    assets=read(ROOT/'data/library/statement_assets.json');bysha={a['sha256']:a for a in assets}
    assert len(assets)==len(bysha)
    previous_assets=json.loads(subprocess.check_output(['git','show',plan['baseCommit']+':data/library/statement_assets.json'],cwd=ROOT))
    assert all(bysha[a['sha256']]==a for a in previous_assets)
    new=read(FOLDER/'assets.json')
    assert all(bysha[a['sha256']]==a for a in new) and len(new)==156
    if check_base:assert assets[len(previous_assets):]==new
    native={}
    for capture in captures:
        assert capture['status']==200 and capture['finalUrl']==capture['url'] and not capture.get('error')
        entry=bysha[capture['sha256']];assert entry==capture['canonicalAsset']
        assert entry['file']=='statement-assets/'+entry['sha256']+'.bin'
        raw=(ROOT/'data/library'/entry['file']).read_bytes()
        assert len(raw)==entry['bytes']==capture['bytes'] and sha(raw)==entry['sha256']
        value=json.loads(raw)
        if capture['kind']=='tag-dictionary':
            dictionary={t['id']:t for t in value['tags']}
            dictionary_sha=capture['sha256']
        else:
            q=value['data']['problem'];assert q['pid']==capture['pid']
            assert q['name']==capture['nativeTitle'] and q['tags']==capture['nativeTagIds']
            assert q['difficulty']==capture['nativeDifficulty']
            native[capture['id']]=(q,capture)
    lessons={x['id']:x['content'] for x in read(ROOT/'data/library/lectures.json')}
    curation=read(ROOT/'backend/resources/knowledge_topic_review.json')
    assert plan['revision'] in curation['appliedPackets']
    pictures=[];sample_pairs=0
    public=LibraryDatabase(library,readonly=True) if library else None
    source_stat=(public.path.stat().st_size,public.path.stat().st_mtime_ns) if public else None
    for item in plan['items']:
        row=byid[item['id']];old=before_byid[item['id']]
        assert checksum(old)==item['beforeProblemSha256']
        assert all(canonical_tag(tag)==tag for tag in item['tags'])
        assert item['urls']==[row['url']] and not row['encoded'].get('catalogHidden')
        assert row['encoded']['knowledgeAnalysis']['status']=='classified'
        assert set(item['tags'])<=set(enrich_row(row['encoded'])['tags'])
        assert not row['encoded']['knowledgeReviewRequired']
        assert row['encoded']['knowledgeReview']['official'] is False
        assert row['encoded']['knowledgeReview']['sources']==item['sources']
        q,capture=native[item['id']];source,=item['sources']
        assert source['problemId']==item['id']=='luogu-training-'+q['pid']
        assert source['reference']==row['url']=='https://www.luogu.com.cn/problem/'+q['pid']
        assert source['sha256']==capture['sha256']
        assert source['nativeTagDictionarySha256']==dictionary_sha
        assert source['nativeTagDescriptors']==[dictionary[t] for t in q['tags'] if dictionary[t]['type']==2]
        body=q.get('contenu') or q['content']
        assert source['reviewedNativeTextSha256']=={k:sha((body.get(k) or '').encode()) for k in ('background','description','formatI','formatO','hint')}
        assert source['fullStatementAndConstraintsReviewed'] and source['nativeBackgroundRequired']
        assert source['fullImplementationRetested'] is False and source['originalJudgeSubmissions']==0
        assert source['statementReviewedTags']==item['tags']
        assert source['nativeSamplesSha256']==checksum(q['samples'])
        assert source['reviewedNativeSampleCount']==len(q['samples']) and source['bundledSamplesCompared']
        sample_pairs+=len(q['samples'])
        for lesson in source['learningEvidence']:
            value=lessons[lesson['lectureId']]
            assert value['available'] and sha(value['markdown'].encode())==lesson['markdownSha256']
        for picture in source.get('reviewedNativeImages',[]):
            assert picture['visuallyReviewed'] and picture['sourceUrl'] in body[picture['sourceField']]
            entry=bysha[picture['sha256']]
            assert entry['mime']==picture['mime']
            data=(ROOT/'data/library'/entry['file']).read_bytes()[entry.get('offset',0):entry.get('offset',0)+entry['bytes']]
            assert sha(data)==picture['sha256']
            pictures.append(picture['sha256'])
        if public:
            with public.connection() as db:
                original=json.loads(db.execute('SELECT content FROM statements WHERE problem_id=?',(item['id'],)).fetchone()[0])
            assert original['url']==row['url']
            assert sha((original.get('currentSourceMarkdown') or original['markdown']).encode())==source['reviewedBundledStatementMarkdownSha256']
            clean=lambda pairs:[(str(a).strip(),str(b).strip()) for a,b in pairs]
            assert clean(q['samples'])==clean((p['input'],p['output']) for p in original['samples'])
    assert sample_pairs==152 and len(pictures)==7
    assert len(read(FOLDER/'excluded.json'))==64
    assert all(canonical_tag(tag) is None for tag in ['循环结构','分支结构','顺序结构','数组','字符串（入门）'])
    unknown=enrich_row({'id':'unseen','url':'https://www.luogu.com.cn/problem/B999999',
                        'title':'二分 素数 DP 循环','sourceTags':['循环结构']})
    assert not unknown['tags'], 'No global broad-label or title inference was introduced'
    assert not plan['difficultyEstimates'] and not plan['newCanonicalLeaves']
    if public:assert (public.path.stat().st_size,public.path.stat().st_mtime_ns)==source_stat
    return native,{'reviewedPreviouslyMissingKnowledge':91,'verifiedAnonymousReceipts':156,
        'originalSamplePairsBound':sample_pairs,'requiredPicturesVisuallyBound':len(pictures),
        'newCanonicalAssets':len(new),'newCanonicalAssetBytes':sum(a['bytes'] for a in new),
        'authoringBoundaryChecked':check_base,
        'unrelatedRowsUnchanged':len(rows)-91 if check_base else None,
        'targetDifficultiesAndNativeValuesUnchanged':True,
        'allDifficultiesAndNativeValuesUnchanged':True if check_base else None,
        'publicDatabaseOpenedReadOnly':bool(public),'personalStateReadOrWritten':False}


def derivation_checks(native):
    def swap_brute(a,m):
        a=list(a);n=len(a)
        if n==1:return a
        for i in range(m):
            v=n-i%(n-1);x=a.index(v);y=a.index(v-1);a[x],a[y]=a[y],a[x]
        return a
    def cycles(a,m):
        n=len(a)
        if n==1:return list(a)
        m%=n*(n-1);whole,tail=divmod(m,n-1)
        a=[(x-1+whole)%n+1 for x in a];where={x:i for i,x in enumerate(a)}
        for i in range(tail):
            v=n-i;x,y=where[v],where[v-1];a[x],a[y]=a[y],a[x];where[v],where[v-1]=y,x
        return a
    cycle_count=0
    for n in range(1,6):
        for a in permutations(range(1,n+1)):
            for m in range(2*n*max(n-1,1)+1):
                assert cycles(a,m)==swap_brute(a,m);cycle_count+=1
    for input_text,expected in native['luogu-training-B3802'][0]['samples']:
        tokens=input_text.split();n,m=map(int,tokens[:2]);a=list(map(int,tokens[2:]));assert len(a)==n
        assert cycles(a,m)==list(map(int,expected.split()))

    rng=random.Random(20261109)
    def rating_dp(x,k,events):
        states={x:0}
        for division,a in events:
            new=dict(states)
            for rating,count in states.items():
                if count>=k or division==2 and rating>=1900:continue
                value=(3*rating+a)//4
                new[value]=min(new.get(value,k+1),count+1)
            states=new
        return max(states)
    def rating_brute(x,k,events):
        best=x
        for mask in range(1<<len(events)):
            if mask.bit_count()>k:continue
            rating=x
            for i,(division,a) in enumerate(events):
                if not mask>>i&1:continue
                if division==2 and rating>=1900:break
                rating=(3*rating+a)//4
            else:best=max(best,rating)
        return best
    rating_count=0
    for _ in range(180):
        events=[(rng.randint(1,2),rng.choice([0,1800,1899,1900,1904,4000])) for _ in range(rng.randint(1,8))]
        x=rng.choice([0,1899,1900,1901,4000]);k=rng.randint(0,len(events))
        assert rating_dp(x,k,events)==rating_brute(x,k,events);rating_count+=1
    assert rating_dp(1900,2,[(1,1904),(1,1899),(2,4000)])==2424

    def magic_formula(matrix,k):
        n,m=len(matrix),len(matrix[0]);d=n+m-1
        r=list(map(sum,matrix));c=[sum(row[j] for row in matrix) for j in range(m)]
        return sorted((r[i]+c[j]-matrix[i][j]+d-1)//d for i in range(n) for j in range(m))[k-1]
    def magic_brute(matrix,k):
        n,m=len(matrix),len(matrix[0])
        for t in range(100):
            a=[[value-t for value in row] for row in matrix]
            if sum(a[i][j]>=sum(a[i])+sum(row[j] for row in a) for i in range(n) for j in range(m))>=k:return t
        raise AssertionError('Finite review bound insufficient')
    for _ in range(200):
        n,m=rng.randint(1,4),rng.randint(1,4);a=[[rng.randint(1,9) for _ in range(m)] for _ in range(n)];k=rng.randint(1,n*m)
        assert magic_formula(a,k)==magic_brute(a,k)

    def nk_period(n,k):
        count=(n**n-n)//10+1;period=min(count,k)
        valid=[((n+10*t)%k)%n==0 for t in range(period)]
        return sum(valid)*(count//k)+sum(valid[:count%k]) if count>=k else sum(valid)
    nk_count=0
    for n in range(1,7):
        for k in range(1,30):
            assert nk_period(n,k)==sum((x%k)%n==0 for x in range(n,n**n+1,10));nk_count+=1

    patterns=[['***','*.*','*.*','*.*','***'],['..*']*5,
              ['***','..*','***','*..','***'],['***','..*','***','..*','***'],
              ['*.*','*.*','***','..*','..*'],['***','*..','***','..*','***'],
              ['***','*..','***','*.*','***'],['***','..*','..*','..*','..*'],
              ['***','*.*','***','*.*','***'],['***','*.*','***','..*','***']]
    screen_count=0
    for input_text,expected in native['luogu-training-B3900'][0]['samples']:
        lines=input_text.splitlines();n=int(lines[0]);grid=lines[1:6]
        digits=''.join(str(patterns.index([row[4*i:4*i+3] for row in grid])) for i in range(n))
        assert digits==expected.strip();screen_count+=n
    projection_count=0
    for input_text,expected in native['luogu-training-B3809'][0]['samples']:
        tokens=list(map(int,input_text.split()));n,m=tokens[:2];a=[tokens[2+i*m:2+(i+1)*m] for i in range(n)]
        output=[int(any(row)) for row in a]+[int(any(a[x][y] for x in range(n))) for y in range(m-1,-1,-1)]
        output.extend(a[x][y] for y in range(m-1,-1,-1) for x in range(n))
        assert output==list(map(int,expected.split()));projection_count+=1
    return {'finitePermutationComparisons':cycle_count,'finiteRatingScheduleComparisons':rating_count,
            'finiteMagicThresholdComparisons':200,'finiteNKPeriodComparisons':nk_count,
            'originalScreenSampleDigitsMatched':screen_count,'originalProjectionSamplesMatched':projection_count,
            'fullNativeLimitJudgeSuitesRetested':False,'originalJudgeSubmissions':0}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library',type=Path)
    parser.add_argument('--check-base',action='store_true',help='Require this batch to be the only change since its exact authoring base')
    parser.add_argument('--record',type=Path)
    args=parser.parse_args()
    native,result=source_checks(args.library,args.check_base)
    result['independentFiniteDerivationChecks']=derivation_checks(native)
    if args.record:args.record.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8',newline='\n')
    print(json.dumps(result,ensure_ascii=True))
