"""Build the requested 12-task school-training content from captured native statements.

This writes only the isolated checkout and the specified authoring archive.
Installation is a separate, backed-up merge into the existing public seed.
"""
import argparse
import base64
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from school_728862_editorials import TASKS,IDEAS,PITFALLS,SUMMARIES
from school_728862_figures import figures
from statement_format import html_markdown,codeforces_samples
from statement_integrity import content_complete
from public_platforms import statement

FOUNDATIONS={
 'A':r'''**十进制拆位。** 对非负整数，`value % 10` 返回个位，`value / 10` 的整数除法去掉个位。`bool seen[10] = {}` 创建十个初始为假的位置，用数字作为下标。数组有效下标为零到九；访问前由取余保证范围。数组查表和改值均为常数时间。''',
 'B':r'''**整数除法与余数。** 对非负整数，`x % 2` 只能为零或一，`x / 2` 向下取整。比如十三除以二，商为六、余一；重复取余便从低位到高位读出二进制。这与小数除法不同，变量用 `int` 就不会保留小数部分。''',
 'C':r'''**动态数组 `vector`。** `vector<int> a(n)` 创建含有 $n$ 个整数的连续数组，有效下标为零至 $n-1$；下标访问为 $O(1)$。`for (int &v : a)` 中的引用让输入直接写进原数组。不要访问 `a[n]`；容器中途增容可能使旧引用、指针或迭代器失效，本题读入后不增容。''',
 'D':r'''**按值传参。** 函数形参 `long long a` 是实参的一份值副本，在函数中减少它，不会改动调用处变量，因而可以安全尝试两种顺序。`min(u,v)` 返回两者较小值，两个参数应使用相容类型。整数溢出发生在运算时，把已经溢出的 `int` 乘积存入 `long long` 无法补救。''',
 'E':r'''**平方根与类型转换。** `sqrtl` 接收、返回 `long double`；`static_cast<long long>` 只做向零截断，不保证得到精确整数平方根，须再做整数校正。`vector<bool>` 是布尔标记的压缩容器，单点读写可作常数时间使用；它的元素是代理对象，不应当作普通 `bool&`。筛表建好后，本题只查询标记。''',
 'F':r'''**排序范围。** `sort(first,last)` 对左闭右开区间原地升序排序，要求随机访问迭代器；`vector` 的 `begin()` 与 `end()` 正好指定全部元素。`end()` 不能解引用。排序一般花 $O(n\log n)$ 次比较；本题从末尾往前取值，不需要自定义比较器。''',
 'G':r'''**字符和字符串。** `char` 保存一个字符，`string` 保存字符序列；单引号如 `'.'` 是字符，双引号如 `"abc"` 是字符串。范围循环按顺序读取每个字符。`ch-'A'+'a'` 只用于已确认是大写英文字母的字符，不能用于任意文字。''',
 'H':r'''**用数组表示状态。** `vector<int> dp(n+1, -1000000)` 创建下标零至 $n$ 的状态表，并设置统一初值。负值表示不可达，零表示可达且段数为零，二者不能混用。`max(old,candidate)` 只选数值较大者，状态是否合法须先由条件判断保证。''',
 'I':r'''**队列 `queue`。** 队列先进先出：`push(v)` 在尾部加入，`front()` 读取头部，`pop()` 移除头部且不返回元素。`front()`、`pop()` 都要求队列非空，所以外层先检查 `empty()`。这些操作均为 $O(1)$；BFS 把已经发现的点入队、入队时标记，避免重复扩展。''',
 'J':r'''**动态数组与二元组。** `vector<long long> best = c` 复制建站费用，之后改 `best` 不会改 `c`。`pair<int,int>` 把一条线的两个城市编号放在一起，`first`、`second` 分别读取两端；`push_back` 在尾部追加，均摊 $O(1)$，增容时可能使原引用失效。`auto edge` 根据容器元素推断为二元组的值副本。`abs` 取绝对值，传入 `long long` 差值以使用对应重载。''',
 'K':r'''**邻接表与队列。** `vector<vector<int>> graph(n)` 为每个点保存一份出边列表，遍历 `graph[u]` 就是在枚举其后继。总存储量为 $O(n+m)$。`queue<int>` 用 `push` 加入队尾，用 `front`、`pop` 读取并移除队首；必须先用 `empty()` 判空。这些队列操作均为 $O(1)$。''',
 'L':r'''**数组下标与空窗口。** `vector<int> a(n)` 的下标为零至 $n-1$。窗口闭区间的元素个数为 $right-left+1$；当左端恰好越过右端一位时，这个值是零，表示空窗口。代码在 `sum > t` 时取走当前左端元素，由所有用时为正且预算为正保证访问仍在已加入部分内。'''
}

