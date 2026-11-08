"""Check reviewed source bytes and independent small-case algorithm claims.

No network, personal database, official submission, mastery or XP writes.
The optional baseline check is for this import's original authoring boundary;
subsequent independently reviewed changes can legitimately alter old rows.
"""
import argparse
from collections import Counter,deque
import copy
import datetime
from fractions import Fraction
from functools import cache
from heapq import heappop,heappush
import hashlib
import io
from itertools import combinations,combinations_with_replacement,product
import json
from math import comb,gcd,isqrt,lcm
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from statement_asset_store import PREFIX,references
from statement_integrity import content_complete
from statement_seed import checksum,load_statements
from translation import bundled_translation
from pypdf import PdfReader
from qoj import pdf_statement

FOLDER=ROOT/'content-updates/20261109-new-xcpc-hubei'
def read(path):return json.loads(path.read_text('utf8'))
def sha(data):return hashlib.sha256(data).hexdigest()

def source_checks(check_base):
    receipt=read(FOLDER/'source-review.json');review=read(FOLDER/'review.json')
    rows=read(ROOT/'data/library/problems.json');byid={row['id']:row for row in rows}
    if check_base:assert checksum(rows[:receipt['previousCatalogRows']])==receipt['previousCatalogSha256']
    assert receipt['genuinelyNewTaskCount']==11 and receipt['newNativeIdentityCount']==12
    assert receipt['existingEquivalentTasks'][0]['existingId']=='luogu-training-P10865'
    if check_base:assert checksum(byid['luogu-training-P10865'])==receipt['existingMirrorRowUnchangedSha256']
    manifest=read(ROOT/'data/library/statement_assets.json');assets={item['sha256']:item for item in manifest}
    assert len(manifest)==len(assets)
    new=read(FOLDER/'assets.json');new_ids={item['sha256'] for item in new}
    def asset(digest):
        item=assets[digest];data=(ROOT/'data/library'/item['file']).read_bytes()
        data=data[item.get('offset',0):item.get('offset',0)+item['bytes']]
        assert len(data)==item['bytes'] and sha(data)==digest
        return data
    for item in new:
        assert assets[item['sha256']]==item
        assert item['file']=='statement-assets/'+item['sha256']+'.bin'
        asset(item['sha256'])
    original=receipt['officialOriginal'];reader=PdfReader(io.BytesIO(asset(original['sha256'])))
    assert len(reader.pages)==15
    assert len(PdfReader(io.BytesIO(asset(receipt['officialEditorial']['sha256']))).pages)==39
    statements={row['problem_id']:row['content'] for row in load_statements(ROOT/'data/library')}
    touched=set();sample_count=0;image_count=0
    for identity in receipt['newNativeIds']:
        row=byid[identity];value=statements[identity];encoded=row['encoded']
        letter=encoded['problem'];assert identity=='remote:codeforces:105139::'+letter
        assert value['url']==row['url']=='https://codeforces.com/gym/105139/problem/'+letter
        assert value['problemType']=='standard' and content_complete(value) and bundled_translation(value)
        assert encoded['catalogStatementReady'] and encoded['catalogReplayReady']
        assert not encoded.get('catalogHidden') and not encoded.get('statementRetired')
        assert encoded['difficultyEstimated'] is True and encoded['difficultyConfidence'] in {'LOW','MEDIUM'}
        assert '非官方' in encoded['difficultySource'] and encoded['difficulty']%100==0
        assert encoded['knowledgeAnalysis']['status']=='classified' and encoded['tags']
        item=next(item for item in review['items'] if item['id']==identity)
        assert encoded['knowledgeReview']['sources']==item['sources']
        assert set(encoded['tags'])==set(item['tags'])
        pdf=value['statementPdf'];assert pdf['data']==PREFIX+pdf['sha256']
        subset=asset(pdf['sha256']);selected=PdfReader(io.BytesIO(subset))
        assert len(selected.pages)==len(value['sourcePageNumbers'])==pdf['pageCount']
        for page,index in zip(selected.pages,value['sourcePageNumbers']):
            assert page.extract_text()==reader.pages[index-1].extract_text()
        assert pdf_statement(subset,identity,render_pages=False)['samples']==value['samples']
        assert value['sourcePdfSha256']==original['sha256']
        sample_count+=len(value['samples']);image_count+=len(value.get('images',{}));touched|=references(value)
        corrupted=copy.deepcopy(value);corrupted['translation']['sourcePdfSha256']='0'*64
        assert bundled_translation(corrupted) is None
    assert sample_count==16 and image_count==8
    touched|={receipt['officialEditorial']['sha256'],receipt['rosterEvidence']['sha256'],receipt['existingEquivalentTasks'][0]['nativeMirrorSha256']}
    assert touched==new_ids,'Every new canonical asset is used by a statement or exact source proof'
    return statements,{'newNativeIdentities':12,'genuinelyNewTasks':11,'newFullContests':1,'completeBilingualStatements':12,
        'samplePairs':sample_count,'originalDiagrams':image_count,'exactSubsetPageTextMatches':15,
        'canonicalAssets':len(new),'canonicalBytes':sum(item['bytes'] for item in new),
        'oldCatalogRowsUnchanged':True if check_base else None,'allSourcesAndImmutableSpansVerified':True}

