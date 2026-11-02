"""Index exact problem links in the bundled OI Wiki, preserving existing IDs.

Only catalogue metadata is added. This does not invent statements, solutions,
ratings, personal records or original-judge receipts. Rebuild/merge the normal
public seed after applying the text-source update.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
import re
import sqlite3
import sys
from urllib.parse import parse_qs, urlsplit

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from insights import canonical_url
from problem_titles import problem_title

# The Wiki link points at a whole Gym; its label explicitly names J. The
# original contest booklet independently confirms J on page 16.
GYM_URL='http://codeforces.com/gym/100963'
GYM_PROOF='https://codeforces.com/gym/100963/attachments/download/4256/20072008-summer-petrozavodsk-camp-japanese-contest-20070829-en.pdf'

def problem_link(url,label=''):
    p=urlsplit(url);host=(p.hostname or '').lower().removeprefix('www.');path=p.path.rstrip('/');q=parse_qs(p.query)
    if host in {'codeforces.com','m1.codeforces.com','m2.codeforces.com'}:
        found=re.fullmatch(r'/(?:contest/(\d+)/problem|problemset/problem/(\d+)|gym/(\d+)/problem)/([A-Za-z0-9]+)',path)
        if found:
            contest=found[1] or found[2] or found[3];index=found[4].upper();kind='gym' if found[3] else 'contest'
            return 'Codeforces',contest+index,f'https://codeforces.com/{kind}/{contest}/problem/{index}'
        if url==GYM_URL and '(J)' in label:
            return 'Codeforces','100963J','https://codeforces.com/gym/100963/problem/J'
    if host=='luogu.com.cn' and re.fullmatch(r'/problem/[A-Za-z]+\d+',path):return '洛谷',path.split('/')[-1].upper(),'https://www.luogu.com.cn'+path
    if host=='atcoder.jp' and re.fullmatch(r'/contests/[\w-]+/tasks/[\w-]+',path):return 'AtCoder',path.split('/')[-1],'https://atcoder.jp'+path
    if host=='uoj.ac' and re.fullmatch(r'/problem/\d+',path):return 'UOJ',path.split('/')[-1],'https://uoj.ac'+path
    if host=='loj.ac' and re.fullmatch(r'/p/\d+',path):return 'LibreOJ',path.split('/')[-1],'https://loj.ac'+path
    if host=='spoj.com' and re.fullmatch(r'/problems/[A-Za-z0-9_]+',path):return 'SPOJ',path.split('/')[-1].upper(),'https://www.spoj.com'+path.upper().replace('/PROBLEMS/','/problems/')+'/'
    if host=='acm.hdu.edu.cn' and path=='/showproblem.php' and q.get('pid',[''])[0].isdigit():return 'HDU',q['pid'][0],f'https://acm.hdu.edu.cn/showproblem.php?pid={q["pid"][0]}'
    if host=='poj.org' and path=='/problem' and q.get('id',[''])[0].isdigit():return 'POJ',q['id'][0],f'http://poj.org/problem?id={q["id"][0]}'
    if host in {'onlinejudge.org','uva.onlinejudge.org'} and path=='/index.php' and q.get('problem',[''])[0].isdigit():
        number=re.search(r'(?:UVa\s*[-:]?\s*)?(\d{3,})',label,re.I)
        return 'UVa',number[1] if number else 'pid-'+q['problem'][0],f'https://onlinejudge.org/index.php?option=com_onlinejudge&page=show_problem&problem={q["problem"][0]}'
    return None

class Links(HTMLParser):
    def __init__(self):super().__init__();self.url=None;self.parts=[];self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':self.url=dict(attrs).get('href');self.parts=[]
    def handle_data(self,text):
        if self.url:self.parts.append(text)
    def handle_endtag(self,tag):
        if tag=='a' and self.url:
            self.links.append((self.url,' '.join(''.join(self.parts).split())));self.url=None;self.parts=[]

def collect():
    entries={}
    path=(ROOT/'backend/resources/oi-wiki.sqlite3').resolve()
    with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as db:
        for identity,title,url,html in db.execute('SELECT id,title,url,html FROM articles ORDER BY id'):
            parser=Links();parser.feed(html)
            for href,label in parser.links:
                target=problem_link(href,label)
                if not target:continue
                platform,code,original=target;key=canonical_url(original)
                item=entries.setdefault(key,{'identity':key,'url':original,'platform':platform,'code':code,'links':[],'references':[]})
                if href not in item['links']:item['links'].append(href)
                reference={'articleId':identity,'articleTitle':title,'articleUrl':url,'label':label}
                if reference not in item['references']:item['references'].append(reference)
                if href==GYM_URL:item['identityProof']={'url':GYM_PROOF,'page':16,'title':'Once Upon A Time'}
    return path,entries

def prepare():
    source=ROOT/'data/library/problems.json';problems=json.loads(source.read_text(encoding='utf-8'))
    by_identity={}
    for row in problems:
        key=canonical_url(row.get('url'))
        if key:by_identity.setdefault(key,row)
    wiki,entries=collect();added=[]
    for key,item in entries.items():
        existing=by_identity.get(key)
        if existing:
            item['problemId']=existing['id']
            if existing['encoded'].get('wikiExample'):
                encoded=existing['encoded']
                if encoded.get('difficulty') is None:
                    if not encoded.get('difficultySource'):encoded['difficultySource']='未知 · 尚未核实原站评级'
                    encoded.setdefault('difficultyConfidence','UNKNOWN')
                if not encoded.get('tags') and not encoded.get('knowledgeCategories'):
                    encoded['knowledgeCategories']=[];encoded['knowledgeReviewRequired']=True
            continue
        identity='wiki-example-'+hashlib.sha256(key.encode()).hexdigest()[:20]
        label=item['references'][0]['label'] or item['platform']+' '+item['code']
        label=re.sub(r'^例题[：:]\s*','',label)
        title=problem_title(label)
        if 'identityProof' in item:title=item['identityProof']['title']
        encoded={'id':identity,'title':title,'contest':item['platform'],'problem':item['code'],'platform':item['platform'],'url':item['url'],'status':'未做','date':'','difficulty':None,'difficultySource':'未知 · 尚未核实原站评级','difficultyConfidence':'UNKNOWN','tags':[],'knowledge':'','knowledgeCategories':[],'knowledgeReviewRequired':True,'catalogStatementReady':False,'catalogReplayReady':False,'wikiExample':True,'metadataProvenance':{'kind':'bundled-oi-wiki-link','references':item['references']}}
        raw={'场次':item['platform'],'题号':item['code'],'题名':title,'难度':'','知识点':'','状态':'未做','日期':''}
        row={'id':identity,'url':item['url'],'raw':raw,'encoded':encoded};problems.append(row);by_identity[key]=row;added.append(row);item['problemId']=identity
    imported=sum(bool(by_identity[key]['encoded'].get('wikiExample')) for key in entries)
    manifest={'schema':1,'wikiSha256':hashlib.sha256(wiki.read_bytes()).hexdigest(),'articles':41,'problemCount':len(entries),'addedCount':imported,'reusedCount':len(entries)-imported,'entries':list(entries.values())}
    return problems,added,manifest

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    problems,added,manifest=prepare()
    if args.apply:
        for path,value in [(ROOT/'data/library/problems.json',problems),(ROOT/'backend/resources/wiki-examples.json',manifest)]:
            path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'problemLinks':manifest['problemCount'],'newRows':len(added),'reusedRows':manifest['reusedCount'],'totalProblems':len(problems),'applied':args.apply},ensure_ascii=False))

if __name__=='__main__':main()
