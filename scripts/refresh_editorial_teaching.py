"""Connect reusable, authored foundations to existing public editorials.

Dry run by default. --write updates only public source JSON and (when explicitly
requested) the educational Markdown archive. Reference programs and all old
lessons/images are preserved. No user database, release, or install is opened.
"""
import argparse
import base64
from collections import Counter, defaultdict
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs' / 'foundations'
SOURCE = ROOT / 'data' / 'library'
VERSION = '2026-10-22-foundations-v1'
START, STOP = '<!-- reusable-foundations:start -->', '<!-- reusable-foundations:end -->'

TAG_LESSONS = {
    '模拟':'enumeration', '枚举':'enumeration', '递推':'dp', '结论与计数':'counting',
    '贪心':'greedy', '构造':'construction', '排序':'sort', '前缀和':'prefix',
    '差分':'difference', '二分查找':'bounds', '二分答案':'binary-answer',
    '线性 DP':'dp', '背包 DP':'knapsack', '树形 DP':'trees',
    '数位 DP':'subset-dp', '状压 DP':'subset-dp', '区间 DP':'subset-dp',
    '记忆化搜索':'subset-dp', '分布压缩 DP':'dp',
    '组合计数':'counting', '取模与同余':'modular', '乘法逆元':'modular', '快速幂':'modular',
    '素数':'number-theory', '最大公约数':'number-theory', '欧拉函数':'number-theory',
    '整除分块':'number-theory', '整数平方根':'number-theory',
    '双指针':'two-pointers', '连续段':'coordinates', '扫描线':'coordinates', '离散化':'coordinates',
    'BFS':'graphs', 'DFS':'graphs', '图论':'graphs', '连通块计数':'graphs', '二分图判定':'graphs',
    '最短路':'shortest-path', '差分约束':'shortest-path',
    '并查集':'dsu', '可撤销并查集':'dsu', '树状数组':'fenwick',
    '线段树':'segment-tree', '可持久化线段树':'segment-tree',
    'LCA':'trees', '倍增':'trees', 'DFS 序':'trees', '树的直径':'trees', '虚树':'trees',
    '拓扑排序':'topology', '生成树':'topology',
    '栈':'queue-stack', '队列':'queue-stack', '堆':'heap',
    '单调栈':'monotonic', '单调队列':'monotonic', '势能分析':'monotonic', '摊还分析':'monotonic',
    '置换环':'permutations', '位运算':'bitwise', 'bitset':'bitwise',
    '字典树':'trie', '哈希':'hashing', '期望与概率':'probability', '博弈论':'games',
    '计算几何':'geometry', '鸽巢原理':'counting', '高精度':'integer',
}
TOOL_NAMES = {
    'vector','iterators','lambda','integer','bindings','maps','sets',
    'heap','queue-stack','strings','recursion','bitwise','numeric-tools',
}


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def programs(text):
    return re.findall(r'^```(?:cpp|c\+\+)\s*\n(.*?)^```\s*$', text, re.S|re.M)


def reference_programs(text):
    # Include original annotated excerpts as well as the full program. Teaching
    # additions use cxx, so none can be confused with these pre-existing blocks.
    return programs(text)


def strip_comments(code):
    # Keep strings out of token detection, while preserving newlines.
    return re.sub(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
                  lambda m: '\n'*m[0].count('\n') or ' ', code, flags=re.S)