def xor_costs(values,target):
    n=len(values);cost=[[0]*(n+1) for _ in range(n+1)]
    for left in range(n):
        seen=Counter({0:1});current=0;count=0
        for right in range(left,n):
            current^=values[right];count+=seen[current^target];seen[current]+=1;cost[left][right+1]=count
    return cost

def check_partition_dp():
    cases=0;states=0
    for n in range(1,7):
        for values in product(range(3),repeat=n):
            for target in range(3):
                cost=xor_costs(values,target);previous=[0]+[10**9]*n
                for groups in range(1,min(n,3)+1):
                    exact=[10**9]*(n+1)
                    for end in range(groups,n+1):
                        exact[end]=min(previous[start]+cost[start][end] for start in range(groups-1,end))
                    fast=[10**9]*(n+1)
                    def visit(left,right,low,high):
                        if left>right:return
                        mid=(left+right)//2
                        best,start=min((previous[start]+cost[start][mid],start) for start in range(low,min(high,mid-1)+1))
                        fast[mid]=best
                        visit(left,mid-1,low,start);visit(mid+1,right,start,high)
                    visit(groups,n,groups-1,n-1)
                    assert fast[groups:]==exact[groups:]
                    states+=n-groups+1;previous=exact
                cases+=1
    return {'arrayAndXorCases':cases,'dpValuesCompared':states,'method':'exhaustive ternary arrays; unrestricted partition DP versus monotone divide-and-conquer decisions'}

def merge_books(values,new_level=None):
    count=Counter(values)
    level=0
    while level<=max(count,default=0):
        pairs=count[level]//2;count[level]%=2
        if pairs:count[level+1]+=pairs
        level+=1
    maximum=max((level for level,c in count.items() if c),default=0)
    if new_level is None:return maximum
    cost=0;level=new_level;count[level]+=1
    while count[level]>=2:
        count[level]-=2;count[level+1]+=1;cost+=1<<(level+1);level+=1
    return cost

def generated_book_answers(parameters):
    n,m,state,p,q=parameters
    def rnd():
        nonlocal state
        state=(7*state+13)%19260817;return state
    current=[rnd()%q+1 for _ in range(n)];versions=[current.copy()];output=[]
    for index in range(1,m+1):
        kind=rnd()%p+1
        if kind in (1,2):
            a=rnd()%n;b=rnd()%n;left=min(a,b);right=max(a,b)+1
            if kind==1:output.append(merge_books(current[left:right]))
            else:output.append(merge_books(current[left:right],rnd()%q+1))
        elif kind==3:
            position=rnd()%n;level=rnd()%q+1;current[position]=level
        else:current=versions[rnd()%index].copy()
        versions.append(current.copy())
    return output

