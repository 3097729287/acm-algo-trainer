"""Extract explicit technique metadata from identified public editorial documents.

Requires pypdf for PDFs. Inputs are a local JSON source index and the public seed;
neither user state nor an API key is read. Documents are identified by at least
three matching original task titles; headings then assign each page to a task.
Only metadata and source URLs are saved, never copied solution bodies.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from knowledge import enrich_row, normalize_tags

TECHNIQUES={
    '线段树':r'segment\s*tree|线段树', '树状数组':r'Fenwick|树状数组|binary indexed tree',
    '并查集':r'disjoint.set|union.find|\bDSU\b|并查集', '二分查找':r'binary search|二分(?:答案|查找)',
    '双指针':r'two.pointer|双指针', '贪心':r'\bgreedy\b|贪心', '动态规划':r'dynamic programming|\bDP\b|动态规划',
    '网络流':r'network flow|maximum flow|\bDinic\b|网络流|最大流', '最小割':r'minimum.cut|\bmin.cut\b|最小割',
    '费用流':r'min.cost.*flow|minimum.cost.*flow|费用流', '最短路':r'\bDijkstra\b|shortest path|最短路',
    '最小生成树':r'minimum spanning tree|\bKruskal\b|最小生成树',
    '二分图匹配':r'bipartite matching|二分图匹配', '拓扑排序':r'topological sort|拓扑排序',
    'KMP':r'\bKMP\b|Knuth.Morris.Pratt', '后缀数组':r'suffix array|后缀数组',
    '后缀自动机':r'suffix automaton|后缀自动机', '字典树':r'\btrie\b|字典树',
    '哈希':r'rolling hash|hashing|字符串哈希', 'Manacher':r'\bManacher\b',
    'FFT':r'\bFFT\b|fast Fourier|快速傅里叶', 'NTT':r'\bNTT\b|number theoretic transform|快速数论变换',
    '组合计数':r'combinatorics|binomial coefficient|组合计数', '莫比乌斯反演':r'M[oö]bius inversion|莫比乌斯反演',
    '树链剖分':r'heavy.light decomposition|树链剖分', '点分治':r'centroid decomposition|点分治',
    '凸包':r'convex hull|凸包', '扫描线':r'sweep.line|扫描线', '计算几何':r'computational geometry|计算几何',
    '单调栈':r'monotonic stack|单调栈', '单调队列':r'monotonic queue|单调队列',
    '状压 DP':r'bitmask.*(?:DP|dynamic programming)|(?:DP|dynamic programming).*bitmask|状压',
    '期望与概率':r'expected value|probability|数学期望|概率', '递推':r'recurrence relation|递推关系',
}


def compact(text):
    return ''.join(c for c in unicodedata.normalize('NFKC',text).casefold() if c.isalnum())


def pages(path):
    if path.suffix.lower()=='.pdf':
        from pypdf import PdfReader
        return [page.extract_text() or '' for page in list(PdfReader(path).pages)[:180]]
    if path.suffix.lower()=='.pptx':
        with zipfile.ZipFile(path) as archive:
            names=sorted((name for name in archive.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',name)),key=lambda name:int(re.search(r'\d+',name)[0]))
            return [' '.join(node.text or '' for node in ET.fromstring(archive.read(name)).iter() if node.tag.endswith('}t')) for name in names]
    return []


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index',type=Path,required=True)
    args=parser.parse_args()
    seed=ROOT/'data/library/problems.json'
    entries=json.loads(seed.read_text('utf8'))
    groups=defaultdict(dict)
    for entry in entries:
        value=entry['encoded']
        if not re.search('ICPC|CCPC',value['contest']):continue
        name=re.sub(r'（Gym \d+）','',value['contest'])
        groups[name].setdefault(compact(value['title']),[]).append(value)
    proofs=defaultdict(list);documents=[]
    for document in json.loads(args.index.read_text('utf8')):
        if not document.get('ok'):continue
        try:texts=pages(Path(document['path']))
        except Exception:continue
        combined=compact('\n'.join(texts));matched=[]
        for name,titles in groups.items():
            hits=sum(len(title)>=8 and title in combined for title in titles)
            if hits>=3 and hits>=len(titles)*.25:matched.append((hits,name))
        if not matched:continue
        best=max(score for score,_ in matched)
        chosen=[name for score,name in matched if score==best]
        assigned=0
        for name in chosen:
            titles=groups[name];last=None
            for page in texts:
                heading=compact(page[:550]);found=[title for title in titles if len(title)>=8 and title in heading]
                if len(found)==1:last=found[0]
                elif len(found)>1:last=None;continue
                else:
                    marker=re.search(r'(?:\bProblem\s+|^\s*)([A-Z])\s*[.：:\-—]\s*',page[:280],re.M)
                    if marker:
                        candidates=[title for title,values in titles.items() if any(v['problem']==marker[1] for v in values)]
                        last=candidates[0] if len(candidates)==1 else None
                    else:last=None
                if not last:continue
                body='\n'.join(line for line in page.splitlines() if compact(line) not in titles)
                tags=[]
                for tag,pattern in TECHNIQUES.items():
                    matches=list(re.finditer(pattern,body,re.I))
                    if any(not re.search(r'not\s|wrong|fails?|doesn.t|无需|不需要|错误|不可行',body[max(0,m.start()-35):min(len(body),m.end()+35)],re.I) for m in matches):tags.append(tag)
                if not tags:continue
                for row in titles[last]:
                    proofs[row['id']].append({'source':document['source'],'tags':tags,'verified':False})
                    assigned+=1
        documents.append({'source':document['source'],'matchedContests':chosen,'matchedTitles':best,'assignedPages':assigned})
    new=0;updated=0;public_path=ROOT/'backend/resources/public-knowledge.json'
    public=json.loads(public_path.read_text('utf8'))
    for entry in entries:
        row=entry['encoded'];proof=proofs.get(row['id'])
        if not proof:continue
        before=set(row.get('tags',[]));value=row
        for item in proof:value=enrich_row(value,algorithm_evidence=item)
        new+=not before and bool(value.get('tags'));updated+=bool(set(value.get('tags',[]))-before)
        value['knowledgeAnalysis']['confidence']='medium'
        value['knowledgeAnalysis']['source']='public-editorial-terms'
        entry['encoded']=value;entry['raw']['知识点']=value.get('knowledge','')
        tags=list(dict.fromkeys(t for p in proof for t in p['tags']))
        normalized = normalize_tags(tags, official=True)
        if (normalized['tags'] or normalized['categories']) and row['url'] not in public['problems']:
            public['problems'][row['url']]={'tags':tags,'source':proof[0]['source'],'reason':'对应原赛题解明确技术词；自动匹配题单与题目，算法未重新验证'}
    seed.write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n','utf8')
    public_path.write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n','utf8')
    report={'version':'1.0.18','documents':documents,'problemsWithEvidence':len(proofs),'newlyTagged':new,'updated':updated,
            'notice':'知识标签来自对应公开题解的明确技术词，题单与题目标题先行匹配；算法未重新验证。未识别文档和扫描页不猜测。'}
    (ROOT/'backend/resources/xcpc-knowledge-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='documents'},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