def selected_lessons(row, problem):
    code = strip_comments('\n'.join(reference_programs(row['markdown'])))
    result=[]
    def add(name):
        if name not in result: result.append(name)
    # Catalog concepts describe the existing solution; explicit library/language
    # tools are additionally recognized in the reference program, never in prose.
    for tag in problem.get('tags', []):
        if tag in TAG_LESSONS: add(TAG_LESSONS[tag])
    patterns = [
        ('bounds',r'\b(?:lower_bound|upper_bound|equal_range)\s*\('),
        ('lambda',r'\[[^\]\n]*\]\s*(?:\([^;{}]*\)\s*(?:mutable\s*)?(?:->[^{};]+)?|)\{'),
        ('lambda',r'\bfunction\s*<'),
        ('vector',r'\bvector\s*<'), ('bindings',r'\b(?:pair|tuple)\s*<|\bauto\s*(?:const\s*)?&?\s*\['),
        ('sort',r'\b(?:sort|stable_sort)\s*\('),
        ('maps',r'\b(?:unordered_map|map|multimap)\s*<'),
        ('sets',r'\b(?:unordered_set|set|multiset)\s*<'),
        ('heap',r'\bpriority_queue\s*<'),
        ('queue-stack',r'\b(?:queue|deque|stack)\s*<'),
        ('strings',r'\bstring\b|\b(?:substr|getline)\s*\('),
        ('numeric-tools',r'\b(?:iota|accumulate|fill|memset)\s*\('),
        ('integer',r'\b(?:long\s+long|__int128|int64_t|uint64_t)\b|\busing\s+ll\b'),
    ]
    for name, pattern in patterns:
        if re.search(pattern, code): add(name)
    if 'bounds' in result: add('iterators')
    # Input/output shifts are not integer bit shifts. Remove complete stream
    # expressions, then recognize actual masks/shifts/xor in the remaining code.
    nonstream = re.sub(r'\b(?:cin|cout|cerr)\s*(?:>>|<<)[^;]*;', '', code)
    if re.search(r'\^\s*[\w(]|\b1(?:LL|ULL|ll|ull)?\s*<<|>>=|<<=|&\s*(?:1(?:LL|ULL)?\b|\(-|-[a-zA-Z_])|\bbitset\s*<',nonstream):
        add('bitwise')
    if re.search(r'\b(?:dfs|search)\s*\(',code):
        add('recursion')
    if not result: add('enumeration')
    return result


def lesson_sources():
    result={}
    for path in sorted(DOCS.glob('*.md')):
        text=path.read_text(encoding='utf-8').strip()
        title,body=text.split('\n',1)
        images={}
        for target in re.findall(r'!\[[^]]*\]\(([^)]+)\)',body):
            source=DOCS/target
            if not source.is_file():raise ValueError('Missing authored illustration: '+str(source))
            images['assets/foundations/'+source.name]='data:image/svg+xml;base64,'+base64.b64encode(source.read_bytes()).decode()
            body=body.replace(']('+target+')','](assets/foundations/'+source.name+')')
        result[path.stem]={'title':title.removeprefix('# '),'body':body.strip(),'images':images,'path':path}
    return result


CORRIDOR_DEFAULT = r'''#### 先看哪些区间在查询点仍然有效

图中所有线段都表示闭区间，竖线是查询位置 $x=5$。绿色 A、B 已经在左侧结束；红色 C、D、E、F 仍覆盖查询点；灰色 G、H 还没有开始。实心圆表示端点也属于区间。

![八个闭区间与同一个查询点：六个已开始，扣掉两个已结束，剩四个覆盖](assets/foundations/interval-coverage.svg)

先计入所有左端点满足 $l_j\le x$ 的区间：A 到 F，共六个。这里多算了已经结束的 A、B，它们的右端点满足 $r_j<x$，减掉这两个就剩四个真正覆盖的位置。

被减的区间必定已计入，因为 $l_j\le r_j<x$；没有开始的 G、H 既不加也不减。因此

$$d(x)=\#\{j:l_j\le x\}-\#\{j:r_j<x\}.$$

图中 D 的 $r_j=x$，端点仍覆盖 $x$，不能扣除；F 的 $l_j=x$，已经开始，必须计入。这分别决定了第一项包含等号、第二项不含等号。

#### 两个边界函数怎样对应这两个数量

排序后的左端点为 $[1,1,2,3,4,5,6,7]$。对五调用 `upper_bound`，得到第一个大于五的位置，下标六，前六项恰好都是 $l_j\le5$。

排序后的右端点为 $[3,4,5,6,7,8,8,9]$。对五调用 `lower_bound`，得到第一个大于等于五的位置，下标二，前两项恰好都是 $r_j<5$。

两个函数返回迭代器，减各自的 `begin()` 才得到前面有几个元素，所以代码得到 $d(5)=6-2=4$。完整的接口、二分实现、重复值和复杂度见上方可展开的二分基础课。

#### 查询原区间的两个端点

`cover(x)` 是用 lambda 定义的局部查询函数：参数 `x` 每次调用传入，`[&]` 使它引用外层排序后的 `ls`、`rs`。定义时只保存可调用对象，不执行查询；调用 `cover(l)`、`cover(r)` 时才分别计算覆盖数。两个数组在调用期间仍存在，且不再修改。

排序只用来查询，原始配对保存在 `seg`。逐个判断 `abs(cover(l)-cover(r)) >= p`，每个区间分别贡献零或一。相同区间仍是不同记录，不去重。

排序 $O(n\log n)$；每次 `cover` 做两次 $O(\log n)$ 二分，共查询 $2n$ 个端点，所以总时间 $O(n\log n)$，空间 $O(n)$。只按端点大小比较，不按最大坐标开数组。'''