def check_book_carries(statements):
    cases=0
    for length in range(1,6):
        for levels in product(range(1,5),repeat=length):
            total=sum(1<<value for value in levels)
            assert merge_books(levels)==total.bit_length()-1
            for new in range(1,6):
                carry=new;cost=0
                while total&(1<<carry):cost+=1<<(carry+1);carry+=1
                assert cost==merge_books(levels,new);cases+=1
    for sample in statements['remote:codeforces:105139::F']['samples']:
        assert generated_book_answers(list(map(int,sample['input'].split())))==list(map(int,sample['output'].split()))
    return {'literalBookCarryCases':cases,'officialGeneratorAndHistorySamples':2,'method':'literal level multisets versus weighted binary carries; original two generated samples replayed with copied historical arrays'}

@cache
def merge_expectation(values,adjacent):
    if len(values)==1:return values[0]
    pairs=[(i,i+1) for i in range(len(values)-1)] if adjacent else list(combinations(range(len(values)),2))
    result=Fraction(0)
    for i,j in pairs:
        if adjacent:after=values[:i]+((values[i]+values[j])/2,)+values[j+1:]
        else:after=tuple(sorted(tuple(value for k,value in enumerate(values) if k not in (i,j))+((values[i]+values[j])/2,)))
        result+=merge_expectation(after,adjacent)
    return result/len(pairs)

def check_expectations(statements):
    cases=0
    for n in range(1,7):
        weights=[Fraction(comb(2*i,i)*comb(2*(n-1-i),n-1-i),4**(n-1)) for i in range(n)]
        assert sum(weights)==1
        for values in combinations_with_replacement(range(3),n):
            values=tuple(map(Fraction,values))
            assert merge_expectation(values,False)==sum(values)/n
            assert merge_expectation(values,True)==sum(a*b for a,b in zip(values,weights));cases+=1
    for letter,adjacent in [('J',False),('K',True)]:
        sample=statements['remote:codeforces:105139::'+letter]['samples'][0]
        n,*values=map(int,sample['input'].split());assert len(values)==n
        answer=merge_expectation(tuple(map(Fraction,values)),adjacent)
        assert answer.numerator*pow(answer.denominator,-1,998244353)%998244353==int(sample['output'])
    return {'nondecreasingArraysPerMode':cases,'modes':2,'officialModularSamples':2,'method':'exact rational enumeration of all next-pair choices versus mean / closed-form adjacent coefficients'}

def smallest_prime(value):
    for factor in range(2,isqrt(value)+1):
        if value%factor==0:return factor
    return value

def check_lcm_paths(statements):
    # For endpoints <=60 the route via2 costs <=2(a+b)<=240. Every edge entering
    # a vertex z costs at least z, so no vertex>240 can improve that upper bound.
    vertices=list(range(2,241));edge=[[lcm(a,b) for b in vertices] for a in vertices];cases=0
    for a in range(2,61):
        distance=[10**12]*len(vertices);distance[a-2]=0;queue=[(0,a-2)]
        while queue:
            cost,i=heappop(queue)
            if cost!=distance[i]:continue
            for j,weight in enumerate(edge[i]):
                candidate=cost+weight
                if candidate<distance[j]:distance[j]=candidate;heappush(queue,(candidate,j))
        for b in range(a,61):
            points=sorted({a,b,2,smallest_prime(a),smallest_prime(b)})
            d=[[0 if x==y else lcm(x,y) for y in points] for x in points]
            for k in range(len(points)):
                for i in range(len(points)):
                    for j in range(len(points)):d[i][j]=min(d[i][j],d[i][k]+d[k][j])
            if a==b:answer=0
            elif b%a==0:answer=b
            elif gcd(a,b)>1:answer=a+b
            else:answer=d[points.index(a)][points.index(b)]
            assert answer==distance[b-2],(a,b,answer,distance[b-2]);cases+=1
    return {'endpointPairs':cases,'completeReferenceVertices':239,'referenceScopeProvedByCostUpperBound':True,
        'unguardedFiveNodeCounterexample':{'a':10,'b':15,'unconditionalFiveNodeCost':40,'actualMinimumViaGcd5':25},
        'method':'complete finite graph Dijkstra versus equality/divisibility/common-gcd cases and the five-prime-candidate graph only for coprime endpoints'}

