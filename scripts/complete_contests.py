"""Repair public contest rosters, preserving existing problem identities and content.

Only anonymous GET responses are read. An optional existing HTTP cache supplies
public first-party responses when a site is temporarily unavailable.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime as dt
import hashlib
import html
import json
from pathlib import Path
import re
import sqlite3
import sys
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT/'backend'), str(ROOT/'backend/common')]
from library import LibraryDatabase
from insights import canonical_url
import public_platforms as P


class PublicClient:
    def __init__(self, directory, http_cache=None):
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)
        self.saved = {}
        if http_cache:
            with sqlite3.connect(http_cache.resolve().as_uri()+'?mode=ro', uri=True) as db:
                for value, in db.execute('SELECT value FROM documents'):
                    value = json.loads(value)
                    url = value.get('url', '')
                    # Explicitly exclude account profiles, cookies and settings.
                    if (url in ('https://codeforces.com/api/problemset.problems', 'https://codeforces.com/api/contest.list?gym=false')
                            or re.fullmatch(r'https://(?:codeforces.com/(?:contest|gym)/\d+/problem/[A-Z]\d?|atcoder.jp/contests/[\w-]+/(?:tasks(?:/[\w-]+)?)(?:\?lang=en)?|ac.nowcoder.com/acm/contest/\d+/[A-Z]\d?)', url)):
                        self.saved[url] = value['text']

    def text(self, url, headers=None):
        path = self.directory/(hashlib.sha256(url.encode()).hexdigest()+'.txt')
        if path.exists():
            return path.read_text('utf8')
        if url in self.saved:
            return self.saved[url]
        request = Request(url, headers={'User-Agent':'Mozilla/5.0 TB public contest collection', **(headers or {})})
        with urlopen(request, timeout=14) as response:
            value = response.read().decode('utf8')
        path.write_text(value, 'utf8')
        return value

    def json(self, url, headers=None):
        return json.loads(self.text(url, headers))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--http-cache', type=Path)
    parser.add_argument('--xcpc-pages', type=int, default=8)
    args = parser.parse_args()
    client = PublicClient(args.cache, args.http_cache)
    database = LibraryDatabase(args.database)
    existing = database.rows()
    by_url = {canonical_url(row.get('url')):row for row in existing}
    groups = {}
    for row in existing:
        if row.get('source') in ('xcpc-history', 'lanqiao-history'):
            continue
        match = re.match(r'https://(codeforces.com|atcoder.jp|ac.nowcoder.com)/(?:contest|contests|acm/contest)/([^/]+)/', row.get('url',''))
        if match:
            groups.setdefault(match.groups(), []).append(row)
    cf_contests = {}; cf_problems = {}
    try:
        cf_contests = {str(c['id']):c for c in client.json('https://codeforces.com/api/contest.list?gym=false')['result']}
        for item in client.json('https://codeforces.com/api/problemset.problems')['result']['problems']:
            cf_problems.setdefault(str(item['contestId']), []).append(item)
    except Exception as error:
        print('CF roster unavailable:', type(error).__name__, flush=True)
    # Public Nowcoder archive provides the complete task order for historical XCPC.
    historical = {}
    for page in range(1, args.xcpc_pages+1):
        url = 'https://ac.nowcoder.com/acm/contest/vip-end-index?topCategoryFilter=13&categoryFilter=22&orderType=NO&page='+str(page)
        try:
            source = client.text(url)
            for cid, encoded, body in re.findall(r'<div\b[^>]*data-id="(\d+)"[^>]*data-json="([^"]+)"[^>]*>(.*?)(?=<div\b[^>]*data-id=|$)',source,re.S):
                name = re.search(r'<h4>.*?<a[^>]*>(.*?)</a>', body, re.S)
                title = P.text(name[1]) if name else ''
                if not re.search(r'ICPC|CCPC|省赛|省大学生程序设计|邀请赛', title, re.I):
                    continue
                metadata = json.loads(html.unescape(html.unescape(encoded)))
                if metadata.get('contestEndTime', float('inf'))/1000 > dt.datetime.now().timestamp():
                    continue
                historical[cid] = {'id':cid,'name':title,'start':metadata.get('contestStartTime'),'end':metadata.get('contestEndTime'),'series':'XCPC'}
                groups.setdefault(('ac.nowcoder.com',cid), [])
        except Exception as error:
            print('XCPC archive page', page, type(error).__name__, flush=True)
    print('rosters', len(groups), 'historical', len(historical), flush=True)
    missing=[]; collected=[]; coverage={}
    def roster(entry):
        (host,cid), old = entry
        name = old[0]['contest'] if old else historical[cid]['name']
        c = {'id':cid,'name':name,'series':old[0].get('series') if old else 'XCPC'}
        result=[]
        if host == 'codeforces.com':
            meta=cf_contests.get(cid,{})
            c.update(start=meta.get('startTimeSeconds'),end=(meta.get('startTimeSeconds',0)+meta.get('durationSeconds',0)) or None)
            for p in cf_problems.get(cid,[]):
                result.append(P.row('codeforces',c,p['index'],p['name'],f'https://codeforces.com/contest/{cid}/problem/{p["index"]}',p.get('rating'),'Codeforces 官方 rating',[P.CF_TAGS[t] for t in p.get('tags',[]) if t in P.CF_TAGS]))
        elif host == 'atcoder.jp':
            source=client.text(f'https://atcoder.jp/contests/{cid}/tasks?lang=en')
            for task,index,title in re.findall(r'<td class="text-center no-break"><a href="/contests/[^"/]+/tasks/([^"]+)">([^<]+)</a></td>\s*<td><a href="[^"]+">([^<]+)</a></td>',source):
                result.append(P.row('atcoder',c,index.strip(),html.unescape(title.strip()),f'https://atcoder.jp/contests/{cid}/tasks/{task}',None,'官方未提供难度'))
        else:
            c=historical.get(cid,c)
            payload=client.json('https://ac.nowcoder.com/acm/contest/problem-list?token=&id='+cid)
            if payload.get('code') != 0:
                raise ValueError('Official task list unavailable')
            for p in (payload.get('data') or {}).get('data',[]):
                value=P.row('nowcoder',c,p['index'],p['title'],f'https://ac.nowcoder.com/acm/contest/{cid}/{p["index"]}',None,'原站未提供可靠数值难度')
                if cid in historical:
                    year=re.search(r'20\d{2}',c['name'])
                    value.update(source='xcpc-roster',series='XCPC',contestFamily='XCPC',xcpcYear=int(year[0]) if year else None,
                                 xcpcKind='邀请赛' if '邀请' in c['name'] else '省赛' if re.search('省|北京市|上海市|重庆市|天津市',c['name']) else '区域赛')
                result.append(value)
        if not result:
            raise ValueError('No public roster')
        for row in result:
            row.update(contestProblemCount=len(result),collectionSource=('https://'+host+('/contests/' if host=='atcoder.jp' else '/acm/contest/' if host=='ac.nowcoder.com' else '/contest/')+cid),collectionNotice='按原站公开完整题单核对题号、题数。')
            if host == 'codeforces.com':
                row.update(contestProblemCount=None,contestRoster=True,collectionNotice='保留原有赛题，并补入公开 problemset 赛题；共用题可能未出现在 API，原赛总题数未核验。')
        return name,result
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs={pool.submit(roster,entry):entry[0] for entry in groups.items()}
        for future in as_completed(jobs):
            try:
                name,rows=future.result();collected.extend(rows);coverage[name]={'expected':rows[0].get('contestProblemCount'),'problems':[r['problem'] for r in rows]}
            except Exception as error:
                missing.append({'contest':list(jobs[future]),'error':type(error).__name__})
    print('full rosters',len(coverage),'tasks',len(collected),'unavailable',len(missing),flush=True)
    new=[]; updates=[]
    for row in collected:
        old=by_url.get(canonical_url(row['url']))
        if old:
            updates.append((old['id'],{key:row[key] for key in ('contestProblemCount','collectionSource','collectionNotice','contestRoster') if key in row}))
            continue
        row.update(source=row.get('source') if row.get('source')=='xcpc-roster' else 'contest-completion',status='未做',date='')
        raw={'场次':row['contest'],'题号':row['problem'],'题名':row['title'],'知识点':row['knowledge'],'难度':str(row['difficulty']) if row['difficulty'] is not None else '—','状态':'未做','日期':'','_id':row['id'],'_url':row['url'],'_platform':row['platform'],'_series':row['series']}
        new.append((raw,row,None,None));by_url[canonical_url(row['url'])]=row
    def statement(record):
        raw,row,solution,_=record
        try:
            value=P.statement(client,row['id'],row['title'],row['url'])
        except Exception:
            match=re.fullmatch(r'https://codeforces.com/contest/(\d+)/problem/([A-Z]\d?)',row['url'])
            if not match:
                raise
            mirror='https://www.luogu.com.cn/problem/CF'+match[1]+match[2]
            value=P.statement(client,row['id'],row['title'],mirror)
            value.update(url=row['url'],statementSource=mirror)
            value['markdown']='来源：[原题]('+row['url']+') · [洛谷公开题面]('+mirror+')\n\n'+value['markdown']
        return raw,row,solution,value
    records=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs={pool.submit(statement,r):r for r in new}
        for i,future in enumerate(as_completed(jobs),1):
            try:
                records.append(future.result())
            except Exception as error:
                # Keep the official roster even when a statement cannot be read.
                record=jobs[future];records.append(record)
                missing.append({'url':record[1]['url'],'error':type(error).__name__})
            if i%25==0:
                print('statements',i,'/',len(new),'unavailable',len(missing),flush=True)
    database.import_records(records,{}, {})
    with database.connection() as db:
        for identity,patch in updates:
            saved=db.execute('SELECT encoded FROM problems WHERE id=?',(identity,)).fetchone()
            if saved:
                row=json.loads(saved[0]);row.update(patch)
                db.execute('UPDATE problems SET encoded=? WHERE id=?',(json.dumps(row,ensure_ascii=False),identity))
    report={'contests':len(coverage),'added':len(records),'statements':sum(bool(r[3]) for r in records),'coverage':coverage,'missing':missing}
    (ROOT/'backend/resources/contest-coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('coverage','missing')}),flush=True)


if __name__=='__main__':
    main()
