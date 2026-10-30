"""Generate reviewed template explanations and their shared Algorithm Lab source.

This changes presentation placement; original SQLite lecture identities, images,
problem links and learned markers are preserved for existing editorials/imports.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / 'backend/resources'

TOPICS = [
    dict(id='dsu', title='并查集', category='数据结构', lectures=[
        'lecture:foundation-dsu'],
        intro='有 n 个对象，开始互不相连。每次把两组接起来，或询问两个对象是否已在同一组；不需要保存组内每一条连接边。',
        invariant='parent 是父指针，根结点指向自己。size 只在根处有意义；合并两个不同根才减少集合数。路径压缩改的是指针长度，不是集合归属。',
        operations=[['find(v)','找到对象 v 所属集合的根；根编号只是代表元，不保证是最小编号。'],['same(a,b)','比较两个根，判断是否同组。'],['unite(a,b)','只连接不同根；重复合并返回 false，不能再累加集合大小。'],['component_size(v)','先找根，再读整组大小。']],
        boundary='编号从 0 开始。路径压缩与按大小合并的均摊复杂度为 O(α(n))，空间 O(n)。普通并查集不能直接删除一条边；撤销需要另一种实现。',
        values=[0,1,2,3,4], scripts=[['unite',0,1],['unite',1,2],['same',0,2],['unite',0,2],['size',1]],
        bug='合并 0 与 1 后，再合并 1 与 0。若每次都累加大小，两个对象会被错误计成四个。'),
    dict(id='fenwick', title='树状数组', category='数据结构', lectures=[
        'lecture:foundation-fenwick','lecture:58d9d668d41f6312aaf37a12','lecture:ff9fbee9ff36049ce6222ad3',
        'lecture:36ec25cec109737102d5956e','lecture:bccb082a95e36319b45ec067'],
        intro='数组会发生单点增量修改，又要反复询问一段的总和。静态前缀和每改一次就可能重算整段，树状数组只改包含该点的若干块。',
        invariant='外部下标从 0 开始，内部 tree 从 1 开始。tree[i] 保存内部 [i-lowbit(i)+1,i] 的和；更新先把外部下标加 1，再沿 i+=lowbit(i) 找更大覆盖块，查询沿 i-=lowbit(i) 拆出互不重叠的块。',
        operations=[['add(i,delta)','给外部下标 i 的一项加增量，不是赋值；合法范围 [0,n)。'],['prefix_sum(end)','求 [0,end) 的和；prefix_sum(0)=0 是空前缀。'],['range_sum(l,r)','左闭右开 [l,r) 的和等于 prefix_sum(r)-prefix_sum(l)。'],['kth(k)','当原数组每项非负时，找从 1 开始的第 k 个频次所在的外部位置；k 无效或超总数返回 n。']],
        boundary='更新与前缀查询 O(log n)，空间 O(n)。外部 add(0,d) 合法，代码先将下标转换为内部 1；不能省去这次转换。区间和用 long long；第 k 小必须满足非负频次前提。',
        values=[2,1,3,0,4], scripts=[['prefix',3],['add',1,5],['sum',1,4],['add',4,-2],['prefix',5]],
        bug='数组 [2,1]，第二项加 3 后应为 [2,4]。把 add(1,3) 当作赋值会误算总和为 5，正确总和是 6。'),
    dict(id='segment-tree', title='懒标记线段树', category='数据结构', lectures=[
        'lecture:foundation-segment-tree','lecture:236c076c7e0f8cd291adb348'],
        intro='既要给整个区间加一个数，又要查询区间总和。每次逐项修改太慢，需要把一整块的变化先记在代表这一块的结点上。',
        invariant='sum 是结点区间的当前总和，lazy 是已经计入这个总和、但尚未传给孩子的增量。覆盖长度 len 的区间加 d，必须使 sum 增加 d*len。',
        operations=[['RangeAddSum(a)','由原数组建立每个区间的总和。'],['add(l,r,delta)','更新左闭右开区间 [l,r)；完全覆盖时更新 sum 和 lazy。'],['range_sum(l,r)','把相交部分的总和合并；只访问一部分时先下传标记，空区间返回 0。'],['push / pull','下传让孩子得到尚欠的增量；回收用两个孩子的和重建父结点。']],
        boundary='实验和代码都用外部 0 开始、左闭右开区间。区间加和区间和每次 O(log n)，空间 O(n)。区间赋值不能直接复用“累加”标记。',
        values=[2,1,3,0,4], scripts=[['addRange',1,4,3],['sum',0,5],['sum',2,3],['addRange',0,3,-2],['sum',1,4]],
        bug='[0,0,0] 整段加 2，总和要加 2×3=6。只让根的 sum 加 2，连整段查询也会立刻出错。'),
    dict(id='trie', title='字典树', category='字符串', lectures=[
        'lecture:foundation-trie','lecture:7734277051034f49ca3ee1e6'],
        intro='维护一组会重复的单词，支持插入、整词计数、前缀计数和删除一次。共享前缀的单词沿同一段路径走，到单词结束时再记结束计数。',
        invariant='pass 表示经过结点的单词份数，end 表示在该结点结束的份数。“有这个前缀”与“有这个完整单词”是不同问题。删除前必须确认整词存在。',
        operations=[['insert(word)','沿字符走，按需建结点并增加路径计数；重复单词增加份数。'],['count(word)','读结束计数，只算完整单词。'],['prefix_count(prefix)','读前缀路径的经过计数。'],['erase(word)','只删除一份已有单词，不能把不存在单词的计数减成负数。']],
        boundary='模板字符集为小写 a-z，各操作 O(字符串长度)，空间与建过的字符路径数相关。空串、重复词和删除约定见代码示例；不同字符集需更换分支表示。',
        values=['ab','abc','ab'], scripts=[['insert','ab'],['insert','abc'],['insert','ab'],['count','ab'],['prefix','ab'],['erase','ab'],['count','ab']],
        bug='仅插入 abc 后，ab 的前缀计数是 1，但完整单词 ab 的计数是 0。不能用 pass 代替 end。'),
    dict(id='binary-lifting', title='倍增', category='数据结构', lectures=[
        'lecture:foundation-binary-lifting','lecture:5d088249ba6e27a509fe4c90','lecture:7990d92643ad917708eb9306'],
        intro='每个位置都有唯一后继，要多次询问从 v 连续走 k 步后在哪里。逐步走要 O(k)，把 k 拆成二进制，就能拼接少量预处理好的跳跃。',
        invariant='up[v][j] 表示从 v 出发走 2^j 步的终点。先走 2^(j-1) 步到 mid，再从 mid 走同样多的步数；不是直接把编号加上步长。',
        operations=[['BinaryLifting(next)','预处理每个位置的 1、2、4、8…步后继。'],['jump(v,k)','按 k 的置位逐段跳；k=0 返回 v 自己。'],['树上祖先','根的后继可以设为自己；超过树深后仍停在根。LCA 还需要深度和共同祖先逻辑，使用独立 LCA 模板。']],
        boundary='编号 [0,n)，next 必须都在范围内；支持函数图、自环和 uint64_t 步数。预处理 O(64n)，查询 O(64)，空间 O(64n)。不对第 64 位做移位。',
        values=[1,2,3,4,2], scripts=[['jump',0,0],['jump',0,1],['jump',0,2],['jump',0,7],['jump',4,8]],
        bug='后继 [1,2,0] 形成三元环。从 0 走 4 步应到 1；用 (v+k)%n 只在特别编号的环上碰巧正确，一般函数图不成立。'),
    dict(id='dinic', title='最大流与最小割', category='图论', lectures=[
        'lecture:foundation-max-flow'],
        intro='有向边有容量上限。流从源点出发到汇点，中间点流入等于流出；要让总流量尽量大。一次选路可能挡住后续选择，必须允许撤回旧流。',
        invariant='残量正向边表示还能增加多少流，反向边表示能撤回多少旧流。Dinic 先按正残量边 BFS 分层，再只沿下一层增广；不能把反向边删掉。',
        operations=[['add_edge(u,v,cap)','加入有向容量边及初始为 0 的反向残量边。'],['max_flow(s,t)','不断分层、增广，返回本次新增流量；第二次调用在已有残量上继续。'],['source_side(s)','完整最大流结束后，正残量还能到达的点是一个最小割的源侧。']],
        boundary='顶点 [0,n)，容量非负且总流量须在 long long 范围内。支持平行边、自环。一般复杂度 O(V²E)，空间 O(V+E)；用显式路径避免深图递归。最小割结论需要完整最大流。',
        values=[[0,1,3],[0,2,2],[1,2,1],[1,3,2],[2,3,3]], scripts=[['flow',0,3]],
        bug='先选择的路径不必属于最终答案。增广时若只减正向容量而不增加反向容量，就无法取消已经不合适的旧分配。'),
    dict(id='li-chao', title='Li Chao 树', category='数据结构', lectures=[
        'lecture:foundation-li-chao'],
        intro='不断加入直线 y=kx+b，又要在指定横坐标上询问所有已加入直线的最小值。不同直线在不同位置可能更优，不能只保留全局斜率最小的一条。',
        invariant='一个结点保存其横坐标中点处更优的线。两条直线至多相交一次；中点落败的线至多在一侧重新胜出，把它递归送往那一侧即可。',
        operations=[['LiChao(coordinates)','先登记全部会查询的横坐标，排序去重后构建离散域。'],['add({k,b})','加入整条直线，按中点比较决定留下谁、向哪一侧递归。'],['query(x)','沿 x 所属路径比较各结点的候选；尚无直线或 x 未登记时返回空值。']],
        boundary='插入和查询 O(log m)，m 为不同查询坐标个数，空间 O(m)。系数和坐标是 long long，求值用 __int128 避免乘法溢出；当前模板处理整条直线，线段插入需另写覆盖逻辑。',
        values=[0,1,2,3,4], scripts=[['line',2,1],['query',1],['line',-1,7],['query',1],['query',4],['line',0,2],['query',3]],
        bug='y=2x+1 与 y=-x+7 在 x=0 时前者更小，在 x=4 时后者更小。只比较左端点并永久丢掉另一条，会漏掉右侧答案。'),
    dict(id='linear-basis', title='线性基', category='数学', lectures=[],
        intro='给出若干非负整数，每个下标选或不选一次，求子集异或能得到什么。以 [6,5,3] 为例，6 XOR 5=3；第三个数并没有带来新的结果。',
        invariant='p[i] 的最高 1 位固定为 i。插入 x 时从最高位往下看：已有主元就异或消掉这一位；遇到空主元就保存剩余数；消成 0 表示它已能由已有数表示。替换只改变生成方式，不改变全部可表示的异或值。',
        operations=[['insert(x)','加入一个数；返回是否增加独立方向，插入 0 或重复信息不会增加 rank。'],['contains(x)','沿同样的主元消元，最终为 0 才可表示。'],['max_xor(seed) / min_xor(seed)','从高位向低位尝试改善答案；更低主元不再改变已经决定的高位。seed 默认是 0，允许空子集。'],['merge(other)','把另一份基的主元插入当前基；这是生成空间的合并，不是支持删除的集合。'],['kth(k)','不同异或结果排序后第 k 个，从 0 开始，包含 0。先清除其它主元位，才能把编号的二进制对应到排序。'],['min_nonzero()','返回最小非零可表示值；只有 0 可表示时返回空值。']],
        boundary='全程 uint64_t，覆盖第 63 位；插入/表示性/最值 O(64)，合并/第 k 小 O(64²)，空间 O(64)。rank=r 时有 2^r 个不同结果；原输入 n 项时每个可达结果有 2^(n-r) 组下标方案。非空异或为 0 当且仅当 n>r。不能把“不同结果数”当作“方案数”。',
        values=['6','5','3'], scripts=[],
        bug='只把原数从大到小各尝试一次不成立。[12,10,9] 会先取 12 并拒绝 10、9，得到 12；真正最大值是 12 XOR 10 XOR 9=15。先消元后再贪心。'),
]

EXAMPLES = {
    'linear-basis': '''int main() {
    XorBasis b;
    assert(b.insert(6) && b.insert(5) && !b.insert(3));
    assert(b.rank == 2 && b.contains(3) && !b.contains(1));
    assert(b.max_xor() == 6 && b.min_xor() == 0);
    assert(b.min_xor(7) == 1 && b.max_xor(7) == 7);
    assert(b.kth(0) == 0 && b.kth(1) == 3 && b.kth(3) == 6 && !b.kth(4));
    assert(b.min_nonzero() == 3);
    XorBasis extra; extra.insert(1); b.merge(extra);
    assert(b.rank == 3 && b.max_xor() == 7);
    XorBasis full; for (int i=0;i<64;++i) full.insert(uint64_t(1)<<i);
    assert(full.kth(UINT64_MAX) == UINT64_MAX);
}''',
    'binary-lifting': '''int main() {
    BinaryLifting jump({1,2,3,4,2});
    assert(jump.jump(0,0) == 0 && jump.jump(0,7) == 4);
    BinaryLifting loop({0}); assert(loop.jump(0,UINT64_MAX) == 0);
}''',
    'dinic': '''int main() {
    Dinic f(4);
    f.add_edge(0,1,3); f.add_edge(0,2,2); f.add_edge(1,2,1);
    f.add_edge(1,3,2); f.add_edge(2,3,3); f.add_edge(0,0,9);
    assert(f.max_flow(0,3) == 5 && f.max_flow(0,3) == 0);
    auto cut=f.source_side(0); assert(cut[0] && !cut[3]);
}''',
    'li-chao': '''int main() {
    LiChao tree({0,1,2,3,4}); assert(!tree.query(1));
    tree.add({2,1}); tree.add({-1,7});
    assert(tree.query(0) == 1 && tree.query(4) == 3);
    tree.add({0,2}); assert(tree.query(3) == 2 && !tree.query(5));
    LiChao empty({}); empty.add({1,2}); assert(!empty.query(0));
}''',
}

REASONING = {
 'dsu': '查根时沿父指针走到 parent[root]=root。把途中结点直接指向同一个根，没有改变“最终到哪个根”，所以没有改变集合。合并前先查两个根，根相同就已经连通；只有两个不同根相连，集合数才减少一。按大小把小集合挂到大集合，每次被挂接的结点所在集合至少翻倍，避免反复接出长链；再配合路径压缩得到均摊界。',
 'fenwick': '例如内部 tree[4] 保存外部 [0,4)，tree[6] 保存 [4,6)。查询前 6 项时先读 tree[6]，再令 6-lowbit(6)=4 读 tree[4]，两块恰好覆盖 [0,6)，既不重叠也不遗漏。外部位置 1 加 5 时先转到内部 2，再访问 2、4 等包含它的块。查询向左拆块与修改向上找覆盖块，是两个相反用途的循环。',
 'segment-tree': '以 [2,1,3,0,4] 为例，给 [1,4) 加 3 后成为 [2,4,6,3,4]，总和从 10 变成 19。完全覆盖的结点可以先只更新自己；此时孩子的 sum 仍可能是旧值。若随后只查这段的一部分，必须先把父亲 lazy 下传，并在父亲清零，才能读到正确孩子。一个 lazy=3 表示每项尚欠 3，不是整个区间尚欠总共 3。',
 'trie': '依次插入 ab、ab、abc：路径 ab 的 passing=3、ending=2，路径 abc 的 passing=1、ending=1。删去一份 ab 时，根、a、ab 的 passing 都减一，ab 的 ending 减一；abc 的计数保持不变。只插入 abc 时虽然路径 ab 存在，ending 仍为 0，所以不能删除 ab。树上保存的是字符前缀，词库计数另由这两个量区分。',
 'binary-lifting': '从 0 走 7 步不是把编号加 7，而是沿后继执行七次。把 7 写成 4+2+1：先用 up[0][2] 得到四步终点，再从这个新终点查两步后继，最后走一步。预处理 up[v][j] 必须先完成所有点的第 j-1 列，两个半段才都有定义。函数图可以进入环，但每一步仍有唯一后继，因此同一个拼接公式仍成立。',
 'dinic': '容量边 u→v 上送过 f 单位流后，还能正向增加 cap-f，并能沿反向 v→u 撤回 f；反向残量不是一条新建的原容量。增广路径的最小正残量是这次可增加的流量。Dinic 的 BFS 记录到源的最少残量边数，随后只沿层数加一的边找阻塞流，避免反复绕圈。再无增广路时，残量可达源侧的所有出边都饱和，当前流量等于这个割的容量。',
 'li-chao': '例如 y=2x+1 与 y=-x+7：在 x=0 时分别为 1、7，在 x=4 时分别为 9、3。它们的差仍是一条直线，至多变号一次。插入时让中点更优的线留下；另一条若在左端与中点的胜负不同，就只可能在左半边再有用，否则只需考察右半边。查询沿横坐标的树路径取最小值，因为每次被下放的候选只可能在该分支获胜。',
 'linear-basis': '''先看二进制，并把最高位对齐：

| 当前原数 | 二进制 | 处理 |
| --- | --- | --- |
| 6 | 110 | 第 2 位还没有主元，保存 p[2]=6 |
| 5 | 101 | 与 110 异或得到 011，保存 p[1]=3 |
| 3 | 011 | 与 p[1] 异或得到 000，不新增方向 |

为什么消元不丢信息？设已有主元为 b，把新数 x 换成 x XOR b。新数能由 x 与 b 产生，原数也能由新数与 b 还原，因此两组能产生的全部异或值完全相同。消成 0 时，这个方向已经包含在旧集合里。

为什么这些主元彼此独立？任选非空的一组主元，看其中最高的主元位。只有这一行在该位为 1，其它行的最高位更低，无法抵消它。因此非空主元组合不可能为 0；这也解释了从高位开始的查询为什么不会被低位破坏。''',
}


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def main():
    lectures = {x['id']: x['content'] for x in json.loads((ROOT/'data/library/lectures.json').read_text(encoding='utf8'))}
    path = RESOURCES/'code-templates.json'
    document = json.loads(path.read_text(encoding='utf8'))
    templates = {x['id'].removeprefix('builtin:'): x for x in document['templates']}
    preservation=ROOT/'data/algorithm-template-preservation.json'
    if not preservation.exists():
        entries=[]
        for key,template in templates.items():
            if key in EXAMPLES:continue
            fields={}
            for name in ['code','contestCode','example','contestExample','practiceIds']:
                value=template.get(name)
                text=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,separators=(',',':'))
                fields[name]=hashlib.sha256(text.encode()).hexdigest()
            entries.append(dict(id=template['id'],fields=fields))
        write_json(preservation,dict(sourceCommit='83079d8b1c9aee211bba6daa6304a329f5d44332',templates=entries))
    audit = []
    for topic in TOPICS:
        key = topic['id']
        if key in EXAMPLES:
            code = (RESOURCES/'algorithm-templates'/f'{key}.cpp').read_text(encoding='utf8')
            contest = '\n'.join(line for line in code.splitlines() if not line.strip().startswith('//'))+'\n'
            templates[key] = dict(id='builtin:'+key, title=topic['title'], category=topic['category'],
                                  summary=topic['intro'], language='cpp17', builtin=True, tags=[topic['title']],
                                  code=code, contestCode=contest, example=EXAMPLES[key], contestExample=EXAMPLES[key],
                                  notes=topic['boundary'], contestNotes=topic['boundary'], practiceIds=[])
        template = templates[key]
        topic['templateId'] = template['id']
        topic['practiceIds'] = template.get('practiceIds', [])
        template['explanation'] = '\n\n'.join([
            '## '+topic['title'], topic['intro'], topic['invariant'],
            '| 操作 | 含义与前提 |\n| --- | --- |\n'+'\n'.join('| `'+name+'` | '+meaning+' |' for name,meaning in topic['operations']),
            topic['boundary'], '### 用一个小例排错', topic['bug']])
        template['learningPath'] = key
        topic['reasoning'] = REASONING[key]
        template['explanation'] += '\n\n### 为什么这些操作成立\n\n'+topic['reasoning']
        topic['sections'] = []
        for identity in topic['lectures']:
            lecture = lectures[identity]
            section = dict(id=identity, title=lecture.get('concept') or lecture['title'],
                           markdown=lecture['markdown'], images=lecture.get('images', {}),
                           sourceProblemIds=lecture.get('sourceProblemIds', []))
            topic['sections'].append(section)
            audit.append(dict(lectureId=identity, title=section['title'], templateId=template['id'],
                              courseId=key, markdownSha256=hashlib.sha256(lecture['markdown'].encode()).hexdigest()))
    document['templates'] = list(templates.values())
    write_json(path, document)
    write_json(RESOURCES/'algorithm-learning.json', dict(revision=1, topics=TOPICS))
    out=ROOT/'.backups/algorithm-learning-20261030';out.mkdir(parents=True,exist_ok=True)
    write_json(out/'placement-audit.json', dict(lecturesInspected=len(lectures), movedLectures=len(audit),
               topics=len(TOPICS), templates=len(templates), preservedLectureRecords=True, entries=audit))
    print(json.dumps(dict(lecturesInspected=len(lectures), movedLectures=len(audit), topics=len(TOPICS), templates=len(templates))))


if __name__ == '__main__':
    main()