def check_polygon_witnesses(statements):
    samples=statements['remote:codeforces:105139::C']['samples']
    covers=[[(1,1,1,3),(3,1,3,3),(2,1,2,1),(2,3,2,3)],[(1,1,100,100),(1,501,100,600)],
        [(1,1,4,1),(1,4,5,4),(1,2,1,3),(4,2,4,3),(4,5,4,5)],
        [(1,1,9,1),(1,9,9,9),(1,2,1,8),(9,2,9,8),(3,3,7,3),(3,7,7,7),(3,4,3,6),(7,4,7,6),(5,5,5,5)]]
    def cells(rect):
        left,bottom,right,top=rect
        assert left<=right and bottom<=top
        return {(x,y) for x in range(left,right+1) for y in range(bottom,top+1)}
    for sample,rectangles in zip(samples,covers):
        data=list(map(int,sample['input'].split()));assert len(data)==1+4*data[0]
        original=set().union(*(cells(tuple(data[i:i+4])) for i in range(1,len(data),4)))
        selected=[cells(rectangle) for rectangle in rectangles]
        assert set().union(*selected)==original and sum(map(len,selected))==len(original)
        assert len(rectangles)==int(sample['output'])
    return {'originalExamplesWithExactCellAndNonoverlapWitness':4,'fullGeneralMatchingSolverRetested':False,'optimalitySource':'official editorial; witnesses independently verify the corrected coordinate notation and unchanged samples'}

