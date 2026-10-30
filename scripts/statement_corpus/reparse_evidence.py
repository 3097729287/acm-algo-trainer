import os
"""Reparse immutable original response bytes using the final production adapter."""
import collections,concurrent.futures,hashlib,html,json,re,sys,threading
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(REPO/'backend'),str(REPO/'backend/common')]
import public_platforms
from statement_format import Tree,plain
import statement_resources as R
LOCK=threading.RLock();RAW=ROOT/'raw';BY_SHA=RAW/'by-sha';BY_SHA.mkdir(exist_ok=True)
RES={};RESP={};VALID={};RESPONSE_TIMES={}
for name in ['resource-results.jsonl','resource-alternatives.jsonl']:
    path=ROOT/'evidence'/name
    if path.exists():
        for line in path.read_text('utf8').splitlines():
            row=json.loads(line)
            if row.get('result')=='verified':
                RES[row.get('originalUrl') or row['url']]=row
                VALID[(row['sha256'],row['kind'])]={k:row[k] for k in ('sha256','bytes','mime','pageCount','frameCount','width','height') if k in row}
for line in (ROOT/'evidence/attempts.jsonl').read_text('utf8').splitlines():
    row=json.loads(line)
    if row.get('status')==200 and row.get('file'):
        RESP[row['url']]=row
        RESPONSE_TIMES[(row['url'],row.get('sha256'))]=row.get('time')
original_inspect=R.inspect_resource
def inspect(data,url,kind):
    key=(hashlib.sha256(data).hexdigest(),kind)
    with LOCK:known=VALID.get(key)
    if known:
        if urlsplit(url).path.lower().endswith('.gif') and known['mime']!='image/gif':raise ValueError('GIF format mismatch')
        if kind=='image' and known['mime']=='application/pdf':raise ValueError('PDF at image destination')
        return dict(known,sourceUrl=url)
    value=original_inspect(data,url,kind)
    with LOCK:VALID[key]=value
    return value
R.inspect_resource=inspect

class Replay:
    def __init__(self,packet,row):
        self.packet=packet;self.row=row;self.used={};self.local={s['url']:s for s in packet.get('sources',[])}
    def bytes(self,url,headers=None):
        if url in RES:
            item=RES[url];data=(ROOT/'resources'/item['file']).read_bytes()
            assert hashlib.sha256(data).hexdigest()==item['sha256']
            return data
        item=self.local.get(url) or RESP.get(url)
        if item is None:
            # A print packet binds the individual task to the real native roster.
            binding=self.packet.get('binding') or {};source=binding.get('sourceUrl')
            if source and self.row['url'].startswith('https://codeforces.com/'):
                page=self.bytes(source).decode('utf8','replace')
                holders=list(re.finditer(r'<div\b[^>]*class="problemindexholder"[^>]*problemindex="([A-Z]\d?)"[^>]*>',page))
                for i,m in enumerate(holders):
                    if m[1]==binding.get('problemIndex'):
                        return page[m.start():holders[i+1].start() if i+1<len(holders) else len(page)].encode()
            if source and self.row['url'].startswith('https://atcoder.jp/'):
                page=self.bytes(source).decode('utf8','replace');roster=self.text(binding['sourceRosterUrl'])
                names=[]
                for tr in Tree(roster).root.find(lambda n:n.tag=='tr'):
                    links=list(tr.find(lambda n:n.tag=='a' and n.attrs.get('href')==urlsplit(self.row['url']).path))
                    if len(links)>=2:names.append(plain(links[0]).strip()+' - '+plain(links[1]).strip())
                holders=list(re.finditer(r'<span class="h2">(.*?)</span>',page,re.S))
                for i,m in enumerate(holders):
                    if html.unescape(m[1]).strip() in names:return page[m.start():holders[i+1].start() if i+1<len(holders) else len(page)].encode()
            # A locale retry still refers to the exact same native problem URL.
            variants=[s for s in self.local if s.split('?')[0]==url.split('?')[0]]
            if len(variants)==1:return self.bytes(variants[0],headers)
            raise ValueError('No verified collected response for '+url)
        data=(RAW/item['file']).read_bytes();sha=hashlib.sha256(data).hexdigest()
        path=BY_SHA/(sha+'.bin')
        with LOCK:
            if not path.exists():path.write_bytes(data)
        self.used[url]={'url':url,'sha256':sha,'file':'by-sha/'+path.name,'time':RESPONSE_TIMES.get((url,sha)),'cached':True}
        return data
    def text(self,url,headers=None):return self.bytes(url,headers).decode('utf8','replace')
    def json(self,url,headers=None):return json.loads(self.text(url,headers))

def reparse(row):
    path=ROOT/'parsed'/(hashlib.sha256(row['id'].encode()).hexdigest()+'.json')
    if not path.exists():return 'no-source'
    packet=json.loads(path.read_text('utf8'));client=Replay(packet,row)
    try:
        value=public_platforms.statement(client,row['id'],row['title'],row['url'])
        result={'statement':value,'sources':list(client.used.values())}
        if packet.get('binding'):result['binding']=packet['binding']
        tmp=path.with_suffix('.reparsed.tmp');tmp.write_text(json.dumps(result,ensure_ascii=False),'utf8');tmp.replace(path)
        return 'verified'
    except Exception as e:
        with LOCK,(ROOT/'evidence/reparse-failures.jsonl').open('a',encoding='utf8') as output:
            output.write(json.dumps({'id':row['id'],'url':row['url'],'error':type(e).__name__,'message':str(e)[:200]},ensure_ascii=False)+'\n')
        return 'failed'

def main():
    rows=json.loads((ROOT/'evidence/inventory.json').read_text('utf8'));counts=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(6) as pool:
        for i,result in enumerate(pool.map(reparse,rows),1):
            counts[result]+=1
            if i%250==0:print({'done':i,'total':len(rows),'counts':dict(counts)},flush=True)
    (ROOT/'evidence/reparse-summary.json').write_text(json.dumps(counts,indent=2),'utf8')
    print(dict(counts),flush=True)
if __name__=='__main__':main()
