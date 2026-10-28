"""Import the three verified 2025 CCPC rosters from cached public QOJ PDFs.

The PDFs contain embedded math fonts that extract to wrong Unicode operators.
Render their original pages losslessly rather than inventing formula text.
Independent table extraction supplies copyable official samples. This tool
requires PyMuPDF only during authoring; the desktop reader needs no PDF engine.
"""
import argparse
import base64
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from statement_format import Tree,plain

EVENTS={'jinan':('济南',2693,15032),'zhengzhou':('郑州',2661,15301),'chongqing':('重庆',3387,15419)}


def samples_from_pdf(document):
    samples=[]
    for page in document:
        for table in page.find_tables().tables:
            rows=table.extract()
            if not rows or [str(x).lower().strip() for x in rows[0]]!=['standard input','standard output']:continue
            for row in rows[1:]:
                if len(row)!=2 or not all(isinstance(x,str) for x in row):raise ValueError('Incomplete sample table')
                samples.append({'name':'样例 '+str(len(samples)+1),'input':row[0],'output':row[1]})
    if not samples:
        # This one published task uses vertically stacked input/output boxes.
        text='\n'.join(page.get_text() for page in document)
        match=re.search(r'\bExample\s*\nstandard input\n([\s\S]+?)\nstandard output\n([\s\S]+?)\nPage \d+ of \d+',text)
        if not match:raise ValueError('No verified sample layout')
        samples=[{'name':'样例 1','input':match[1].strip(),'output':match[2].strip()}]
    return samples


