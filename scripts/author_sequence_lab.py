"""Stage verified Algorithm Lab problems in public text sources only.

The ten statements are concise Chinese restatements, with all algorithmic
conditions, input contracts and official samples retained. No personal DBs or
the original educational archive are read or written.
"""
import argparse
import base64
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
BACKUP = ROOT / '.backups/sequence-lab-20261023'
VERSION = '2026-10-24-sequence-lab-v1'
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/common')]
from knowledge import category_path, enrich_row


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def read(name):
    return json.loads((ROOT / f'data/library/{name}.json').read_text(encoding='utf-8'))


def canonical(url):
    match = re.search(r'/(?:problemset/problem|contest)/(\d+)/(?:problem/)?([A-Za-z]\d*)', urlparse(url or '').path)
    return ''.join(match.groups()).upper() if match else None


def image_for(p):
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 365" role="img" aria-labelledby="title"><title id="title">' + html.escape(p['title']) + '：教学小例</title><rect width="920" height="365" rx="12" fill="#fff"/><g font-family="Microsoft YaHei,Arial,sans-serif" fill="#253340">']

    def text(x, y, value, size=17, color='#253340'):
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">{html.escape(str(value))}</text>')

    def row(values, y, label, selected=(), start=1):
        text(24,y+28,label,15)
        for i,value in enumerate(values):
            x=244+i*76; chosen=i in selected
            parts.append(f'<rect x="{x}" y="{y}" width="68" height="49" rx="6" fill="{"#e2f3ed" if chosen else "#f1f4f7"}" stroke="{"#257c67" if chosen else "#a6b4c0"}"/>')
            text(x+17,y+30,value,19)
            text(x+22,y+66,i+start,12,'#657586')

    def bracket(l,r,y,caption,color='#257c67'):
        x1=244+l*76;x2=244+(r+1)*76-8
        parts.append(f'<path d="M{x1},{y-7} V{y} H{x2} V{y-7}" stroke="{color}" stroke-width="2" fill="none"/>')
        text(x1,y+24,caption,15,color)

    text(24,35,p['pid']+' · 教学小例',22)
    kind=p['kind']
    if kind=='fence':
        row(p['mini']['a'],78,'原位置的木板高度',range(2,5));bracket(2,4,169,'恰好 3 块：6+1+1=8')
        text(24,232,'P[5] 取前五块，再减去 P[2] 的前两块，留下位置 3～5。',18)
        text(24,279,'比较的是每个起点的整段总和；输出起点 3。',18)
    elif kind=='stones':
        row([4,1,3,2],78,'原序账本',range(1,3));row([1,2,3,4],188,'排序副本账本',range(1,3))
        text(24,310,'同样位置 2～3：原序 1+3=4，排序副本 2+3=5。',18)
    elif kind=='coffee':
        # Actual recommendation intervals on a shared temperature axis.
        for i,(l,r) in enumerate(p['mini']['ranges']):
            y=75+i*32;text(24,y+6,f'配方 {i+1}：[{l},{r}]',14)
            parts.append(f'<line x1="{277+(l-1)*76}" y1="{y}" x2="{277+(r-1)*76}" y2="{y}" stroke="#327b9c" stroke-width="7" stroke-linecap="round"/>')
        row([1,2,2,2,1],182,'累计覆盖次数',range(1,4));row([0,1,1,1,0],274,'至少 2 份：每点记 0/1',range(1,4))
    elif kind=='greg':
        row([1,2,1],70,'操作编号 → 执行次数');row([2,6,5],170,'数组位置 → 最终增量');
        text(24,300,'原值 [1,2,3] + 增量 [2,6,5] = 最终 [3,8,8]。',18)
        text(24,335,'操作 2 被执行两次：其每次增量 2，要乘次数 2。',17)
    elif kind=='weighted':
        row([1,2,1],74,'固定的位置覆盖次数',[1]);row([1,5,3],179,'把大数放高次数位置',[1]);
        text(24,305,'两问 [1,2]、[2,3]：1+5 + 5+3 = 14。位置 2 的数贡献两次。',17)
    elif kind=='cards':
        row([4,1,2,10],74,'初始剩余区间',range(4));bracket(0,3,164,'从两端取较大者，先手取 10')
        text(24,237,'取牌顺序：先手 10 → 后手 4 → 先手 2 → 后手 1。',18)
        text(24,290,'得分 12 与 5；最后一张牌仍在区间内，循环要允许 l=r。',17)
    elif kind=='pairs':
        # Nodes represent distinct positions, even where values repeat.
        for i,v in enumerate([1,2,2,4]):
            x=265+i*132
            parts.append(f'<circle cx="{x}" cy="105" r="24" fill="#e2f3ed" stroke="#257c67"/>');text(x-7,111,v,19);text(x-22,69,f'位置 {i+1}',13)
        for a,b,y in [(0,1,188),(0,2,240),(1,2,296)]:
            xa=265+a*132;xb=265+b*132
            parts.append(f'<path d="M{xa},135 Q{(xa+xb)/2},{y} {xb},135" stroke="#257c67" stroke-width="3" fill="none"/>')
        text(24,324,'和在 [3,4] 的三对：(1,2)、(1,3)、(2,3)。重复值仍是不同位置。',17)
    elif kind=='books':
        row([3,1,2,1],85,'按原顺序的阅读时间',range(1,4));bracket(1,3,179,'连续 3 本，用时 1+2+1=4 ≤ 5')
        text(24,255,'加入右端后超时才移走左端，合法后再更新最长长度。',18)
        text(24,305,'正好等于预算也合法；不能排序后挑短书。',18)
    elif kind=='friends':
        text(24,82,'财富轴（友谊值标在点下）',17)
        parts.append('<line x1="240" y1="145" x2="780" y2="145" stroke="#708090" stroke-width="2"/>')
        for m,s,x in [(1,4,280),(3,2,490),(5,10,700)]:
            parts.append(f'<circle cx="{x}" cy="145" r="8" fill="#257c67"/>');text(x-8,123,m,19);text(x-38,185,f'友谊 {s}',17)
        parts.append('<path d="M490,206 V218 H700 V206" fill="none" stroke="#257c67" stroke-width="3"/>')
        text(460,249,'财富差 2&lt;4' .replace('&lt;','<')+'，友谊 2+10=12',17,'#257c67')
        text(24,310,'三人全部选择时财富差 5−1=4，等于 d，已经不合法。',18)
    elif kind=='pokemon':
        row(list('aabcbc'),85,'房间按原顺序',range(1,4));bracket(1,3,179,'abc：集齐全部三类，长度 3')
        text(24,254,'从 aabc 移去第一个 a 后，仍有一个 a，种类数仍为 3。',18)
        text(24,307,'只有计数变成 0，才真正失去一种宝可梦。',18)
    parts.append('</g></svg>')
    return ''.join(parts)