CORRIDOR_EXTRA = r'''

#### 从逐个判断推到集合相减

对任意区间 $j$，覆盖条件是两个条件同时成立：$l_j\le x$ 且 $r_j\ge x$。先只检查第一个条件，把已经开始的区间集合记为 $S$；在 $S$ 中，不满足第二个条件的恰好是 $r_j<x$ 的集合 $E$。区间端点保证 $l_j\le r_j$，所以 $E\subseteq S$，可以直接用 $|S|-|E|$，无需再求一次交集。这就是两项独立计数能够组合成覆盖数的原因。

把图上的其他位置也核对一次：

| 查询点 | 已开始数量 | 已结束数量 | 覆盖数量 |
|---|---|---|---|
| $x=3$ | $4$ | $0$ | $4$ |
| $x=4$ | $5$ | $1$ | $4$ |
| $x=5$ | $6$ | $2$ | $4$ |
| $x=7$ | $8$ | $4$ | $4$ |

特别是查询三时，A 的右端点等于三，依旧属于覆盖集合；查询七时，C 的右端点等于七也不能先移除。闭区间边界不是实现细节，而是计数条件本身。

#### 从通用二分写法回到这两行代码

`upper_bound(ls.begin(),ls.end(),x)-ls.begin()` 跨过的是所有“不大于 $x$”的左端点；若改用 `lower_bound`，会漏掉恰在 $x$ 开始的 F。`lower_bound(rs.begin(),rs.end(),x)-rs.begin()` 跨过的是所有“严格小于 $x$”的右端点；若改用 `upper_bound`，又会把恰在 $x$ 结束的 D 错删。

把两端点各自排序后，它们在数组中的位置不再表示原来是哪一个区间；这个查询只需要两种集合的大小，因此无碍。要回到某条原区间的左右端点时，必须读 `seg`，不能把排序后的 `ls[i]` 和 `rs[i]` 重新配对。'''


def corridor(text, detailed):
    replacement='### 思路\n\n'+CORRIDOR_DEFAULT
    if detailed:replacement+=CORRIDOR_EXTRA
    replacement+='\n\n'
    return re.sub(r'^### 思路\s*\n.*?(?=^### 参考代码)',lambda m:replacement,text,flags=re.S|re.M)


def inline_lesson(name,source):
    title=source['title']
    body=re.sub(r'^(#{2,4}) ', lambda m:'#'*(len(m[1])+2)+' ',source['body'],flags=re.M)
    # Pedagogical excerpts are cxx; only the existing complete reference
    # program uses cpp, keeping md_full and reference extraction unambiguous.
    body=body.replace('```cpp','```cxx')
    return '### 从零讲：'+title+'\n\n'+body