def convert(item,cache):
    import pymupdf as fitz
    slug=item['event'];place,cid,start=EVENTS[slug];pid=item['id'];index=ord(item['index'])-65
    if not 0<=index<13 or pid!=start+index or item['contestId']!=cid:raise ValueError('Roster identity mismatch')
    pdf=(cache/f'{pid}.pdf').read_bytes();html=(cache/f'{pid}.html').read_text('utf8')
    if hashlib.sha256(pdf).hexdigest()!=item['statementSha256'] or hashlib.sha256(html.encode()).hexdigest()!=item['htmlSha256']:raise ValueError('Cached source hash mismatch')
    root=Tree(html).root
    if f'/contest/{cid}' not in html:raise ValueError('Missing first-party contest association')
    title=next((re.sub(r'^#?\s*'+str(pid)+r'\.\s*','',plain(n).strip()) for n in root.find(lambda n:n.tag=='h1') if str(pid) in plain(n)),None)
    if title!=item['title']:raise ValueError('Source title mismatch')
    limit=re.search(r'Time Limit:\s*([0-9.]+)\s*s\s*Memory Limit:\s*(\d+)\s*MB',plain(root))
    if not limit:raise ValueError('Missing actual resource limits')
    event=json.loads((cache.parent/'xcpc-sources'/f'2025-{slug}-board-config.json').read_text('utf8'))
    moment=lambda key:dt.datetime.fromtimestamp(event[key]/1000,dt.timezone.utc).isoformat()
    identity=f'xcpc-qoj::{pid}';url=f'https://qoj.ac/problem/{pid}';contest=f'CCPC 2025 {place}区域赛'
    images={};body=[]
    with fitz.open(stream=pdf,filetype='pdf') as document:
        first=document[0].get_text()
        marker=re.search(r'Problem\s+([A-M])\.',first)
        if marker and marker[1]!=item['index']:raise ValueError('PDF task letter differs from roster')
        for page in document:
            top=40
            if page.number==0:
                titles=page.search_for(title)
                if titles:top=max(top,min(rect.y0 for rect in titles)-8)
            clip=fitz.Rect(39,top,page.rect.width-39,page.rect.height-35)
            raw=page.get_pixmap(matrix=fitz.Matrix(2,2),clip=clip,alpha=False).tobytes('png')
            name=f'qoj-{pid}-page-{page.number+1}.png'
            images[name]='data:image/png;base64,'+base64.b64encode(raw).decode('ascii')
            body.append(f'![原题题面第 {page.number+1} 页]({name})')
        samples=samples_from_pdf(document);pages=len(document)
    raw={'场次':contest,'题号':item['index'],'题名':title,'知识点':'','难度':'—','状态':'未做','日期':'',
         '_id':identity,'_url':url,'_platform':'QOJ','_series':'XCPC'}
    encoded={'id':identity,'contest':contest,'problem':item['index'],'title':title,'url':url,'tags':[],'knowledge':'','difficulty':None,
             'difficultySource':'QOJ 未提供单题评级','difficultyEstimated':False,'difficultyConfidence':'UNKNOWN',
             'knowledgeCategories':[],'knowledgeReviewRequired':True,
             'platform':'QOJ','series':'XCPC','contestFamily':'XCPC','source':'xcpc-qoj','status':'未做','date':'','queue':None,
             'solutionAvailable':False,'solutionState':'missing','contestId':str(cid),'contestProblemCount':13,'rosterVerified':True,
             'contestFullName':event['contest_name'],'examYear':2025,'examStage':'区域赛','xcpcYear':2025,'xcpcKind':'区域赛','xcpcPlace':place,
             'startedAt':moment('start_time'),'endedAt':moment('end_time'),'contestDate':moment('start_time'),'eventYear':2025,
             'durationMinutes':(event['end_time']-event['start_time'])//60000,'contestDateSource':'XCPC.io 公开正式赛榜单配置',
             'collectionSource':item['contestUrl'],'collectionNotice':'按原站公开完整题单核对题号、题数。'}
    statement={'id':identity,'title':title,'url':url,'markdown':'# '+title+'\n\n'+'\n\n'.join(body),'images':images,'samples':samples,
               'limits':{'timeMs':round(float(limit[1])*1000),'memoryMb':int(limit[2])},'statementAvailable':True,
               'statementFormat':'pdf-pages-v1','translationAvailable':False,'pageCount':pages,
               'sourcePdfSha256':item['statementSha256'],'sourcePdfUrl':item['statementUrl']}
    proof={key:item[key] for key in ('id','index','title','event','url','contestUrl','statementUrl','retrievedFrom','htmlSha256','statementSha256')}
    proof.update(problemId=identity,pages=pages,samples=len(samples),sampleSha256=hashlib.sha256(json.dumps(samples,ensure_ascii=False,sort_keys=True).encode()).hexdigest())
    return {'id':identity,'url':url,'raw':raw,'encoded':encoded},{'problem_id':identity,'content':statement},proof


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',required=True,type=Path);parser.add_argument('--backup',required=True,type=Path)
    parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    manifest=json.loads((args.cache/'manifest.json').read_text('utf8'))
    if manifest.get('errors') or Counter(p['event'] for p in manifest['problems'])!={key:13 for key in EVENTS}:raise ValueError('Incomplete public rosters')
    converted=[convert(item,args.cache) for item in manifest['problems']]
    if len({p['id'] for p,_,_ in converted})!=39:raise ValueError('Duplicate problem identity')
    coverage={'source':'https://qoj.ac','events':{key:{'place':value[0],'contestId':value[1],'problems':13} for key,value in EVENTS.items()},
              'problems':[proof for _,_,proof in converted],'notes':'PDF 原始分页保留公式与配图；样例按原表格独立提取。未编造评级、知识点或本地完整判题数据。'}
    if args.apply:
        folder=ROOT/'data/library';args.backup.mkdir(parents=True,exist_ok=True)
        for name,new,key in [('problems.json',[p for p,_,_ in converted],'id'),('statements.json',[s for _,s,_ in converted],'problem_id')]:
            file=folder/name;copy=args.backup/name
            if not copy.exists():shutil.copy2(file,copy)
            current=json.loads(file.read_text('utf8'));mapped={value[key]:value for value in current}
            mapped.update({value[key]:value for value in new})
            file.write_text(json.dumps([mapped[k] for k in sorted(mapped)],ensure_ascii=False,indent=2,sort_keys=True),'utf8',newline='\n')
        (ROOT/'backend/resources/qoj-2025-coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2,sort_keys=True),'utf8',newline='\n')
    print(json.dumps({'problems':39,'pages':sum(p['pages'] for p in coverage['problems']),'samples':sum(p['samples'] for p in coverage['problems']),'applied':args.apply},ensure_ascii=False))


if __name__=='__main__':main()