def main(apply=False):
    BACKUP.mkdir(exist_ok=True)
    subprocess.run(['node','frontend/scripts/export-sequence-course.mjs',str(BACKUP/'course-export.json')],cwd=ROOT,check=True)
    data=json.loads((BACKUP/'course-export.json').read_text(encoding='utf-8'))
    ratings=json.loads((BACKUP/'source-ratings.json').read_text(encoding='utf-8'))
    rating_index={str(p['contestId'])+p['index']:p for p in ratings}
    tables={name:read(name) for name in ['problems','statements','solutions','detailed_solutions','lectures','links']}
    old_counts={name:len(rows) for name,rows in tables.items()}
    existing={canonical(row.get('url')):row['id'] for row in tables['problems'] if canonical(row.get('url'))}
    base_lectures={r['id']:r['content'] for r in tables['lectures']}
    selected=[];added=[]
    for course,problems in data['problems'].items():
        topic='前缀和' if course=='prefix-difference' else '双指针'
        source=ROOT/f'docs/foundations/{course if course=="prefix-difference" else "two-pointers-lab"}.md'
        foundation=source.read_text(encoding='utf-8')
        lid=f'lecture:sequence-{course}'
        related_ids=[]
        for p in problems:
            verified=rating_index[p['pid']]
            assert verified['rating']==p['rating']<=2200
            pid=existing.get(p['pid'],p['id']);related_ids.append(pid)
            if pid!=p['id']:
                # Keep every old editorial intact. This task normally adds ten
                # unseen identities; aliases stay attached to their old identity.
                selected.append({'pid':p['pid'],'id':pid,'state':'existing identity preserved; no replacement'})
                continue
            if any(row['id']==pid for row in tables['problems']):
                row=next(row for row in tables['problems'] if row['id']==pid)
                row['encoded']=enrich_row(row['encoded'])
                row['raw']['知识点']=row['encoded']['knowledge']
                selected.append({'pid':p['pid'],'id':pid,'state':'already staged'})
                continue
            group=('前缀和与差分' if course=='prefix-difference' else '双指针')+' 精选'
            tags=[topic]
            if p['kind'] in ['coffee','greg','weighted']:tags.append('差分')
            if p['kind'] in ['stones','weighted','pairs','friends']:tags.append('排序')
            encoded={'id':pid,'contest':group,'problem':p['pid'],'title':verified['name'],'originalTitle':verified['name'],'url':p['url'],'platform':'Codeforces','series':'算法实验室','contestFamily':'算法实验室','contestFullName':group,'status':'未做','date':'','difficulty':p['rating'],'difficultySource':'Codeforces 官方 rating','nativeDifficulty':p['rating'],'difficultyEstimated':False,'difficultyCheckedAt':'2026-10-23','difficultyEvidence':['https://codeforces.com/api/problemset.problems'],'tags':tags,'sourceTags':tags,'knowledge':topic,'knowledgeCategories':['基础算法'],'source':'algorithm-lab-curation','queue':None,'startedAt':None,'endedAt':None,'contestDate':None,'solutionAvailable':True,'detailedSolutionAvailable':True,'solutionState':'ready','algorithmLab':{'topic':course,'guided':True,'revision':1},'collectionSource':p['url']}
            raw={'_id':pid,'_url':p['url'],'_platform':'Codeforces','_series':'算法实验室','场次':group,'题号':p['pid'],'题名':verified['name'],'知识点':' + '.join(tags),'难度':str(p['rating']),'状态':'未做','日期':''}
            encoded=enrich_row(encoded)
            raw['知识点']=encoded['knowledge']
            tables['problems'].append({'id':pid,'url':p['url'],'raw':raw,'encoded':encoded})
            samples=[{'name':f'原站样例 {i+1}','input':pair[0],'output':pair[1]} for i,pair in enumerate(data['samples'][p['pid']])]
            statement=f"# {verified['name']}\n\n原题：[Codeforces {p['pid']}]({p['url']})。以下为保留全部算法条件的中文简述；情节文字从简。\n\n## 题目\n\n{p['statement']}\n\n## 输入、输出与数据范围\n\n{p['ranges']}\n"
            limits={'timeMs':{'816B':2500,'295A':1500,'363B':1000,'276C':1000,'381A':1000}.get(p['pid'],2000),'memoryMb':512 if p['pid']=='816B' else 256}
            tables['statements'].append({'problem_id':pid,'content':{'id':pid,'title':verified['name'],'url':p['url'],'markdown':statement,'samples':samples,'limits':limits,'statementAvailable':True,'statementVersion':3,'officialTags':verified['tags'],'sourceCheckedAt':'2026-10-23','restatement':True}})
            svg=image_for(p);image_path=f'assets/sequence/{p["pid"]}.svg';image_data='data:image/svg+xml;base64,'+base64.b64encode(svg.encode()).decode();images={image_path:image_data}
            detail_intro=f"## {p['pid']} · {verified['name']}\n\n题源：[原题]({p['url']})，Codeforces 官方 rating {p['rating']}（2026-10-23 API 核对）。\n\n### 题意与限制\n\n{p['statement']}\n\n{p['ranges']}\n\n"
            independent='<!-- reusable-foundations:start -->\n\n### 从零讲：'+foundation.removeprefix('# ').replace('\n','\n',1)+'\n\n'
            # Attach only language tools actually used by each preserved program.
            for tool in ['lecture:foundation-vector']+(['lecture:foundation-sort'] if 'sort(' in data['references'][p['pid']] else []):
                base=base_lectures.get(tool)
                if base:
                    independent+='\n\n'+base['markdown']+'\n'
                    tables['links'].append({'problem_id':pid,'lecture_id':tool,'kind':'explicit','position':'2' if tool.endswith('vector') else '3'})
            independent+='\n<!-- reusable-foundations:end -->\n\n'
            clues='\n\n'.join('**'+clue+'。** '+why for clue,why in p['clues'])
            picture=f"![{p['calculation']}]({image_path})\n\n"
            core=f"### 从哪些条件入手\n\n{clues}\n\n### 推导与覆盖\n\n{p['insight']}\n\n{picture}{p['calculation']}\n\n### 推到关键代码\n\n{p['state']}\n\n```cpp\n{p['line']}\n```\n\n{p['lineReason']}\n\n"
            debug=f"### 用极小数据排错\n\n{p['bug']}\n\n错误程序得到 {p['bugAnswer']}。{p['bugWhy']}\n\n### 换条件再判断\n\n{p['recall']}\n\n复测边界：\n\n"+'\n'.join('- '+x for x in p['tests'])+'\n\n'
            code=f"### 参考程序 · C++17\n\n```cpp\n{data['references'][p['pid']]}\n```\n\n复杂度：{p['complexity']}\n"
            brief=detail_intro+independent+f"### 思路\n\n{p['insight']}\n\n"+picture+p['calculation']+'\n\n'+p['lineReason']+'\n\n'+code
            detailed=detail_intro+independent+core+debug+code
            for key,markdown in [('solutions',brief),('detailed_solutions',detailed)]:
                tables[key].append({'problem_id':pid,'markdown':markdown,'images':images,'source_path':f'算法实验室/{course}/{p["pid"]}{"详细" if key=="detailed_solutions" else ""}题解.md','digest':digest(markdown),'teachingRevision':VERSION})
            tables['links'].append({'problem_id':pid,'lecture_id':lid,'kind':'explicit','position':'1'})
            selected.append({'pid':p['pid'],'id':pid,'url':p['url'],'officialRating':p['rating'],'state':'new curated problem; two original editorials','newThinking':p['focus'],'miniAnswer':p['answer'],'bugAnswer':p['bugAnswer']})
            added.append((p,svg))
        title=('前缀和与差分：累计量与变化量' if course=='prefix-difference' else '双指针：每次移动都要有依据')
        if not any(r['id']==lid for r in tables['lectures']):
            content={'id':lid,'available':True,'title':'从零讲：'+title,'displayTitle':title,'topic':title,'concept':title,'knowledgeName':topic,'category':'基础算法','categories':['基础算法'],'tags':[topic],'sourceTags':[topic],'catalogTags':[],'sourcePath':source.relative_to(ROOT).as_posix(),'sourceProblemIds':related_ids,'sourceHeading':title,'conceptSource':'independent-foundation','sourceMarkdown':foundation,'markdown':foundation,'sourceHash':digest(foundation),'excerpt':foundation.split('\n\n')[1],'images':{},'editorialVersion':VERSION,'curationVersion':'lectures-v1.1'}
            content['category']=category_path(topic)
            content['categories']=[category_path(topic)]
            tables['lectures'].append({'id':lid,'content':content})
        else:
            row=next(r for r in tables['lectures'] if r['id']==lid)
            if row['content'].get('editorialVersion')==VERSION:
                row['content']['sourcePath']=source.relative_to(ROOT).as_posix()
                row['content']['category']=category_path(topic)
                row['content']['categories']=[category_path(topic)]
    report={'revision':VERSION,'applied':apply,'before':old_counts,'after':{k:len(v) for k,v in tables.items()},'problems':selected,'scope':'Two new courses and their ten curated problems; no claim of completing the separate whole-library editorial review.','sources':['https://codeforces.com/api/problemset.problems']+[p['url'] for ps in data['problems'].values() for p in ps]}
    if apply:
        for name,rows in tables.items():
            source=ROOT/f'data/library/{name}.json';destination=BACKUP/'pre-library'/source.relative_to(ROOT)
            if not destination.exists():destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
            source.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        meta_path=ROOT/'data/library/meta.json';meta=json.loads(meta_path.read_text(encoding='utf-8'))
        if meta.get('sequenceLabRevision')!=VERSION:
            backup=BACKUP/'pre-library/data/library/meta.json'
            if not backup.exists():shutil.copy2(meta_path,backup)
            meta['revision']=str(int(meta.get('revision','0'))+1);meta['sequenceLabRevision']=VERSION
            meta_path.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if meta.get('sequenceLabKnowledgeRevision')!='canonical-categories-v1':
            meta['revision']=str(int(meta.get('revision','0'))+1)
            meta['sequenceLabKnowledgeRevision']='canonical-categories-v1'
            meta_path.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        directory=ROOT/'docs/editorial-figures';directory.mkdir(exist_ok=True)
        for p,svg in added:(directory/f'sequence-{p["pid"]}.svg').write_text(svg,encoding='utf-8')
    (BACKUP/'library-staging.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='problems'},ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');main(parser.parse_args().apply)