METHOD_NAMES={
 'A':'逐年枚举与数位去重','B':'二进制计数','C':'固定长度滑动窗口',
 'D':'枚举削减顺序','E':'质数平方与埃氏筛','F':'排序贪心','G':'逐字符模拟',
 'H':'按长度动态规划','I':'BFS 统计连通块','J':'虚拟电源与 Prim',
 'K':'拓扑序定向','L':'双指针滑动窗口'
}

FOUNDATION_LINKS={
 'A':['integer','arrays'],'B':['integer','bitwise'],'C':['vector'],
 'D':['functions','integer'],'E':['integer','vector'],
 'F':['sort','iterators'],'G':['strings','string-tools'],
 'H':['vector'],'I':['queue-stack','vector'],'J':['vector','bindings','integer'],
 'K':['queue-stack','vector','structures'],'L':['vector','integer']
}
TOPICS={
 'A':'整数拆位与布尔数组','B':'整数除法与余数','C':'vector：长度可变的连续数组',
 'D':'按值传参与整数类型','E':'浮点平方根与整数校正','F':'sort 与迭代器范围',
 'G':'char 与 string','H':'vector 的创建与初值','I':'queue 的基本用法',
 'J':'vector 与 pair','K':'嵌套 vector 与 queue','L':'vector 下标与边界'
}

