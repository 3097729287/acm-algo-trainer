"""AC occurrence propagation, interval covering and linear-time weighted transitions."""
from nowcoder_editorials import CONTENT, add, read, reviewed_clone
from nowcoder_ac_support import AC


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    put(234273,2000,['AC自动机','fail树'],'统计每个模式串在文本的出现次数，含重复模式。',
        '建立所有模式的Trie并构造fail指针，记录每个模式的终点。扫描文本时沿自动机转移，只给当前状态计数加1。若某模式是当前状态代表串的后缀，它的终点必在当前状态的fail祖先链上。扫描后按BFS序逆序把count[u]加到count[fail[u]]，一次性汇总全部后缀匹配。模式重复时共享终点，分别输出同一个计数。',
        r'''int n; cin >> n; vector<string> pattern(n); size_t total=1; for (auto &s:pattern) { cin >> s; total+=s.size(); } Aho ac(26,'a',total); vector<int> end(n); for (int i=0;i<n;i++) end[i]=ac.insert(pattern[i]); ac.build(); string text; cin >> text; vector<long long> count(ac.node.size()); int u=0; for (char c:text) { u=ac.node[u].next[c-'a']; count[u]++; } for (int i=(int)ac.order.size()-1;i>0;i--) { int v=ac.order[i]; count[ac.node[v].fail]+=count[v]; } for (int v:end) cout << count[v] << '\n';''',
        '不在每个字符处遍历整条fail链，否则重复字符数据可退化平方。出现允许重叠。',
        declarations=AC,complexity=r'模式总长L、文本长N，时间 $O(26L+N)$，空间 $O(26L+N)$。')
    put(233977,2200,['AC自动机','最少区间覆盖'],'用字典单词覆盖目标串，允许匹配部分重叠，最少单词数。',
        'AC自动机每个状态保存自身及fail链上的最长模式长度。扫描目标串，第i位得到的最长匹配区间[i−len+1,i]包含同终点的全部较短匹配，所以只保留它。对每个左端记录最远右端。\n\n之后贪心覆盖：当前已覆盖[0,covered)，把左端≤covered的区间都纳入候选，选择能把右端推得最远的一个。若无法前进就无解。交换论证：任何可行下一块必须与当前覆盖衔接，选最远不会增加之后所需块数。',
        r'''int n; string text; cin >> n >> text; vector<string> pattern(n); size_t total=1; for (auto &s:pattern) { cin >> s; total+=s.size(); } Aho ac(26,'a',total); for (auto &s:pattern) ac.insert(s); ac.build(); vector<int> farthest(text.size(),-1); int u=0; for (int i=0;i<(int)text.size();i++) { u=ac.node[u].next[text[i]-'a']; int length=ac.node[u].longest; if (length) { int start=i-length+1; farthest[start]=max(farthest[start],i+1); } } int covered=0,scan=0,best=0,answer=0; while (covered<(int)text.size()) { while (scan<=(int)covered && scan<(int)text.size()) best=max(best,farthest[scan++]); if (best<=covered) { cout << -1; return 0; } covered=best; answer++; } cout << answer;''',
        '允许重叠，所以不能用只允许首尾相接的分词DP。只使用完整单词的匹配区间，不任意裁剪单词。',
        declarations=AC,complexity=r'时间 $O(26L+N)$，空间 $O(26L+N)$。')
    put(20155,2200,['AC自动机','计数DP','fail树'],'统计长M大写文本中至少出现一个模式的数量。',
        '先数没有任何模式的文本，用26^M减去。AC状态若自身或fail祖先是模式终点则禁用，DP只保留安全状态。朴素逐状态枚举26字符可以正确求解；为兼容M至10000的加强版，下面把每一层转移压到与节点数线性。\n\n设mass[u]为本层DP在fail子树u中的总量，按逆BFS累加得到。先把全部质量乘26放入根作为默认转移。对每条真实Trie边u−c→v，把mass[u]从fallback转移目标移到v：fallback为go(fail[u],c)，根边的fallback为根。对同一个源状态和字符，沿其fail祖先上的这些改道正好依次抵消，只剩最长可用前缀边，所以等价于完整AC转移。最后把所有禁用状态置0。\n\n每层只遍历节点和真实Trie边，既避免漏算重复字母转移，也减少加强版26倍循环。',
        r'''int n,m; cin >> n >> m; vector<string> pattern(n); size_t total=1; for (auto &s:pattern) { cin >> s; total+=s.size(); } Aho ac(26,'A',total); for (auto &s:pattern) ac.insert(s); ac.build(); const int mod=10007; int size=ac.node.size(); vector<int> dp(size),mass(size),next(size); dp[0]=1; int all=1; for (int step=0;step<m;step++) { all=all*26%mod; mass=dp; for (int i=(int)ac.order.size()-1;i>0;i--) { int u=ac.order[i],f=ac.node[u].fail; mass[f]=(mass[f]+mass[u])%mod; } fill(next.begin(),next.end(),0); next[0]=26*mass[0]%mod; for (int v=1;v<size;v++) { int u=ac.node[v].parent,c=ac.node[v].letter,fallback=u?ac.node[ac.node[u].fail].next[c]:0; next[v]=(next[v]+mass[u])%mod; next[fallback]=(next[fallback]-mass[u]+mod)%mod; } for (int u=0;u<size;u++) dp[u]=ac.node[u].longest?0:next[u]; } int safe=0; for (int x:dp) safe=(safe+x)%mod; cout << (all-safe+mod)%mod;''',
        '要把fail链上的模式终点也视为禁用。重定向只遍历原始Trie边，不能把补全的自动机边都当真实边。',
        declarations=AC,complexity=r'模式总长L，时间 $O(26L+ML)$，空间 $O(26L)$。')
    if 'nowcoder-global::234268' not in existing:
        reviewed_clone(234268,20155,'完整核对加强版仅M上界改为10000，字符集、计数模10007与样例相同；沿用每层线性于Trie节点数的优化转移。')
    put(50358,2100,['AC自动机','有向环检测'],'是否存在无限长二进制串避开全部病毒子串。',
        '在AC自动机中去掉所有模式终点及其fail后代代表的禁用状态。无限安全串等价于从根出发的安全转移图能到达一个环：有环即可无限重复其边字符，无限路径在有限状态图中也必重复状态。\n\n先BFS标记根可达的安全状态，再对这部分计算入度并做拓扑删除。若删完所有可达点则无环，否则剩余部分包含环，输出TAK。',
        r'''int n; cin >> n; vector<string> pattern(n); size_t total=1; for (auto &s:pattern) { cin >> s; total+=s.size(); } Aho ac(2,'0',total); for (auto &s:pattern) ac.insert(s); ac.build(); int size=ac.node.size(); vector<bool> reachable(size); vector<int> order={0},indegree(size); reachable[0]=true; for (size_t i=0;i<order.size();i++) for (int c=0;c<2;c++) { int v=ac.node[order[i]].next[c]; if (!ac.node[v].longest && !reachable[v]) { reachable[v]=true; order.push_back(v); } } for (int u:order) for (int c=0;c<2;c++) { int v=ac.node[u].next[c]; if (reachable[v]) indegree[v]++; } queue<int> queue; for (int u:order) if (!indegree[u]) queue.push(u); int removed=0; while (!queue.empty()) { int u=queue.front(); queue.pop(); removed++; for (int c=0;c<2;c++) { int v=ac.node[u].next[c]; if (reachable[v] && --indegree[v]==0) queue.push(v); } } cout << (removed<(int)order.size()?"TAK":"NIE");''',
        '不可达的安全环无用，必须从根筛可达性。两字符可能指向同一状态，入度与删除均按两条边计数。',
        declarations=AC,complexity=r'时间、空间均 $O(L)$，二进制字母表固定为2。')
    put(233969,2300,['AC自动机','树上匹配','反转'],'每位女士姓名为新字母接母亲姓名，批量统计给定姓名前缀。',
        '把姓名和查询都反转：反转姓名是从家族根到该女士的边字母序列，查询前缀变为这条根路径的后缀。将全部反转查询建AC自动机。母亲编号小于女儿，按编号计算state[i]=go(state[parent[i]],c[i])，给该状态计数加1。所有女士处理后按fail逆BFS汇总，查询终点计数即有该反转后缀的根路径数，也就是原问题答案。',
        r'''int n,k; cin >> n >> k; vector<int> parent(n+1); string letter(n+1,'A'); for (int i=1;i<=n;i++) cin >> letter[i] >> parent[i]; vector<string> query(k); size_t total=1; for (auto &s:query) { cin >> s; reverse(s.begin(),s.end()); total+=s.size(); } Aho ac(26,'A',total); vector<int> end(k); for (int i=0;i<k;i++) end[i]=ac.insert(query[i]); ac.build(); vector<int> state(n+1); vector<long long> count(ac.node.size()); for (int i=1;i<=n;i++) { state[i]=ac.node[state[parent[i]]].next[letter[i]-'A']; count[state[i]]++; } for (int i=(int)ac.order.size()-1;i>0;i--) { int u=ac.order[i]; count[ac.node[u].fail]+=count[u]; } for (int u:end) cout << count[u] << '\n';''',
        '不要显式拼接每个完整姓名，链状家族会产生平方总长度。每位女士只贡献其整条根路径的结尾一次。',
        declarations=AC,complexity=r'查询总长L，时间 $O(26L+n+k)$，空间 $O(26L+n+k)$。')


if __name__ == '__main__': run()
