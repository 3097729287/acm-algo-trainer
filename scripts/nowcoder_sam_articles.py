"""Suffix automata, suffix-array output and palindromic trees."""
from nowcoder_editorials import CONTENT, add, read
from nowcoder_sam_support import SAM, SAM_EXPLANATION
from nowcoder_suffix_support import SUFFIX_ARRAY, EXPLANATION


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    put(237303,1900,['后缀数组','LCP'],'多组输出后缀字典序排名的起点和相邻LCP。',
        EXPLANATION+'\n\n字符编码为1..26，调用后输出sa+1转换成原题一基位置，height首项已置0。倍增每轮只按已有排名做计数排序，不调用比较排序处理整条后缀。',
        r'''int tests; cin >> tests; while (tests--) { string s; cin >> s; vector<int> data; for (char c:s) data.push_back(c-'a'+1); SuffixArray index(data); for (int i=0;i<(int)s.size();i++) cout << index.sa[i]+1 << (i+1==(int)s.size()?'\n':' '); for (int i=0;i<(int)s.size();i++) cout << index.height[i] << (i+1==(int)s.size()?'\n':' '); }''',
        '后缀排名从1输出，代码内部从0开始；height[0]=0，不与最后后缀循环比较。',
        declarations=SUFFIX_ARRAY,complexity=r'每组时间 $O(n\log n)$，空间 $O(n)$。')
    put(237304,2000,['后缀自动机','不同子串'],'统计本质不同的非空子串数。',
        SAM_EXPLANATION+'\n\n每个状态u贡献len[u]−len[link[u]]种不同子串，各状态之间结束位置集合不同，不会重复。累加所有非根状态即可。次数不影响本题答案，但模板仍包含正确的次数传播，便于理解同一类状态的用途。',
        r'''string s; cin >> s; SuffixAutomaton sam(s); long long answer=0; for (int u=1;u<(int)sam.node.size();u++) answer+=sam.node[u].length-sam.node[sam.node[u].link].length; cout << answer;''',
        '子串非空，根不贡献。不同位置出现的相同字符串只计算一次。',
        declarations=SAM,complexity=r'固定字母表时间 $O(n)$，空间 $O(26n)$。')
    put(237650,2100,['后缀自动机','出现次数'],'重复子串的长度乘出现次数最大值。',
        SAM_EXPLANATION+'\n\n同一状态内出现次数固定，长度越大乘积越大，所以只检查该状态最长代表串len[u]。当count[u]>1时用1LL*len[u]*count[u]更新答案；所有仅出现一次的状态跳过。',
        r'''string s; cin >> s; SuffixAutomaton sam(s); long long answer=0; for (auto &u:sam.node) if (u.count>1) answer=max(answer,1LL*u.length*u.count); cout << answer;''',
        '克隆状态初始次数是0，但传播后可能重复；不能直接依据初始标记判断是否出现多次。',
        declarations=SAM,complexity=r'固定字母表时间 $O(n)$，空间 $O(26n)$；预留至多2n+1状态避免扩容峰值。')
    put(237661,2100,['后缀自动机','长度后缀最大值'],'对每个长度求出现次数最多的子串次数。',
        SAM_EXPLANATION+'\n\n先在F[len[u]]处用count[u]取最大。状态还代表更短子串，而任一长L+1的子串，其长L前缀出现次数不会更少，因此F[L]≥F[L+1]。从长到短取后缀最大值，就补齐各状态长度区间的贡献。',
        r'''string s; cin >> s; SuffixAutomaton sam(s); vector<int> answer(s.size()+1); for (auto &u:sam.node) answer[u.length]=max(answer[u.length],u.count); for (int len=(int)s.size()-1;len>=1;len--) answer[len]=max(answer[len],answer[len+1]); for (int len=1;len<=(int)s.size();len++) cout << answer[len] << '\n';''',
        '必须做从长到短的最大值传播，只记录状态最大长度会漏掉不存在独立状态的长度。',
        declarations=SAM,complexity=r'固定字母表时间 $O(n)$，空间 $O(26n)$。')
    put(237662,2200,['后缀自动机','倍增定位'],'查询原串任意子串的出现次数。',
        SAM_EXPLANATION+'\n\n保存构建第r个前缀时的状态prefix[r]。s[l..r]是这个前缀的长度L=r−l+1后缀，因此沿suffix link向上找到len[u]≥L且len[link[u]]<L的状态，它的count就是所求。预处理link倍增表，从高位开始只跳到len仍≥L的祖先。',
        r'''string s; cin >> s; SuffixAutomaton sam(s); int size=sam.node.size(),levels=1; while ((1LL<<levels)<=size) levels++; vector<vector<int>> up(levels,vector<int>(size)); for (int u=1;u<size;u++) up[0][u]=sam.node[u].link; for (int b=1;b<levels;b++) for (int u=0;u<size;u++) up[b][u]=up[b-1][up[b-1][u]]; int q; cin >> q; while (q--) { int l,r; cin >> l >> r; int length=r-l+1,u=sam.prefix[r]; for (int b=levels-1;b>=0;b--) if (sam.node[up[b][u]].length>=length) u=up[b][u]; cout << sam.node[u].count << '\n'; }''',
        '按子串长度定位，不是直接使用prefix[r]次数。原串构建完成后prefix[r]状态仍有效，克隆只调整其link。',
        declarations=SAM,complexity=r'预处理 $O(n\log n)$，每问 $O(\log n)$，空间 $O(26n+n\log n)$。')
    put(237308,2200,['后缀自动机','公共子串'],'求两串本质不同公共子串数量。',
        SAM_EXPLANATION+'\n\n对s建SAM，扫描t维护当前最长匹配后缀长度L和状态u；失配时沿link缩短，能转移后继续匹配，并记best[u]=max(best[u],L)。扫描后按len降序把best[u]传给link父亲，传递长度不能超过父亲len。\n\n状态u原本代表(len[parent],len[u]]内的不同子串，如今t能匹配的最长长度为best[u]，所以公共贡献为max(0,min(best[u],len[u])−len[parent])。逐状态累加就不会重复统计。',
        r'''string s,t; cin >> s >> t; SuffixAutomaton sam(s); vector<int> best(sam.node.size()); int u=0,length=0; for (char ch:t) { int c=ch-'a'; while (u && !sam.node[u].next[c]) { u=sam.node[u].link; length=sam.node[u].length; } if (sam.node[u].next[c]) { u=sam.node[u].next[c]; length++; } else { u=0; length=0; } best[u]=max(best[u],length); } for (int i=(int)sam.order.size()-1;i>0;i--) { int v=sam.order[i],p=sam.node[v].link; best[p]=max(best[p],min(best[v],sam.node[p].length)); } long long answer=0; for (int v=1;v<(int)sam.node.size();v++) answer+=max(0,min(best[v],sam.node[v].length)-sam.node[sam.node[v].link].length); cout << answer;''',
        '这里只计不同字符串，不乘出现次数。向link传播时须截断为父状态长度。',
        declarations=SAM,complexity=r'固定字母表时间 $O(|s|+|t|)$，空间 $O(26|s|+|t|)$。')
    put(237664,2300,['后缀自动机','倍增','动态规划'],'付p键入一字符或付q复制已经输出的子串，最小打印费用。',
        SAM_EXPLANATION+'\n\n先对整串建SAM，记录每个状态的最小结束位置minEnd：每个前缀状态加入自身位置，克隆初始无穷，再按len降序向link取最小。对于以i结束、长L的后缀，能从已经输出的前缀复制，当且仅当其最早出现结束点≤i−L。\n\n沿prefix[i]的link祖先链，越短越容易满足。用倍增跳过“minEnd[u]+len[u]>i”的状态，停在第一个临界状态u；它的父亲长度整段可复制，而u自身区间能复制到min(len[u],i−minEnd[u])，二者最大值就是最长不重叠可复制后缀L。\n\n设dp[i]为前i字最小费用，dp[i]=min(dp[i−1]+p,dp[i−L]+q)。只用最长L足够，因为dp不减：把某个打印方案截短，最后一次复制也可截成更短的已出现子串，费用不会增加。因此同费用复制越长不会更差。',
        r'''string s; long long p,q; cin >> s >> p >> q; int n=s.size(); SuffixAutomaton sam(s); int size=sam.node.size(),levels=1; while ((1LL<<levels)<=size) levels++; vector<int> minimum(size,n+1); for (int i=1;i<=n;i++) minimum[sam.prefix[i]]=min(minimum[sam.prefix[i]],i); for (int i=(int)sam.order.size()-1;i>0;i--) { int u=sam.order[i]; minimum[sam.node[u].link]=min(minimum[sam.node[u].link],minimum[u]); } vector<vector<int>> up(levels,vector<int>(size)); for (int u=1;u<size;u++) up[0][u]=sam.node[u].link; for (int b=1;b<levels;b++) for (int u=0;u<size;u++) up[b][u]=up[b-1][up[b-1][u]]; vector<long long> dp(n+1); for (int i=1;i<=n;i++) { int u=sam.prefix[i]; for (int b=levels-1;b>=0;b--) { int v=up[b][u]; if (v && minimum[v]+sam.node[v].length>i) u=v; } int parent=sam.node[u].link,length=max(sam.node[parent].length,min(sam.node[u].length,i-minimum[u])); dp[i]=dp[i-1]+p; if (length>0) dp[i]=min(dp[i],dp[i-length]+q); } cout << dp[n];''',
        '复制源必须完整位于此次粘贴之前，不允许一边粘贴一边借用新输出字符。用minEnd条件排除重叠。',
        declarations=SAM,complexity=r'时间 $O(n\log n)$，空间 $O(26n+n\log n)$。')
    put(236737,2200,['回文树','出现次数'],'回文子串长度乘出现次数的最大值。',
        '回文树每个非根节点代表一个不同回文串，两个根分别为长度−1、0。加入字符c时，从当前最长回文后缀沿fail找能被c两侧包住的后缀，得到新回文；若节点不存在则建立并寻找其最长真回文后缀fail。给当前最长回文后缀次数加1。\n\n每个位置结束的较短回文都在其fail链上，因此最后按创建编号逆序向fail累加次数，得到每个回文的真实出现次数。fail节点总比自己早建，逆编号即可。取len*count最大值。',
        r'''int n; string s; cin >> n >> s; struct Node { array<int,26> next={}; int length=0,fail=0,count=0; }; vector<Node> node; node.reserve(n+2); node.emplace_back(); node.emplace_back(); node[0].length=-1; node[1].fail=0; int last=1; auto find=[&](int u,int position) { while (position-node[u].length-1<0 || s[position-node[u].length-1]!=s[position]) u=node[u].fail; return u; }; for (int i=0;i<n;i++) { int c=s[i]-'a',p=find(last,i); if (!node[p].next[c]) { int u=node.size(); node.emplace_back(); node[u].length=node[p].length+2; node[u].fail=node[u].length==1?1:node[find(node[p].fail,i)].next[c]; node[p].next[c]=u; } last=node[p].next[c]; node[last].count++; } long long answer=0; for (int u=(int)node.size()-1;u>=2;u--) { answer=max(answer,1LL*node[u].length*node[u].count); node[node[u].fail].count+=node[u].count; } cout << answer;''',
        '长度−1根保证总能扩展，不参与答案。重复出现可重叠，不能只计不同回文节点数量。',
        complexity=r'固定字母表时间 $O(n)$，空间 $O(26n)$。')


if __name__ == '__main__': run()