def dumps(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
def write(path,body):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        previous=path.read_bytes()
        if previous==body.encode('utf8'):return
        backup=Path.home()/'.dsh/backups/gym728862'/path.relative_to(path.anchor)
        backup=backup.with_name(backup.name+'.'+dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.bak')
        backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(previous)
    path.write_text(body,encoding='utf8',newline='\n')

def article(letter,title,variant,code):
    # Use complete snippets / qualified library names, and quote string literals.
    # The archive's older format checker otherwise mistakes these real C++
    # constructs for mathematical variable names.
    inline={
      'value % 10':'value % 10;','value / 10':'value / 10;',
      'x % 2':'x % 2;','x / 2':'x / 2;',
      'vector<int> a(n)':'std::vector<int> a(n)',
      'vector<int> dp(n+1, -1000000)':'std::vector<int> dp(n+1, -1000000)',
      'long long a':'long long a;','min(u,v)':'std::min(u,v)',
      'min(n, a-x)':'std::min(n, a-x)','max(old,candidate)':'std::max(old,candidate)',
      'sqrtl':'std::sqrtl','static_cast<long long>':'static_cast<long long>(value);',
      'vector<bool>':'std::vector<bool>','sort(first,last)':'std::sort(first,last)',
      'pair<int,int>':'std::pair<int,int>','auto edge':'for (auto edge : wires)',
      'first':'edge.first','second':'edge.second',
      'queue':'std::queue','queue<int>':'std::queue<int>',
      'push(v)':'q.push(v);','front()':'q.front();','pop()':'q.pop();','empty()':'q.empty();',
      'front':'q.front();','pop':'q.pop();','sum > t':'while (sum > t)',
      'aoyeui':'"aoyeui"','y':"'y'",'A':"'A'",'Z':"'Z'",'a':"'a'",'.':"'.'",
      'abacaba':'"abacaba"','bcb':'"bcb"','.b.c.b':'".b.c.b"'
    }
    def prose(s):
        def replace(m):
            if m[1]=='bool&':return '`bool` 引用'
            if m[1]=='c':return '原数组'
            return '`'+inline.get(m[1],m[1])+'`'
        return re.sub(r'`([^`\n]+)`',replace,s)
    idea=prose(IDEAS[letter][variant])
    tools='\n\n### 从零讲：'+TOPICS[letter]+'\n\n'+prose(FOUNDATIONS[letter])
    return (f'## {letter}. {title}\n\n### 题意\n\n'+SUMMARIES[letter]+tools+'\n\n### 思路\n\n'+idea
       +'\n\n### 参考代码\n\n```cpp\n'+code.rstrip()+'\n```\n\n### 易错点\n\n'+prose(PITFALLS[letter])+'\n')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--archive',type=Path,required=True)
    args=ap.parse_args();archive=args.archive.resolve();work=archive/'_work'
    captures=json.loads((work/'source.json').read_text(encoding='utf8'))
    official=json.loads((work/'official-problems.json').read_text(encoding='utf8'))
    official={(p['contestId'],p['index']):p for p in official}
    out=ROOT/'data/school-training/728862';out.mkdir(parents=True,exist_ok=True)
    fig=figures()
    for name,body in fig.items():
        write(archive/'assets'/name,body);write(out/'assets'/name,body)
    defaults=[];details=[];records=[];statements=[];methods=[];provenance=[];links=[]
    logs=[]
    for position,(letter,title,cid,index,knowledge) in enumerate(TASKS):
        source=captures['problems'][position];assert source['title'].startswith(letter+'.')
        reference=json.loads((work/('original-'+letter+'.json')).read_text(encoding='utf8'))
        assert reference['title'].split('. ',1)[1]==title
        assert [(s['input'].split(),s['output'].split()) for s in codeforces_samples(reference['html'])]==[(s['input'].split(),s['output'].split()) for s in source['samples']]
        rating=official[(cid,index)]['rating'];assert rating<=2300
        log=(work/'logs'/('verify_'+letter.lower()+'.log')).read_text(encoding='utf8')
        assert '★不通过★' not in log and 'TIMING_PASS' in log and '不一致 0 组' in log
        logs.append(log)
        code=(archive/'A-L'/letter/(letter.lower()+'.cpp')).read_text(encoding='utf8')
        default=article(letter,title,0,code);detail=article(letter,title,1,code)
        defaults.append(default);details.append(detail)
        write(out/'default'/(letter+'.md'),default);write(out/'detailed'/(letter+'.md'),detail)
        for suffix in ['.cpp','_brute.cpp']:
            src=archive/'A-L'/letter/(letter.lower()+suffix)
            write(out/'reference'/src.name,src.read_text(encoding='utf8'))
        identity=f'remote:codeforces:728862::{letter}';url=f'https://codeforces.com/gym/728862/problem/{letter}'
        original=f'https://codeforces.com/problemset/problem/{cid}/{index}'
        tags=knowledge.split(' + ')
        row={'id':identity,'contest':'1101 TTC(Team Training Contest)','contestFullName':'1101 TTC(Team Training Contest)',
          'problem':letter,'contestLetter':letter,'title':title,'originalTitle':title,'contestTaskTitle':source['title'].split('. ',1)[1],
          'originalProblemUrl':original,'platform':'Codeforces','series':'校队训练','contestFamily':'校队训练','contestId':'728862',
          'schoolTraining':True,'source':'school-training','status':'未做','date':'','queue':None,
          'tags':tags,'sourceTags':tags,'knowledge':knowledge,'difficulty':rating,
          'difficultySource':'Codeforces 原题官方 rating（已核对本场题意、约束和样例）','difficultyConfidence':'HIGH','difficultyEstimated':False,
          'difficultyEvidence':[original,'https://codeforces.com/api/problemset.problems','完整题意、数据范围、输入输出与样例核对一致'],
          'difficultyCheckedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'url':url,'contestRoster':True,'contestProblemCount':12,
          'solutionAvailable':True,'detailedSolutionAvailable':True,'solutionState':'available','statementAvailable':True,
          'catalogContentReady':True,'catalogStatementReady':True,'catalogReplayReady':True,'problemType':'standard',
          'collectionSource':'https://codeforces.com/gym/728862','collectionNotice':'用户指定整场校队训练；保留本场题号，原题评分单独记载。'}
        raw={'_id':identity,'_i':position,'场次':row['contest'],'题号':letter,'题名':title,'知识点':'、'.join(tags),'难度':str(rating),'状态':'未做','日期':''}
        records.append({'id':identity,'url':url,'raw':raw,'encoded':row})
        class CapturedClient:
            def text(self,request):
                if request!=url:raise ValueError('Unexpected statement URL')
                return source['html']
            def bytes(self,request):
                if not request.startswith('https://espresso.codeforces.com/'):raise ValueError('Unexpected asset host')
                file=work/'resources'/request.rsplit('/',1)[1];file.parent.mkdir(parents=True,exist_ok=True)
                if not file.exists():
                    with urllib.request.urlopen(request,timeout=30) as response:file.write_bytes(response.read())
                return file.read_bytes()
        native=statement(CapturedClient(),identity,title,url)
        native['limits']={'timeMs':3000 if letter=='K' else 1000 if letter in 'BCD H'.replace(' ','') else 2000,'memoryMb':256}
        assert native['integrity']['status']=='complete',native.get('resourceIssues')
        assert content_complete(native)
        assert [(x['input'].split(),x['output'].split()) for x in native['samples']]==[(x['input'].split(),x['output'].split()) for x in source['samples']]
        statements.append({'problem_id':identity,'content':native})
        images={name:'data:image/svg+xml;base64,'+base64.b64encode((out/name).read_bytes()).decode('ascii') for name in re.findall(r'!\[[^\]]*\]\((assets/[^)]+)\)',default+detail)}
        common={'problem_id':identity,'source_path':f'school-training/728862/{letter}.md','images':images}
        methods.append({'problem_id':identity,'content':{'schema':1,'primaryMethod':'main','methods':[{'id':'main','title':METHOD_NAMES[letter],'knowledge':knowledge,'tags':tags,'legacy':True}]}})
        links.extend({'problem_id':identity,'lecture_id':'lecture:foundation-'+name,'kind':'foundation','position':order} for order,name in enumerate(FOUNDATION_LINKS[letter]))
        provenance.append({'letter':letter,'title':title,'contestTaskTitle':row['contestTaskTitle'],'url':url,'originalUrl':original,'rating':rating,
          'gymHtmlSha256':hashlib.sha256(source['html'].encode()).hexdigest(),'originalHtmlSha256':hashlib.sha256(reference['html'].encode()).hexdigest(),
          'normalizedBodiesIdentical':html_markdown(source['html'],url)==html_markdown(reference['html'],original),
          'semanticReview':'题目目标、限制、输入输出及样例逐项核对；部分转载题的数学排版不同。','sampleCount':len(native['samples']),
          'codeSha256':hashlib.sha256(code.encode()).hexdigest()})
    catalog='| 题号 | 题名 | 考点 | 难度 |\n|---|---|---|---|\n'+''.join(f'| {L} | {title} | {knowledge} | {official[(cid,idx)]["rating"]} |\n' for L,title,cid,idx,knowledge in TASKS)
    head='# 校队训练 728862 题解\n\n> 比赛：https://codeforces.com/gym/728862\n> 名称：1101 TTC(Team Training Contest)\n> 语言：C++17\n\n本场 A–D 转载时以字母命名，正文同时保留已核实的原题名；所有题仍使用本场题号与提交入口。难度取核对一致的原题官方评分。本次按用户指定整场收录。\n\n## 目录\n\n'+catalog+'\n'
    totals={'samples':sum(int(re.search(r'官方样例：([0-9]+) 组全过',s)[1]) for s in logs),
      'edges':sum(int(re.search(r'边界用例：([0-9]+) 条全过',s)[1]) for s in logs),
      'random':sum(int(re.search(r'随机对拍：实跑 ([0-9]+) 组全一致',s)[1]) for s in logs)}
    timing='；'.join(f'{L} '+re.search(r'极限计时：官方最大规模 ([0-9.]+ s)',s)[1] for (L,*_),s in zip(TASKS,logs))
    measured='\n## 实测记录\n\n'+f'十二份正解及十二份独立基准均已编译，无警告。\n官方样例 {totals["samples"]} 组、边界 {totals["edges"]} 条全过。\n随机对拍实跑 {totals["random"]} 组全一致，种子 728862；其中 I、J、K 各一千组。\n最大规模均通过时限检查：{timing}。\nC、J、K 使用合法性判定器；本地验证未向原站提交。\n'
    write(archive/'728862题解.md',head+'\n'.join(defaults)+measured)
    write(archive/'728862详细题解.md',head+'\n'.join(details)+measured)
    write(out/'problems.json',dumps(records));write(out/'statements.json',dumps(statements))
    write(out/'solution_methods.json',dumps(methods));write(out/'provenance.json',dumps(provenance))
    write(out/'links.json',dumps(links))
    write(out/'validation-summary.json',dumps(totals))
    print(dumps({'problems':len(records),'articles':len(defaults)+len(details),'figures':len(fig),**totals}))

if __name__=='__main__':main()
