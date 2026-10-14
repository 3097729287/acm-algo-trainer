"""Complete previously collected Luogu official contests using public task lists."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import datetime as dt
import json
from pathlib import Path
import re
from complete_contests import PublicClient, LibraryDatabase, P, ROOT, canonical_url
import cf_eq


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('--cache',type=Path,required=True)
    args=parser.parse_args()
    client=PublicClient(args.cache);library=LibraryDatabase(args.database)
    existing=library.rows();known={canonical_url(r.get('url')):r for r in existing}
    names={r['contest'] for r in existing if r.get('platform')=='洛谷' and r.get('source')=='archive'}
    headers={'x-lentille-request':'content-only'};found={};errors=[]
    def index(page):
        return client.json('https://www.luogu.com.cn/contest/list?page='+str(page),headers=headers)['data']['contests']['result']
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(index,page) for page in range(1,71)]):
            try:
                for c in future.result():
                    if (c.get('host') or {}).get('id')!=1000 or c.get('endTime',float('inf'))>dt.datetime.now().timestamp():continue
                    title=c['name'];match=re.search(r'(入门赛|基础赛)\s*#?\s*(\d+)',title)
                    monthly=re.search(r'LGR-(\d+)',title) if '月赛' in title else None
                    name=(match[1]+' '+match[2]) if match else ('月赛 '+monthly[1]) if monthly else ''
                    if name in names or 'Yinchuan' in title:
                        # For split divisions the existing problem URLs choose the matching roster.
                        found[str(c['id'])]=(name or title,c)
            except Exception as e:errors.append({'phase':'index','error':type(e).__name__})
    print('matched contests',len(found),'of',len(names),'existing names',flush=True)
    updates={};records=[];coverage={};selected={}
    def detail(entry):
        cid,(name,c)=entry
        data=client.json('https://www.luogu.com.cn/contest/'+cid,headers=headers)['data']
        items=data.get('contestProblems') or []
        if not items:raise ValueError('No public problem list')
        expected={canonical_url(r.get('url')):str(r['problem']) for r in existing if r['contest']==name}
        matched={canonical_url('https://www.luogu.com.cn/problem/'+p['problem']['pid']):str(p.get('no') or chr(65+i)) for i,p in enumerate(items)}
        # Shared tasks between divisions are not evidence that both rosters are
        # this archived contest. Select by exact original URL and task index.
        score=(sum(matched.get(url)==letter for url,letter in expected.items()),len(set(expected)&set(matched)))
        if expected and score[1]==0:return None
        return name,score,cid,data
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs={pool.submit(detail,item):item[0] for item in found.items()}
        for future in as_completed(jobs):
            try:
                answer=future.result()
                if answer:
                    name,score,cid,data=answer
                    if name not in selected or score>selected[name][0]:selected[name]=(score,cid,data)
            except Exception as e:errors.append({'contest':jobs[future],'error':type(e).__name__})
    def collect(entry):
        name,(_,cid,data)=entry
        items=data['contestProblems'];meta=data['contest'];result=[]
        for i,item in enumerate(items):
            problem=item['problem'];pid=problem['pid'];url='https://www.luogu.com.cn/problem/'+pid
            row=P.row('luogu',{'id':cid,'name':name,'start':meta['startTime'],'end':meta['endTime'],'series':'洛谷官方赛'},item.get('no') or chr(65+i),problem['name'],url,cf_eq.cf_eq_luogu(problem.get('difficulty'))['cf_eq_rating'],'CF-EQ / 洛谷官方难度档')
            row.update(contestProblemCount=len(items),collectionSource='https://www.luogu.com.cn/contest/'+cid,collectionNotice='按原站公开完整题单核对题号、题数。')
            old=known.get(canonical_url(url))
            if old:
                updates[old['id']]={k:row[k] for k in ('contestProblemCount','collectionSource','collectionNotice')}
                if old.get('source')=='xcpc-history':updates[old['id']]['problem']=row['problem']
                continue
            row.update(source='contest-completion')
            raw={'场次':row['contest'],'题号':row['problem'],'题名':row['title'],'知识点':'','难度':str(row['difficulty'] or '—'),'状态':'未做','日期':'','_id':row['id'],'_url':url,'_platform':'洛谷','_series':row['series']}
            value=P.statement(client,row['id'],row['title'],url)
            result.append((raw,row,None,value))
        return name,len(items),result
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs={pool.submit(collect,item):item[0] for item in selected.items()}
        for future in as_completed(jobs):
            try:
                answer=future.result()
                if answer:
                    name,count,values=answer;coverage[name]=count;records.extend(values)
                    print(name,count,'added',len(values),flush=True)
            except Exception as e:errors.append({'contest':jobs[future],'error':type(e).__name__})
    library.import_records(records,{}, {})
    with library.connection() as db:
        for identity,patch in updates.items():
            row=json.loads(db.execute('SELECT encoded FROM problems WHERE id=?',(identity,)).fetchone()[0]);row.update(patch)
            db.execute('UPDATE problems SET encoded=? WHERE id=?',(json.dumps(row,ensure_ascii=False),identity))
            if 'problem' in patch:
                raw=json.loads(db.execute('SELECT raw FROM problems WHERE id=?',(identity,)).fetchone()[0]);raw['题号']=patch['problem']
                db.execute('UPDATE problems SET raw=? WHERE id=?',(json.dumps(raw,ensure_ascii=False),identity))
    report={'contests':len(coverage),'added':len(records),'coverage':coverage,'missing':errors,'unmatched':sorted(names-set(coverage))}
    (ROOT/'backend/resources/luogu-contest-coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='coverage'},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
