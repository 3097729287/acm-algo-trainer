"""Static RMQ, online append maxima and lazy interval transformations."""
from nowcoder_editorials import CONTENT, add, read

RMQ = r'''
struct RangeMaximum {
    int size = 1; vector<long long> tree;
    RangeMaximum(int n) { while (size < n) size <<= 1; tree.assign(size*2,LLONG_MIN); }
    void setValue(int p,long long value) { p += size; tree[p] = value; for (p >>= 1; p; p >>= 1) tree[p] = max(tree[p*2],tree[p*2+1]); }
    long long query(int l,int r) {
        long long result = LLONG_MIN;
        for (l += size,r += size; l < r; l >>= 1,r >>= 1) {
            if (l & 1) result = max(result,tree[l++]);
            if (r & 1) result = max(result,tree[--r]);
        }
        return result;
    }
};
'''
BIT = r'''
struct Fenwick {
    int n; vector<long long> tree;
    Fenwick(int n): n(n),tree(n+1) {}
    void add(int p,long long v) { for (;p <= n;p += p & -p) tree[p] += v; }
    long long sum(int p) { long long result = 0; for (;p;p -= p & -p) result += tree[p]; return result; }
};
'''
ASSIGN = r'''
struct SegmentTree {
    int n; vector<long long> sum,tag; vector<bool> marked;
    SegmentTree(const vector<long long> &a): n((int)a.size()-1),sum(4*n+4),tag(4*n+4),marked(4*n+4) { build(1,1,n,a); }
    void build(int u,int l,int r,const vector<long long> &a) {
        if (l == r) { sum[u] = a[l]; return; }
        int mid = (l+r)/2; build(u*2,l,mid,a); build(u*2+1,mid+1,r,a); sum[u] = sum[u*2]+sum[u*2+1];
    }
    void apply(int u,int l,int r,long long b) { sum[u] = (1LL*(l+r)+2*b)*(r-l+1)/2; marked[u] = true; tag[u] = b; }
    void push(int u,int l,int r) {
        if (!marked[u] || l == r) return;
        int mid=(l+r)/2; apply(u*2,l,mid,tag[u]); apply(u*2+1,mid+1,r,tag[u]); marked[u]=false;
    }
    void change(int u,int l,int r,int ql,int qr,long long b) {
        if (ql <= l && r <= qr) { apply(u,l,r,b); return; }
        push(u,l,r); int mid=(l+r)/2;
        if (ql <= mid) change(u*2,l,mid,ql,qr,b);
        if (qr > mid) change(u*2+1,mid+1,r,ql,qr,b);
        sum[u]=sum[u*2]+sum[u*2+1];
    }
    long long query(int u,int l,int r,int ql,int qr) {
        if (ql <= l && r <= qr) return sum[u];
        push(u,l,r); int mid=(l+r)/2; long long result=0;
        if (ql <= mid) result+=query(u*2,l,mid,ql,qr);
        if (qr > mid) result+=query(u*2+1,mid+1,r,ql,qr);
        return result;
    }
};
'''


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    put(25045,1400,['线段树','区间最值'],'静态身高数组，多次查询闭区间最高与最低差。',
        '建立两棵区间最大值树：第一棵放原身高，第二棵放相反数。区间最小值就是相反数最大值的负数，因此答案为maxHeight+maxNegative。查询时把输入闭区间[A,B]转为零下标半开区间[A−1,B)。',
        r'''int n,q; cin >> n >> q; RangeMaximum high(n),negative(n); for (int i=0;i<n;i++) { long long x; cin >> x; high.setValue(i,x); negative.setValue(i,-x); } while (q--) { int l,r; cin >> l >> r; cout << high.query(l-1,r)+negative.query(l-1,r) << '\n'; }''',
        '只有一个元素时差为0；两棵树必须查询相同区间。',
        declarations=RMQ,complexity=r'构建 $O(n\log n)$，每问 $O(\log n)$，空间 $O(n)$。')
    put(20164,1700,['单调栈','二分查找'],'末尾加入反馈取模后的数，查询最后L项最大值。',
        '维护下标递增、数值严格递减的候选栈。新值v加入时，栈尾值≤v的候选可以永久删除：未来任何包含旧下标的后缀也包含更新、更大的v。查询最后L项，就是找栈中第一个下标≥长度−L+1的候选，它是区间最大值，二分即可。每次把答案记录为t，供下次插入使用。',
        r'''int m; long long d; cin >> m >> d; vector<int> position; vector<long long> value; int length=0; long long last=0; while (m--) { char op; long long x; cin >> op >> x; if (op == 'A') { long long v=((x%d)+last)%d; length++; while (!value.empty() && value.back() <= v) { value.pop_back(); position.pop_back(); } position.push_back(length); value.push_back(v); } else { int start=length-(int)x+1; int index=lower_bound(position.begin(),position.end(),start)-position.begin(); last=value[index]; cout << last << '\n'; } }''',
        '被支配候选可删，历史查询答案t仍独立保存。先对输入x取模，再加t，避免长整数输入相加溢出。',
        declarations='',complexity=r'插入总计 $O(M)$，每问 $O(\log M)$，空间 $O(M)$。')
    put(20259,2000,['离散化','区间最大值','分类讨论'],'部分年份降雨已知，判断“X是自Y以来最多”的真假或不确定。',
        '二分找到Y、X是否已知，并查询严格中间(Y,X)内已知雨量最大值M。若两端已知且rain[Y]<rain[X]，必假；X已知且M≥rain[X]，必假；X未知但Y已知且M≥rain[Y]，也必假，因为X既须大于M又不能超过Y。\n\n排除矛盾后，只有两端都已知且X−Y等于两端记录下标差，才说明整段每一年都已记录，可输出true；否则仍有未知年份，输出maybe。未知两端也不应擅自补为0。',
        r'''int n; cin >> n; vector<long long> year(n),rain(n); RangeMaximum maximum(n); for (int i=0;i<n;i++) { cin >> year[i] >> rain[i]; maximum.setValue(i,rain[i]); } int q; cin >> q; while (q--) { long long y,x; cin >> y >> x; int iy=lower_bound(year.begin(),year.end(),y)-year.begin(),ix=lower_bound(year.begin(),year.end(),x)-year.begin(); bool knownY=iy<n && year[iy]==y,knownX=ix<n && year[ix]==x; int left=upper_bound(year.begin(),year.end(),y)-year.begin(),right=lower_bound(year.begin(),year.end(),x)-year.begin(); long long middle=maximum.query(left,right); bool bad=(knownY && knownX && rain[iy]<rain[ix]) || (knownX && middle>=rain[ix]) || (knownY && !knownX && middle>=rain[iy]); if (bad) cout << "false\n"; else if (knownY && knownX && x-y==ix-iy) cout << "true\n"; else cout << "maybe\n"; }''',
        '中间年份降雨必须严格小于X，因此相等也是假。年份可能为负，差值用64位。原查询语义为Y<X。',
        declarations=RMQ,complexity=r'预处理 $O(n\log n)$，每问 $O(\log n)$，空间 $O(n)$。')
    put(22593,2100,['线段树','覆盖计数','集合去重'],'动态集合中插入、删除闭整数线段，询问所有线段覆盖的整数点数。',
        '样例[1,2]贡献2，说明计算的是整数点个数。将[l,r]映射成半开单位段[l,r+1)，在坐标0..L上建树。节点维护直接覆盖次数cover；cover>0时整段全覆盖，否则由子段已覆盖长度相加。集合set负责去重，只有首次插入和确实存在的删除才修改覆盖树。一次删除与先前同段插入使用完全相同的节点分解，所以cover不会错误抵消其他区间。',
        r'''int n,limit; cin >> n >> limit; vector<int> cover(4*(limit+1)+4),length(cover.size()); auto update=[&](auto &&self,int u,int l,int r,int ql,int qr,int delta)->void { if (ql<=l && r<=qr) cover[u]+=delta; else { int mid=(l+r)/2; if (ql<=mid) self(self,u*2,l,mid,ql,qr,delta); if (qr>mid) self(self,u*2+1,mid+1,r,ql,qr,delta); } if (cover[u]) length[u]=r-l+1; else length[u]=l==r?0:length[u*2]+length[u*2+1]; }; set<pair<int,int>> active; while (n--) { int op,l,r; cin >> op >> l >> r; if (op==1 && active.insert({l,r}).second) update(update,1,0,limit,l,r,1); else if (op==2 && active.erase({l,r})) update(update,1,0,limit,l,r,-1); else if (op==3) cout << length[1] << '\n'; }''',
        '这是set而非多重集，重复加入不能重复计数。询问行仍有两个无用参数，必须读完。',
        complexity=r'每次修改 $O(\log L+\log N)$，查询 $O(1)$，空间 $O(L+N)$。')
    body=r'''int n,q; cin >> n >> q; Fenwick first(n),second(n); auto point=[&](int p,long long x) { if (p<=n) { first.add(p,x); second.add(p,x*(p-1)); } }; long long previous=0; for (int i=1;i<=n;i++) { long long x; cin >> x; point(i,x-previous); previous=x; } auto prefix=[&](int p) { return p*first.sum(p)-second.sum(p); }; while (q--) { OPREAD if (CHANGE) { long long x; cin >> x; point(l,x); point(r+1,-x); } else cout << prefix(r)-prefix(l-1) << '\n'; }'''
    for number,numeric in [(51100,False),(50454,True)]:
        code=body.replace('OPREAD','int op,l,r; cin >> op >> l >> r;' if numeric else 'char op; int l,r; cin >> op >> l >> r;').replace('CHANGE','op==1' if numeric else "op=='C'")
        put(number,1800,['树状数组','差分'],'维护区间加与区间求和。',
            '设差分d[i]=a[i]−a[i−1]。给[l,r]加x只改变d[l]+=x、d[r+1]−=x。前缀和Σ(i=1..p)a[i]=Σ(j=1..p)(p−j+1)d[j]=p*Σd[j]−Σ(j−1)d[j]。用两棵树状数组分别维护d[j]与(j−1)d[j]，区间和由两个前缀和相减得到。',
            code,'初始数组也必须转换为差分写入两棵树。r=n时忽略n+1端点；节点、加权差分和总和均用64位。',
            declarations=BIT,complexity=r'初始化 $O(n\log n)$，每次操作 $O(\log n)$，空间 $O(n)$。')
    put(200195,1900,['线段树','覆盖懒标记','等差数列'],'区间覆盖为k,k+1,...并查询区间和。',
        '对本次左端l，目标值可写为a[i]=i+b，其中b=k−l。因此懒标记只保存全局偏移b，不必给每个子区间另算首项。覆盖节点[L,R]后，区间和=(L+R+2b)*(R−L+1)/2。新覆盖直接替换旧标记；部分访问前把标记下传，子节点继续使用相同b。',
        r'''int n,m; cin >> n >> m; vector<long long> a(n+1); for (int i=1;i<=n;i++) cin >> a[i]; SegmentTree tree(a); while (m--) { int op,l,r; cin >> op >> l >> r; if (op==1) { long long k; cin >> k; tree.change(1,1,n,l,r,k-l); } else cout << tree.query(1,1,n,l,r) << '\n'; }''',
        '偏移b可能为0或负数，必须独立保存“是否存在覆盖”的布尔标记，不能用tag==0判断。',
        declarations=ASSIGN,complexity=r'构建 $O(n)$，每次操作 $O(\log n)$，空间 $O(n)$。')
    put(25879,2100,['线段树','区间加','二次统计量'],'区间加并询问所有下标对i<j的a[i]*a[j]之和。',
        '节点维护总和S和下标对乘积和P。左右合并时，跨左右的对贡献S左*S右，所以P=P左+P右+S左*S右。长len的一段统一加x，每一对新增x*(a[i]+a[j])+x²；每个原值被计算len−1次，因此P新增x*(len−1)*S+C(len,2)*x²，S新增len*x。以区间加懒标记维护即可。\n\n中间乘积增长比区间和更快，代码用128位保存S、P与乘法，并提供十进制输出。',
        r'''int n,q; cin >> n >> q; vector<__int128> sum(4*n+4),pairs(sum.size()),tag(sum.size()); auto pull=[&](int u) { sum[u]=sum[u*2]+sum[u*2+1]; pairs[u]=pairs[u*2]+pairs[u*2+1]+sum[u*2]*sum[u*2+1]; }; auto apply=[&](int u,int l,int r,__int128 x) { long long len=r-l+1; pairs[u]+=x*(len-1)*sum[u]+(__int128)len*(len-1)/2*x*x; sum[u]+=len*x; tag[u]+=x; }; auto build=[&](auto &&self,int u,int l,int r)->void { if (l==r) { long long x; cin >> x; sum[u]=x; return; } int mid=(l+r)/2; self(self,u*2,l,mid); self(self,u*2+1,mid+1,r); pull(u); }; build(build,1,1,n); auto push=[&](int u,int l,int r) { if (!tag[u] || l==r) return; int mid=(l+r)/2; apply(u*2,l,mid,tag[u]); apply(u*2+1,mid+1,r,tag[u]); tag[u]=0; }; auto change=[&](auto &&self,int u,int l,int r,int ql,int qr,long long x)->void { if (ql<=l && r<=qr) { apply(u,l,r,x); return; } push(u,l,r); int mid=(l+r)/2; if (ql<=mid) self(self,u*2,l,mid,ql,qr,x); if (qr>mid) self(self,u*2+1,mid+1,r,ql,qr,x); pull(u); }; auto query=[&](auto &&self,int u,int l,int r,int ql,int qr)->pair<__int128,__int128> { if (ql<=l && r<=qr) return {sum[u],pairs[u]}; push(u,l,r); int mid=(l+r)/2; pair<__int128,__int128> a={0,0},b={0,0}; if (ql<=mid) a=self(self,u*2,l,mid,ql,qr); if (qr>mid) b=self(self,u*2+1,mid+1,r,ql,qr); return {a.first+b.first,a.second+b.second+a.first*b.first}; }; auto print=[](__int128 value) { if (value<0) { cout << '-'; value=-value; } string text; do { text.push_back('0'+value%10); value/=10; } while (value); reverse(text.begin(),text.end()); cout << text << '\n'; }; while (q--) { int op,l,r; cin >> op >> l >> r; if (op==1) { long long x; cin >> x; change(change,1,1,n,l,r,x); } else print(query(query,1,1,n,l,r).second); }''',
        '先用旧S更新P，再修改S。单元素区间没有数对，P为0；两个查询结果的合并也要加入跨段乘积。',
        complexity=r'构建 $O(n)$，每次操作 $O(\log n)$，空间 $O(n)$。')


if __name__ == '__main__': run()
