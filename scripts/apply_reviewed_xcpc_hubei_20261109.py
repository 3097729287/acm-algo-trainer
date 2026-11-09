"""Register one complete, page-reviewed contest; never import roster placeholders.

The authoring stage contains only anonymous public source material and real
Workbench receipts. Public output keeps every original identity and history,
stores each resource once by SHA, and distinguishes a new native identity from
an already collected mirror of the same task.
"""
import argparse
import copy
import datetime
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from codeforces_pdf import normalized
from contest_scope import excluded
from statement_asset_store import dehydrate
from statement_integrity import content_complete,native_submission_supported
from statement_resources import inspect_resource
from statement_seed import checksum,load_statements
from translation import bundled_translation

FOLDER=ROOT/'content-updates/20261109-new-xcpc-hubei'
PDF_URL='https://codeforces.com/gym/105139/attachments/download/25286/contest-40758-en.pdf'
PDF_SHA='925611a43f223d1489a315b8e7ebecf0f202abd51f5f50aec5033549f9012282'
EDITORIAL_URL='https://codeforces.com/gym/105139/attachments/download/25287/Sol_ICPC_hubei_24.pdf'
EDITORIAL_SHA='11de7ea32d7a426a25e11c325f38444233f057a9b6e0c9184a2bb93ef14b5f23'
TITLES=['Long Live','Nana Likes Polygons','Lili Likes Polygons','MACARON Likes Happy Endings','Spicy or Grilled?','Enchanted','Genshin Impact Startup Forbidden II','Genshin Impact Startup Forbidden III','Colorful Tree','Points on the Number Axis A','Points on the Number Axis B','LCMs']
PAGES=[[1],[2],[3,4],[5],[6],[7,8],[9,10],[11],[12],[13],[14],[15]]
TIME=[1000,1000,1000,2000,1000,1500,8000,1000,2000,1000,1000,1000]
MEMORY=[256,512,512,512,256,1024,512,512,512,256,256,256]

def read(path):return json.loads(path.read_text('utf8'))
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def sha(data):return hashlib.sha256(data).hexdigest()