def enrich(text,names,sources,detailed=False,target=False):
    text=re.sub(re.escape(START)+r'.*?'+re.escape(STOP)+r'\n*','',text,flags=re.S)
    old=reference_programs(text)
    if target:text=corridor(text,detailed)
    chapters='\n\n'.join(inline_lesson(name,sources[name]) for name in names)
    block=START+'\n\n'+chapters+'\n\n'+STOP+'\n\n'
    match=re.search(r'^### (?:从零讲|手算|思路)',text,re.M)
    if not match:
        match=re.search(r'^### (?!题意\s*$|参考代码\s*$|易错点\s*$)',text,re.M)
    if not match:raise ValueError('No teaching insertion point')
    text=text[:match.start()]+block+text[match.start():]
    if reference_programs(text)!=old:raise AssertionError('Reference program was changed')
    return text


def backup(path,folder):
    mirror=str(path.parent.resolve()).replace(':','').replace('\\','_').replace('/','_')
    target=folder/mirror/path.name
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():shutil.copy2(path,target)


def check_images(row):
    for target in re.findall(r'!\[[^]]*\]\(([^)]+)\)',row['markdown']):
        if target.startswith(('http:','https:','data:')):continue
        if target not in row.get('images',{}):raise ValueError('Unresolved image '+row['problem_id']+' '+target)
        base64.b64decode(row['images'][target].split(',',1)[1],validate=True)