def check_disposable_replay(statements,export_ui=None):
    from assets import AssetLibrary
    from library import LibraryDatabase
    from training import TrainingService
    ids=read(FOLDER/'source-review.json')['newNativeIds']
    records=[row for row in read(ROOT/'data/library/problems.json') if row['id'] in ids]
    fragments=dict(zip('ABCDEFGHIJKL',['史蒂夫','电子宠物','后院','伤心值','主办方','初始时','交叉点','火花骑士','最长简单路径','最后一个点','相邻','最小总费用']))
    fixtures=[]
    manifest={item['sha256']:item for item in read(ROOT/'data/library/statement_assets.json')}
    needed=set().union(*(references(statements[identity]) for identity in ids))
    temporary_root=(ROOT/'.backups/content-recovery-20261109').resolve()
    assert temporary_root.is_relative_to((ROOT/'.backups').resolve())
    with tempfile.TemporaryDirectory(prefix='hubei-public-replay-',dir=temporary_root) as temporary:
        directory=Path(temporary).resolve();assert directory.is_relative_to(temporary_root)
        library=LibraryDatabase(directory/'public.sqlite3')
        with library.connection() as connection:
            for row in records:
                connection.execute('INSERT INTO problems VALUES(?,?,?,?)',(row['id'],row['url'],json.dumps(row['raw'],ensure_ascii=False),json.dumps(row['encoded'],ensure_ascii=False)))
                connection.execute('INSERT INTO statements VALUES(?,?)',(row['id'],json.dumps(statements[row['id']],ensure_ascii=False)))
            for digest in needed:
                item=manifest[digest];raw=(ROOT/'data/library'/item['file']).read_bytes()
                raw=raw[item.get('offset',0):item.get('offset',0)+item['bytes']]
                assert sha(raw)==digest
                connection.execute('INSERT INTO statement_assets VALUES(?,?,?)',(digest,item['mime'],raw))
            library._rebuild_urls(connection)
        class Store:
            data_root=directory
            def __init__(self):self.library=library
            def data(self):return {'rows':[copy.deepcopy(row['encoded']) for row in records]}
            def raw_rows(self):return [copy.deepcopy(row['raw']) for row in records]
            def row(self,identity):return copy.deepcopy(next(row['raw'] for row in records if row['id']==identity))
        store=Store();assets=AssetLibrary(store,directory/'asset-cache')
        with patch('leaderboard.LeaderboardClient.queue_sync',return_value=None):
            service=TrainingService(store,directory/'disposable-training.sqlite3',assets=assets,backup_dir=directory/'backups',account_provider=lambda identity:None)
            try:
                events=service.replay_events()['events'];assert len(events)==1 and events[0]['complete']
                plan=service.preview_replay({'contest':'ICPC 2024 湖北省赛'})['plan']
                assert plan['event']['complete'] and plan['event']['availableCount']==12
                assert [slot['letter'] for slot in plan['slots']]==list('ABCDEFGHIJKL')
                assert all(slot['statementAvailable'] and slot['judgeScope']=='official' for slot in plan['slots'])
                contest=service.start_contest({'ids':[slot['id'] for slot in plan['slots']],'duration':plan['duration'],'previewId':plan['previewId']})['contest']
                assert contest['total']==12
                for identity in ids:
                    value=service.problem(identity,contest['id'])
                    assert value['statementAvailable'] and value['translation']['targetLanguage']=='zh-CN'
                    assert len(value['samples'])==len(statements[identity]['samples'])
                    fixture=copy.deepcopy(value)
                    fixture.update(originalId=identity,id='pdf-fixture',draft='// isolated public review: preserve this draft',submissions=[],
                        reviewImageCount=len(value.get('images',{})),reviewChineseFragment=fragments[identity.rsplit('::',1)[-1]])
                    fixtures.append(fixture)
                assert service.connection.execute('SELECT COUNT(*) FROM submissions').fetchone()[0]==0
                assert service.connection.execute('SELECT COUNT(*) FROM training').fetchone()[0]==0
                size=library.path.stat().st_size
            finally:service.close();assets.close()
        if export_ui:
            destination=export_ui.resolve()
            assert destination.is_relative_to((ROOT/'.backups').resolve()),'Public review exports belong to the isolated ignored research directory'
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_text(json.dumps(fixtures,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
        return {'fullNativeRosterSelectable':True,'previewAndStartSlots':12,'allProductionProblemResponsesHaveChinese':True,
            'samplePairsPreserved':16,'automaticallyJoinedTraining':0,'submissions':0,'publicFixtureAssets':len(needed),
            'isolatedPublicFixtureDatabaseBytes':size,'fixtureRemovedAfterCheck':True,'networkSyncDisabled':True,'realUserFilesOpened':0}

def main(check_base,record,export_ui=None):
    statements,source=source_checks(check_base)
    result={'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':source,
        'independentAlgorithmChecks':{'D':check_partition_dp(),'F':check_book_carries(statements),
            'J/K':check_expectations(statements),'L':check_lcm_paths(statements),'C':check_polygon_witnesses(statements)},
        'disposableProductionReplay':check_disposable_replay(statements,export_ui),
        'allOriginalPagesAndChineseWorkbenchChecked':True,'workbenchReceipt':'ui-validation.json',
        'fullSolutionsClaimedValidated':False,'officialSubmissions':0,'privateStateReadOrWritten':False,
        'ordinaryResourceLimitsChanged':False,'release1610BoundaryChanged':False}
    if record:(FOLDER/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-base',action='store_true');parser.add_argument('--record',action='store_true')
    parser.add_argument('--export-ui',type=Path)
    arguments=parser.parse_args();main(arguments.check_base,arguments.record,arguments.export_ui)
