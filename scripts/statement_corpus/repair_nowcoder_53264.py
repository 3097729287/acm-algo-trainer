"""Recover original NC53264 illustrations from the explicitly linked JOI PDF.

Keeps the Chinese CC-BY-SA statement and samples; no editorial is authored.
The full original and the exact five task pages are both preserved.
"""
import argparse,copy,datetime as dt,hashlib,json,re,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'backend'),str(ROOT/'backend/common')]
from scripts.import_nowcoder_training import Client,original_samples
from statement_seed import checksum,load_statements
from statement_integrity import content_complete
URL='https://ac.nowcoder.com/acm/problem/53264'
PDF='https://www2.ioi-jp.org/camp/2014/2014-sp-tasks/2014-sp-d4.pdf'
IDENTITY='nowcoder-global::53264'

def digest(raw):return hashlib.sha256(raw).hexdigest()
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')

def repair(cached,work,source):
    import pymupdf as fitz
    from pypdf import PdfReader,PdfWriter
    work.mkdir(parents=True,exist_ok=True)
    client=Client(work/'http');html=client.text(URL)
    if '两个人的星座' not in html:raise ValueError('Original identity changed')
    page_samples=original_samples(html);value=json.loads(cached.read_text('utf8'))
    if value['id']!=IDENTITY:raise ValueError('Wrong cached original')
    if [(s['input'],s['output']) for s in page_samples]!=[(s['input'],s['output']) for s in value['samples']]:raise ValueError('Original samples changed')
    raw=client.bytes(PDF);pdf_path=work/'official-day4.pdf';pdf_path.write_bytes(raw)
    pdf=fitz.open(pdf_path)
    if len(pdf)!=15 or any(not re.search(r'Constellation\s*2',pdf[i].get_text()) for i in range(5)):raise ValueError('Official task/page mapping changed')
    tables=[]
    for page in (2,4):
        for table in pdf[page].find_tables().tables:
            cells=table.extract()
            if len(cells)==2 and '入力例' in cells[0][0]:tables.append(cells[1])
    if len(tables)!=3 or any(a.split()!=s['input'].split() or b.split()!=s['output'].split() for (a,b),s in zip(tables,page_samples)):raise ValueError('JOI and Nowcoder samples disagree')
    assets=json.loads((source/'statement_assets.json').read_text('utf8'));known={a['sha256']:a for a in assets}
    backup=work/'source-before-repair';backup.mkdir(exist_ok=True)
    for name in ['statement_assets.json','problems.json']:
        if not (backup/name).exists():shutil.copy2(source/name,backup/name)
    def asset(data,mime):
        sha=digest(data);path=source/'statement-assets'/(sha+'.bin')
        if path.exists():
            if path.read_bytes()!=data:raise ValueError('Existing immutable asset differs')
        else:path.write_bytes(data)
        if sha not in known:
            item={'sha256':sha,'mime':mime,'file':'statement-assets/'+path.name,'bytes':len(data)};assets.append(item);known[sha]=item
        return 'tb-asset:'+sha,sha
    full,full_sha=asset(raw,'application/pdf')
    writer=PdfWriter();reader=PdfReader(pdf_path)
    for page in reader.pages[:5]:writer.add_page(page)
    subset=work/'constellation2-only.pdf'
    with subset.open('wb') as file:writer.write(file)
    part,part_sha=asset(subset.read_bytes(),'application/pdf')
    images={};resources={}
    for name,page,rect in [('conditions',0,(140,425,452,545)),('sample-stars',2,(195,553,405,763)),('four-candidates',3,(117,162,480,531))]:
        key='nc53264-'+name+'.png';data=pdf[page].get_pixmap(matrix=fitz.Matrix(2,2),clip=fitz.Rect(rect)).tobytes('png');ref,sha=asset(data,'image/png');images[key]=ref
        resources[key]={'sha256':sha,'bytes':len(data),'mime':'image/png','sourceUrl':PDF,'sourcePdfSha256':full_sha,'sourcePages':[page+1],'clipRect':list(rect),'method':'original-pdf-rendered-region'}
    pdf.close()
    value=copy.deepcopy(value)
    broken='http://z4a.net/images/2018/10/17/Snipaste_2018-10-17_20-59-03..png'
    if value['markdown'].count(broken)!=1:raise ValueError('Cached illustration reference changed')
    value['markdown']=value['markdown'].replace(broken,'nc53264-conditions.png').replace('https://www.ioi-jp.org/camp/2014/2014-sp-tasks/2014-sp-d4.pdf',PDF)
    value['markdown']+='\n\n## 样例 1 图示\n\n星星的位置如下图：红星用圆、蓝星用菱形、黄星用三角形表示。\n\n![样例 1 的星星位置](nc53264-sample-stars.png)\n\n四种候补如下：\n\n![样例 1 的四种候补](nc53264-four-candidates.png)\n\n[官方原题（仅本题 5 页）](nc53264-original.pdf)\n'
    value.update(images=images,attachments={PDF:{'data':full,'mime':'application/pdf','fileName':'JOISC2014-Day4.pdf','bytes':len(raw),'sha256':full_sha},'nc53264-original.pdf':{'data':part,'mime':'application/pdf','fileName':'JOISC2014-Constellation2.pdf','bytes':subset.stat().st_size,'sha256':part_sha,'sourcePdfSha256':full_sha,'sourcePageNumbers':[1,2,3,4,5]}},resourceManifest=resources,resourceIssues=[],statementAvailable=True,sourceHtmlSha256=digest(html.encode()),limits={'timeMs':3000,'memoryMb':256})
    value['integrity']={'schema':1,'sourceVerified':True,'status':'complete','sampleCount':3,'pdfPageCountVerified':True,'method':'original-nowcoder-text-and-joi-pdf-figures','checkedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'corpusAuditVerifiedSha256':digest(value['markdown'].encode())}
    if not content_complete(value):raise ValueError('Recovered statement remains incomplete')
    old=next((r['content'] for r in load_statements(source) if r['problem_id']==IDENTITY),None)
    packet={'schema':1,'statements':[{'problem_id':IDENTITY,'beforeSha256':checksum(old),'content':value}]}
    target=source/'statement-patches/nowcoder-53264-original-resources-20261104.json'
    if target.exists() and json.loads(target.read_text('utf8'))!=packet:raise ValueError('Repair already exists with different content')
    dump(target,packet);dump(source/'statement_assets.json',assets)
    problems=json.loads((source/'problems.json').read_text('utf8'))
    row=next(p for p in problems if p['id']==IDENTITY);row['encoded'].update(statementAvailable=True,catalogStatementReady=True,catalogContentReady=True,catalogReplayReady=True)
    dump(source/'problems.json',problems)
    report={'id':IDENTITY,'originalUrl':URL,'officialPdfUrl':PDF,'officialPdfSha256':full_sha,'taskPdfSha256':part_sha,'sourcePages':[1,2,3,4,5],'illustrations':3,'samplePairsVerified':3,'samplesPreservedExactly':True,'sourceHtmlSha256':value['sourceHtmlSha256'],'beforeSha256':checksum(old),'afterSha256':checksum(value),'license':'Chinese source CC-BY-SA; existing LOJ attribution retained; JOI original credited','ratingInvented':False,'editorialsAdded':0}
    dump(work/'verified.json',report);return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cached',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--source',type=Path,default=ROOT/'data/library');a=p.parse_args()
    print(json.dumps(repair(a.cached,a.work,a.source),ensure_ascii=False))