def apply(write=False,archive=None):
    from editorial_figures import draw
    draw()
    sources=lesson_sources()
    data={n:load(SOURCE/(n+'.json')) for n in ['problems','solutions','detailed_solutions','lectures','links','meta']}
    original_meta=dict(data['meta'])
    fingerprints={n:hashlib.sha256((SOURCE/(n+'.json')).read_bytes()).hexdigest() for n in data}
    problems={row['id']:row['encoded'] for row in data['problems']}
    defaults={row['problem_id']:row for row in data['solutions']}
    details={row['problem_id']:row for row in data['detailed_solutions']}
    if defaults.keys()!=details.keys():raise ValueError('Both original editorial variants must already exist')
    target_ids={pid for pid in defaults if problems[pid].get('title')=='小月的长廊'}
    chosen={pid:list(dict.fromkeys(selected_lessons(defaults[pid],problems[pid])+selected_lessons(details[pid],problems[pid]))) for pid in defaults}
    uses=defaultdict(list)
    for pid,names in chosen.items():
        for name in names: uses[name].append(pid)
    stamp=dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    save=ROOT/'.backups'/('editorial-teaching-'+stamp)
    report={'version':VERSION,'problemCount':len(defaults),'variants':2,'authoredLessons':len(sources),
            'appliedLessons':len(uses),'lessonUseCounts':{k:len(v) for k,v in uses.items()},
            'targetProblems':sorted(target_ids),'archiveFiles':0,'archiveProblems':0,
            'referenceProgramsChanged':0,'previousLessonsDeleted':0,'allArticlesHumanReviewed':False,
            'scope':'Existing public editorials; no new problem/editorial, personal database or live install.'}
    archive_jobs=defaultdict(dict)
    coverage=[]
    for variant,rows in [('solutions',data['solutions']),('detailed_solutions',data['detailed_solutions'])]:
        for row in rows:
            pid=row['problem_id'];names=chosen[pid];old=dict(row)
            # Reuse an existing problem illustration in both reading variants.
            other=details[pid] if variant=='solutions' else defaults[pid]
            row['images']={**other.get('images',{}),**row.get('images',{})}
            row['markdown']=enrich(row['markdown'],names,sources,variant=='detailed_solutions',pid in target_ids)
            for name in names:row['images'].update(sources[name]['images'])
            if pid in target_ids:
                file=DOCS/'assets'/'interval-coverage.svg'
                row['images']['assets/foundations/'+file.name]='data:image/svg+xml;base64,'+base64.b64encode(file.read_bytes()).decode()
            # If the other variant had a topic-specific illustration missing
            # here, present it next to the derivation with its original caption.
            original_images=re.findall(r'(!\[[^]]*\]\(([^)]+)\))',other['markdown'])
            current_targets=set(re.findall(r'!\[[^]]*\]\(([^)]+)\)',row['markdown']))
            missing=[img for img,path in original_images if path not in current_targets and path in old.get('images',{})|other.get('images',{}) and 'assets/foundations/' not in path]
            if missing:
                row['markdown']=row['markdown'].replace('### 参考代码','\n\n'.join(dict.fromkeys(missing))+'\n\n### 参考代码',1)
            check_images(row)
            assert reference_programs(row['markdown'])==reference_programs(old['markdown'])
            rel=row['source_path'].replace('\\','/').removeprefix('题解/')
            letter=problems[pid].get('problem')
            if letter:archive_jobs[rel][letter]=(pid,names,variant=='detailed_solutions')
            coverage.append({'problemId':pid,'variant':variant,'lessons':names,
                             'images':len(re.findall(r'!\[',row['markdown'])),
                             'referenceHash':hashlib.sha256('\n'.join(reference_programs(row['markdown'])).encode()).hexdigest()})
    existing_ids={row['id'] for row in data['lectures']}
    for name,source in sources.items():
        identity='lecture:foundation-'+name
        body='# '+source['title']+'\n\n'+source['body']+'\n'
        first=(uses.get(name) or [None])[0]
        tag=next((tag for tag,slug in TAG_LESSONS.items() if slug==name),None)
        tool=name in TOOL_NAMES or name in ('bounds','sort')
        knowledge='C++ 语言与标准库' if tool else (tag or '基础知识')
        content={'id':identity,'available':True,'title':'从零讲：'+source['title'],
                 'concept':source['title'],'displayTitle':source['title'],'knowledgeName':knowledge,
                 'topic':source['title'],'category':'C++ 语言与标准库' if tool else '算法基础',
                 'categories':['C++ 语言与标准库' if tool else '算法基础'],
                 'tags':[tag] if tag else [],'sourceTags':[],'catalogTags':[],
                 'sourceProblemIds':uses.get(name,[]),'sourceContest':'','sourceProblem':'',
                 'sourceTitle':'独立基础课','sourcePath':'docs/foundations/'+name+'.md',
                 'sourceHeading':source['title'],'originalTitle':source['title'],'originalConcept':source['title'],
                 'editorialVersion':VERSION,'curationVersion':'lectures-v1.1','conceptSource':'independent-foundation',
                 'sourceMarkdown':body,'sourceHash':hashlib.sha256(body.encode()).hexdigest(),
                 'originalSourceHash':hashlib.sha256(body.encode()).hexdigest(),
                 'sourceCodeHashes':[],'markdown':body,'images':source['images'],
                 'excerpt':re.sub(r'[#`*]','',source['body'].split('\n\n')[0])[:180],
                 'quality':{'normalized':True,'supplemented':True,'sourceAlgorithmReverified':False,
                            'catalogClassificationChanged':False}}
        entry={'id':identity,'content':content}
        if identity in existing_ids:
            position=next(i for i,r in enumerate(data['lectures']) if r['id']==identity)
            data['lectures'][position]=entry
        else:data['lectures'].append(entry)
    links={(r['problem_id'],r['lecture_id']) for r in data['links']}
    for pid,names in chosen.items():
        position=max((r['position'] for r in data['links'] if r['problem_id']==pid),default=-1)+1
        for name in names:
            identity='lecture:foundation-'+name
            if (pid,identity) not in links:
                data['links'].append({'kind':'explicit','lecture_id':identity,'position':position,'problem_id':pid})
                position+=1;links.add((pid,identity))
    audit=json.loads(data['meta'].get('lectureAudit','{}'))
    audit.update(lectureCount=len(data['lectures']),normalizedLectureCount=sum(bool(r['content'].get('quality',{}).get('normalized')) for r in data['lectures']),
                 independentFoundationCount=len(sources),teachingRevision=VERSION)
    data['meta']['lectureAudit']=json.dumps(audit,ensure_ascii=False)
    data['meta']['teachingRevision']=VERSION
    serialize=lambda value:json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    changed_sources=any(serialize(data[n])!=(SOURCE/(n+'.json')).read_text(encoding='utf-8')
                        for n in ['solutions','detailed_solutions','lectures','links'])
    if changed_sources or data['meta']!=original_meta:
        data['meta']['revision']=str(int(data['meta'].get('revision','0'))+1)
    if write:
        save.mkdir(parents=True)
        for name in ['solutions','detailed_solutions','lectures','links','meta']:
            path=SOURCE/(name+'.json')
            if hashlib.sha256(path.read_bytes()).hexdigest()!=fingerprints[name]:
                raise RuntimeError('Concurrent public source change: '+name)
            if serialize(data[name])!=path.read_text(encoding='utf-8'):
                backup(path,save/'before')
                path.write_text(serialize(data[name]),encoding='utf-8')
        (save/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2),encoding='utf-8')
    if archive:
        archive=Path(archive).resolve()
        archive_paths=sorted(p for p in archive.rglob('*题解.md') if not any(part.startswith('_') for part in p.relative_to(archive).parts))
        for path in archive_paths:
            rel=path.relative_to(archive).as_posix()
            jobs=archive_jobs.get(rel,{})
            if not path.is_relative_to(archive):raise ValueError('Archive path escapes requested root')
            if not path.is_file():continue
            original=path.read_text(encoding='utf-8-sig');matches=list(re.finditer(r'^## ([A-Z][0-9]?)\. .*$',original,re.M))
            catalog={}
            for line in original.splitlines():
                cells=[part.strip() for part in line.strip().strip('|').split('|')]
                if len(cells)==4 and re.fullmatch('[A-Z][0-9]?',cells[0]):
                    tags=[re.sub(r'\[[^]]*\]','',part).strip() for part in cells[2].split('+')]
                    catalog[cells[0]]={'tags':tags,'title':cells[1]}
            text=original;count=0
            for match in reversed(matches):
                letter=match[1]
                stop=re.search(r'^## ',original[match.end():],re.M)
                end=match.end()+stop.start() if stop else len(original)
                old=original[match.start():end]
                if letter in jobs:
                    pid,names,detailed=jobs[letter]
                else:
                    description=catalog.get(letter,{'tags':[]})
                    names=selected_lessons({'markdown':old},description)
                    pid='archive:'+rel+'::'+letter
                    detailed='详细' in path.name
                    if description.get('title')=='小月的长廊':target_ids.add(pid)
                if not re.search(r'^### ',old,re.M):
                    raise ValueError('Unrecognized archive article: '+str(path)+' '+letter)
                section=enrich(old,names,sources,detailed,pid in target_ids)
                text=text[:match.start()]+section+text[end:];count+=1
                if write:
                    for name in names:
                        for key,value in sources[name]['images'].items():
                            asset=path.parent/key;asset.parent.mkdir(parents=True,exist_ok=True)
                            payload=base64.b64decode(value.split(',',1)[1])
                            if asset.exists() and asset.read_bytes()!=payload:backup(asset,save/'before')
                            asset.write_bytes(payload)
                    if pid in target_ids:
                        asset=path.parent/'assets/foundations/interval-coverage.svg';asset.parent.mkdir(parents=True,exist_ok=True)
                        if asset.exists() and asset.read_bytes()!=(DOCS/'assets/interval-coverage.svg').read_bytes():backup(asset,save/'before')
                        shutil.copy2(DOCS/'assets/interval-coverage.svg',asset)
            if count:
                report['archiveFiles']+=1;report['archiveProblems']+=count
                if write and text!=original:
                    backup(path,save/'before');path.write_text(text,encoding='utf-8')
    report.update(lectureCount=len(data['lectures']),relationshipCount=len(data['links']),
                  articlesWithIllustrations=sum(r['images']>0 for r in coverage),
                  dryRun=not write)
    if write:
        (save/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        (ROOT/'data'/'editorial-teaching-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    parser.add_argument('--archive',type=Path,help='Explicitly authorized educational archive to update, never a live database')
    args=parser.parse_args()
    print(json.dumps(apply(args.write,args.archive),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