def main(stage):
    source=ROOT/'data/library'
    target=source/('statement-patches/'+'z'*34+'-20261109-new-xcpc-hubei.json')
    ids=['remote:codeforces:105139::'+letter for letter in 'ABCDEFGHIJKL']
    rows=read(source/'problems.json');old=copy.deepcopy(rows);byid={row['id']:row for row in rows}
    statements={row['problem_id']:row['content'] for row in load_statements(source)}
    if target.exists():
        packet=read(target)
        assert [item['problem_id'] for item in packet['statements']]==ids
        for item in packet['statements']:
            assert item['beforeSha256']==checksum(None)
            assert checksum(statements[item['problem_id']])==checksum(item['content'])
            assert byid[item['problem_id']]['encoded']['catalogStatementReady'] is True
            assert item['content']['integrity']['status']=='complete'
        print('Existing complete-contest packet verified; no source or metadata was changed.')
        return
    assert not (set(ids)&set(byid)) and not (set(ids)&set(statements))
    assert not any(re.search(r'codeforces\.com/gym/105139(?:/|$)',row.get('url') or '') for row in rows)
    cleanup=read(stage/'pre-add-cleanup.json')
    assert cleanup['checkedBeforeNewContent'] and not cleanup['duplicateManifestHashes']
    ui=read(stage/'ui/receipt.json');checked={item['id']:item for item in ui['checked']}
    assert set(checked)==set(ids) and ui['browserErrors']==ui['formulaErrors']==ui['externalRequests']==0
    assert all(ui[key] for key in ['allOriginalPagesRendered','consoleAndChineseSamplesPreserved','originalBookletByteIdentity','originalSubsetByteIdentity','allOriginalImagesLoaded','editorDraftsPreserved'])
    assert ui['realJudgeSubmissions']==0
    raw=(stage/'original.pdf').read_bytes();tutorial=(stage/'editorial.pdf').read_bytes()
    assert sha(raw)==PDF_SHA and sha(tutorial)==EDITORIAL_SHA
    assert inspect_resource(raw,PDF_URL,'attachment')['pageCount']==15
    assert inspect_resource(tutorial,EDITORIAL_URL,'attachment')['pageCount']==39
    provider=(stage/'roster-web-provider.txt').read_bytes();roster=provider.decode('utf8')
    assert 'Finished' in roster and 'register for practice' in roster
    for title in TITLES:assert title in roster
    # This is a provider's read-only public-document extract, not origin HTML.
    # The normal anonymous HTML GET was 403 and is preserved as a limitation.
    captures=read(stage/'capture.json')
    assert any(item.get('status')==200 and item.get('sha256')==PDF_SHA for item in captures)
    assert any(item.get('status')==200 and item.get('sha256')==EDITORIAL_SHA for item in captures)
    mirror_raw=(stage/'existing-H-luogu-P10865-content.json').read_bytes()
    mirror=read(stage/'existing-H-luogu-P10865-content.json')['data']['problem']
    assert mirror['pid']=='P10865'
    content=mirror.get('contenu') or mirror['content']
    assert content['name']=='[HBCPC2024] Genshin Impact Startup Forbidden III'
    mirror_id='luogu-training-P10865';assert mirror_id in byid
    original_mirror_sha=checksum(byid[mirror_id])
    assert mirror['samples']==[['5 5 3\n1 1 2\n2 2 1\n5 5 2','4']]
    assets=read(source/'statement_assets.json');known={item['sha256']:item for item in assets}
    assert len(known)==len(assets)
    pending={};proofs=[];patches=[]
    def save(digest,mime,data):
        assert sha(data)==digest
        if digest in known:
            assert known[digest]['bytes']==len(data)
        elif digest in pending:assert pending[digest][1]==data
        else:pending[digest]=(mime,data)
    save(PDF_SHA,'application/pdf',raw);save(EDITORIAL_SHA,'application/pdf',tutorial)
    save(sha(provider),'application/octet-stream',provider)
    save(sha(mirror_raw),'application/json',mirror_raw)
    for i,letter in enumerate('ABCDEFGHIJKL'):
        identity=ids[i];url='https://codeforces.com/gym/105139/problem/'+letter
        value=read(stage/'statements'/(letter+'-reviewed.json'));actual=checked[identity]
        assert value['id']==identity and value['url']==url and value['title']==TITLES[i]
        assert normalized(TITLES[i]) in normalized(value['sourceTextArchive'][0]['text'][:1400])
        assert value['sourcePdfUrl']==PDF_URL and value['sourcePdfSha256']==PDF_SHA
        assert value['sourcePageNumbers']==PAGES[i] and value['statementPdf']['sourcePageNumbers']==PAGES[i]
        assert value['sourceRosterSha256']==sha(provider)
        assert value['sourceRosterEvidenceKind']=='read-only-web-provider-text-not-origin-html'
        assert value['limits']=={'timeMs':TIME[i],'memoryMb':MEMORY[i]}
        assert value['problemType']=='standard' and content_complete(value)
        assert native_submission_supported(url)
        assert bundled_translation(value) is not None
        assert value['translation']['markdown'].startswith((FOLDER/f'105139-{letter}.zh.md').read_text('utf8').rstrip())
        assert value['sourceText'].startswith((FOLDER/f'105139-{letter}.en.md').read_text('utf8').rstrip())
        assert actual['pages']==len(PAGES[i]) and actual['samples']==len(value['samples'])
        assert actual['images']==len(value.get('images',{}))
        assert actual['subsetSha256']==value['statementPdf']['sha256']
        assert actual['originalBookletSha256']==PDF_SHA and actual['bilingualVerified'] and actual['downloadVerified']
        notes=[]
        if letter=='A':notes.append('The non-algorithmic closing song passage is paraphrased in the reviewed English/Chinese text; the literal official PDF is unchanged.')
        if letter=='C':notes.append('Malformed coordinate intervals in the printed example notes are explicitly identified; reviewed notation is checked against every original input cell, with the literal PDF retained.')
        if letter=='G':notes.append('The first-line move count omitted in the prose formatting is made explicit from the original example/protocol; capture priority and the liberty definition are unchanged.')
        value['sourceTextReview'].update(method='all-pages-reviewed-semantic-and-math-transcription',sourceCaveats=notes)
        native_limits={'timeMs':TIME[i],'memoryMb':MEMORY[i]}
        printed_limits={'timeMs':1000 if letter=='D' else 4000 if letter=='G' else TIME[i],'memoryMb':MEMORY[i]}
        value['nativeSourceReview']={'method':'whole-official-roster-and-all-pdf-pages-with-real-workbench-review',
            'id':identity,'nativeProblemUrl':url,'sourcePdfUrl':PDF_URL,'sourcePdfSha256':PDF_SHA,
            'sourcePageNumbers':PAGES[i],'sourceRosterUrl':'https://codeforces.com/gym/105139',
            'sourceRosterEvidenceSha256':sha(provider),'sourceRosterEvidenceKind':'read-only-web-provider-text-not-origin-html',
            'nativeLimits':native_limits,'printedPdfLimits':printed_limits,'currentNativeLimitsPreferred':True,
            'samplesSha256':checksum(value['samples']),'samplePairs':len(value['samples']),
            'allPagesRenderedInWorkbench':True,'originalDownloadByteIdentity':True,'realJudgeSubmissions':0,
            'submissionEvidence':'The native finished dashboard offers practice registration/submission and every A–L task has accepted submissions; no account or real submission was used.'}
        if letter=='H':value['nativeSourceReview']['existingEquivalentIdentity']=mirror_id
        value['integrity']={'schema':1,'sourceVerified':True,'status':'complete',
            'sampleCount':len(value['samples']),'pdfPageCountVerified':True,
            'markdownSha256':sha(value['markdown'].encode()),
            'sourceDocuments':[{'url':PDF_URL,'sha256':PDF_SHA}],
            'reviewedSourceBindingSha256':checksum(value['nativeSourceReview']),
            'issues':[]}
        encoded={'id':identity,'url':url,'platform':'Codeforces','series':'XCPC','source':'xcpc-codeforces',
            'contest':'ICPC 2024 湖北省赛','contestFullName':'The 2024 International Collegiate Programming Contest in Hubei Province, China',
            'contestId':'105139','contestFamily':'XCPC','contestRoster':True,'contestProblemCount':12,'contestPhase':'FINISHED',
            'collectionSource':'https://codeforces.com/gym/105139','eventYear':2024,'examYear':2024,'xcpcYear':2024,'xcpcKind':'省赛',
            'contestDate':None,'contestDatePrecision':'year','contestDateSource':'赛事原名年份；原稿/题解文档印有2024-04-27，尚未以独立赛程确认实际开赛时刻',
            'contestDocumentDate':'2024-04-27','startedAt':None,'endedAt':None,
            'problem':letter,'title':TITLES[i],'originalTitle':TITLES[i],'problemType':'standard',
            'catalogStatementReady':True,'catalogReplayReady':True,'statementAvailable':True,'translationAvailable':True,
            'solutionAvailable':False,'solutionState':'missing','status':'未做','date':'','queue':None,
            'difficulty':None,'difficultyEstimated':False,'difficultyConfidence':'UNKNOWN','tags':[],'sourceTags':[],
            'knowledge':'','knowledgeReviewRequired':True,
            'nativeSourceReceipt':'content-updates/20261109-new-xcpc-hubei/source-review.json#'+identity}
        assert not excluded(encoded)
        row={'id':identity,'url':url,'raw':{'_id':identity,'_url':url,'_platform':'Codeforces','_series':'XCPC',
            '场次':encoded['contest'],'题号':letter,'题名':TITLES[i],'知识点':'','难度':'—','状态':'未做','日期':''},'encoded':encoded}
        rows.append(row)
        patches.append({'problem_id':identity,'beforeSha256':checksum(None),'content':dehydrate(value,save)})
        proofs.append(value['nativeSourceReview'])
    assert rows[:len(old)]==old and checksum(byid[mirror_id])==original_mirror_sha
    assert sum(len(read(stage/'statements'/(letter+'-reviewed.json'))['samples']) for letter in 'ABCDEFGHIJKL')==16
    new=[]
    for digest,(mime,data) in sorted(pending.items()):
        entry={'sha256':digest,'mime':mime,'bytes':len(data),'file':'statement-assets/'+digest+'.bin'}
        destination=source/entry['file']
        if destination.exists():assert destination.read_bytes()==data
        else:destination.write_bytes(data)
        assets.append(entry);new.append(entry)
    dump(source/'statement_assets.json',assets)
    dump(source/'problems.json',rows)
    dump(target,{'schema':1,'statements':patches})
    dump(FOLDER/'assets.json',new)
    dump(FOLDER/'ui-validation.json',ui)
    result={'schema':1,'revision':'20261109-hubei-105139-complete-official-originals',
        'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'newContestCount':1,'newNativeIds':ids,
        'newNativeIdentityCount':12,'genuinelyNewTaskCount':11,'existingEquivalentTasks':[{'newId':ids[7],'existingId':mirror_id,
            'nativeMirrorUrl':'https://www.luogu.com.cn/problem/P10865','nativeMirrorSha256':sha(mirror_raw),'sameFullStatementAndConstraints':True,'sameSampleSha256':checksum(mirror['samples'])}],
        'previousCatalogRows':len(old),'catalogRows':len(rows),'previousCatalogSha256':checksum(old),
        'officialOriginal':{'url':PDF_URL,'sha256':PDF_SHA,'pageCount':15},
        'officialEditorial':{'url':EDITORIAL_URL,'sha256':EDITORIAL_SHA,'physicalPageCount':39,'logicalSlides':26},
        'rosterEvidence':{'url':'https://codeforces.com/gym/105139','sha256':sha(provider),'kind':'read-only-web-provider-text-not-origin-html',
            'anonymousRawHtmlGet':'403, not bypassed or retried with alternate authorization','ordinaryOfficialPdfGet':'200 for both explicitly linked original and tutorial'},
        'samples':16,'originalImages':8,'newCanonicalAssets':len(new),'newCanonicalAssetBytes':sum(item['bytes'] for item in new),
        'oldIdsAndRowsUnchanged':True,'existingMirrorRowUnchangedSha256':original_mirror_sha,'personalStateReadOrWritten':False,
        'installed':False,'release1610BoundaryChanged':False,'originalSubmissions':0,'cleanupInspection':cleanup,'problems':proofs}
    dump(FOLDER/'source-review.json',result)
    print(json.dumps({key:value for key,value in result.items() if key not in {'problems','cleanupInspection','newNativeIds','existingEquivalentTasks'}},ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stage',type=Path,required=True)
    main(parser.parse_args().stage.resolve(strict=True))
