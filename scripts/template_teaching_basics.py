"""Authored, individually checked variations for the basic solving templates.

This is teaching source, not a completion generator. Each named variation has
its own contract, counterexample and independently exercised implementation.
"""
from textwrap import dedent


def cpp(text):
    return dedent(text).strip() + '\n'


PAIR = cpp(r'''
// a 已经非递减排序。返回两个不同位置；不存在返回 {-1,-1}。
pair<int,int> pair_sum(const vector<long long>& a,long long target) {
    int left=0,right=(int)a.size()-1;
    while(left<right) {
        // 先提升再相加；即使两项接近 long long 极值也不溢出。
        __int128 sum=(__int128)a[left]+a[right];
        if(sum==target) return {left,right};
        if(sum<target) ++left; // 此 left 与任何剩余位置配对都过小。
        else --right;         // 此 right 与任何剩余位置配对都过大。
    }
    return {-1,-1};
}
''')
PAIR_CONTEST = cpp(r'''
pair<int,int> pair_sum(const vector<long long>& a,long long x) {
    int l=0,r=(int)a.size()-1;
    while(l<r){__int128 s=(__int128)a[l]+a[r];
        if(s==x)return {l,r};if(s<x)++l;else --r;}
    return {-1,-1};
}
''')
COUNT_PAIRS = cpp(r'''
// 数原下标 i<j 的配对份数；a 非递减，重复数不是同一个对象。
long long count_pairs(const vector<long long>& a,long long target) {
    int left=0,right=(int)a.size()-1;long long answer=0;
    while(left<right) {
        __int128 sum=(__int128)a[left]+a[right];
        if(sum<target){++left;continue;}
        if(sum>target){--right;continue;}
        if(a[left]==a[right]) {
            long long count=right-left+1;
            answer+=count*(count-1)/2;break; // 同值段内任取两个下标。
        }
        long long x=a[left],y=a[right],first=0,second=0;
        while(left<=right&&a[left]==x){++first;++left;}
        while(left<=right&&a[right]==y){++second;--right;}
        answer+=first*second; // 两段的每个下标可以相互配对。
    }
    return answer;
}
''')
COUNT_PAIRS_CONTEST = cpp(r'''
long long count_pairs(const vector<long long>& a,long long x){
    int l=0,r=(int)a.size()-1;long long ans=0;
    while(l<r){__int128 s=(__int128)a[l]+a[r];
        if(s<x){++l;continue;}if(s>x){--r;continue;}
        if(a[l]==a[r]){long long n=r-l+1;ans+=n*(n-1)/2;break;}
        long long u=a[l],v=a[r],p=0,q=0;
        while(l<=r&&a[l]==u)++p,++l;
        while(l<=r&&a[r]==v)++q,--r;ans+=p*q;}
    return ans;
}
''')
UNIQUE = cpp(r'''
// a 已排序。在原数组前缀保留每种值第一次出现的内容，返回新长度。
int unique_prefix(vector<long long>& a) {
    int write=0;
    for(int read=0;read<(int)a.size();++read) {
        // [0,write) 是已读前缀去重后的结果；write 不超过 read。
        if(write==0||a[read]!=a[write-1])a[write++]=a[read];
    }
    // 尾部不是结果；调用者要按返回长度读取或 a.resize(write)。
    return write;
}
''')
UNIQUE_CONTEST = cpp(r'''
int unique_prefix(vector<long long>& a){int w=0;
    for(int r=0;r<(int)a.size();++r)if(!w||a[r]!=a[w-1])a[w++]=a[r];
    return w;
}
''')
LONGEST = cpp(r'''
// 非负数组，limit>=0，且总和可存入 long long。返回和不超过 limit 的最长长度。
int longest_window(const vector<long long>& a,long long limit) {
    assert(limit>=0);int left=0,best=0;long long sum=0;
    for(int right=0;right<(int)a.size();++right) {
        assert(a[right]>=0);sum+=a[right]; // 加入右端后，[left,right] 的真实总和。
        while(left<=right&&sum>limit)sum-=a[left++];
        // 已恢复合法性；所有更左的起点均已因过大排除，当前段最长。
        best=max(best,right-left+1);
    }
    return best;
}
''')
LONGEST_CONTEST = cpp(r'''
int longest_window(const vector<long long>& a,long long k){
    assert(k>=0);int l=0,ans=0;long long s=0;
    for(int r=0;r<(int)a.size();++r){assert(a[r]>=0);s+=a[r];
        while(l<=r&&s>k)s-=a[l++];ans=max(ans,r-l+1);}
    return ans;
}
''')
SHORTEST = cpp(r'''
// 非负数组，target>0，总和可存入 long long；找不到返回 0。
int shortest_window(const vector<long long>& a,long long target) {
    assert(target>0);int left=0,best=(int)a.size()+1;long long sum=0;
    for(int right=0;right<(int)a.size();++right) {
        assert(a[right]>=0);sum+=a[right];
        // 每个合法段先计入答案，再删左端；不能只保留最终不合法状态。
        while(left<=right&&sum>=target) {
            best=min(best,right-left+1);sum-=a[left++];
        }
    }
    return best==(int)a.size()+1?0:best;
}
''')
SHORTEST_CONTEST = cpp(r'''
int shortest_window(const vector<long long>& a,long long k){
    assert(k>0);int l=0,ans=(int)a.size()+1;long long s=0;
    for(int r=0;r<(int)a.size();++r){assert(a[r]>=0);s+=a[r];
        while(l<=r&&s>=k){ans=min(ans,r-l+1);s-=a[l++];}}
    return ans==(int)a.size()+1?0:ans;
}
''')
COUNT_WINDOWS = cpp(r'''
// 非负数组，总和与段数可存入 long long；不统计空段。
long long windows_at_most(const vector<long long>& a,long long limit) {
    if(limit<0)return 0; // 非负元素组成的非空段不可能有负总和。
    int left=0;long long sum=0,answer=0;
    for(int right=0;right<(int)a.size();++right) {
        assert(a[right]>=0);sum+=a[right];
        while(left<=right&&sum>limit)sum-=a[left++];
        // 固定右端，合法起点恰为 left..right，共 right-left+1 个。
        answer+=right-left+1;
    }
    return answer;
}
long long windows_exactly(const vector<long long>& a,long long target) {
    if(target<0)return 0;
    // 两个嵌套集合相减。target=0 时后一项返回 0，零元素不会漏计。
    return windows_at_most(a,target)-windows_at_most(a,target-1);
}
''')
COUNT_WINDOWS_CONTEST = cpp(r'''
long long windows_at_most(const vector<long long>& a,long long k){
    if(k<0)return 0;int l=0;long long s=0,ans=0;
    for(int r=0;r<(int)a.size();++r){assert(a[r]>=0);s+=a[r];
        while(l<=r&&s>k)s-=a[l++];ans+=r-l+1;}return ans;
}
long long windows_exactly(const vector<long long>& a,long long k){
    return k<0?0:windows_at_most(a,k)-windows_at_most(a,k-1);
}
''')
FIXED = cpp(r'''
// 固定长度窗口的和可以允许负数；只依赖加、减可逆，不依赖和的单调性。
pair<long long,int> minimum_fixed(const vector<long long>& a,int width) {
    assert(1<=width&&width<=(int)a.size());
    long long sum=0;for(int i=0;i<width;++i)sum+=a[i];
    long long best=sum;int start=0;
    for(int right=width;right<(int)a.size();++right) {
        sum+=a[right]-a[right-width]; // 移出旧左端，移入新右端。
        if(sum<best){best=sum;start=right-width+1;}
    }
    return {best,start}; // 仅严格变小才更新，所以保留最早起点。
}
''')
FIXED_CONTEST = cpp(r'''
pair<long long,int> minimum_fixed(const vector<long long>& a,int k){
    assert(k>0&&k<=(int)a.size());long long s=0;
    for(int i=0;i<k;++i)s+=a[i];long long best=s;int p=0;
    for(int r=k;r<(int)a.size();++r){s+=a[r]-a[r-k];
        if(s<best)best=s,p=r-k+1;}return {best,p};
}
''')
LAST_TRUE = cpp(r'''
// [left,right) 上 true 在前、false 在后。无 true 用 nullopt，避免 left-1 溢出。
template<class Predicate>
optional<long long> last_true(long long left,long long right,Predicate feasible) {
    assert(left<=right);long long begin=left;
    while(left<right) {
        long long middle=(long long)((__int128)left+((__int128)right-left)/2);
        if(feasible(middle))left=middle+1;else right=middle;
    }
    if(left==begin)return nullopt;
    return left-1; // left>begin>=LLONG_MIN，这里才允许减 1。
}
''')
LAST_TRUE_CONTEST = cpp(r'''
template<class F>optional<long long> last_true(long long l,long long r,F ok){
    assert(l<=r);long long b=l;
    while(l<r){long long m=(long long)((__int128)l+((__int128)r-l)/2);
        if(ok(m))l=m+1;else r=m;}
    return l==b?nullopt:optional<long long>(l-1);
}
''')
BOUNDS = cpp(r'''
// 两种边界分别证明：第一个 >=x；第一个 >x。空数组都返回 0。
int lower_position(const vector<long long>& a,long long x) {
    int left=0,right=a.size();
    while(left<right){int middle=left+(right-left)/2;
        if(a[middle]>=x)right=middle;else left=middle+1;}
    return left;
}
int upper_position(const vector<long long>& a,long long x) {
    int left=0,right=a.size();
    while(left<right){int middle=left+(right-left)/2;
        if(a[middle]>x)right=middle;else left=middle+1;}
    return left;
}
''')
BOUNDS_CONTEST = cpp(r'''
int lower_position(const vector<long long>& a,long long x){int l=0,r=a.size();
    while(l<r){int m=l+(r-l)/2;if(a[m]>=x)r=m;else l=m+1;}return l;}
int upper_position(const vector<long long>& a,long long x){int l=0,r=a.size();
    while(l<r){int m=l+(r-l)/2;if(a[m]>x)r=m;else l=m+1;}return l;}
''')
PREFIX2D = cpp(r'''
// 允许负数；外部坐标均从 0 开始，查询矩形 [x1,x2) × [y1,y2)。
vector<vector<long long>> prefix_2d(const vector<vector<long long>>& a) {
    int n=a.size(),m=n?a[0].size():0;
    vector<vector<long long>> p(n+1,vector<long long>(m+1));
    for(int i=0;i<n;++i)for(int j=0;j<m;++j)
        p[i+1][j+1]=a[i][j]+p[i][j+1]+p[i+1][j]-p[i][j];
    return p;
}
long long rectangle(const vector<vector<long long>>& p,int x1,int y1,int x2,int y2) {
    // 两块被减去的区域在左上角重叠一次，必须补回来一次。
    return p[x2][y2]-p[x1][y2]-p[x2][y1]+p[x1][y1];
}
''')
PREFIX2D_CONTEST = cpp(r'''
vector<vector<long long>> prefix_2d(const vector<vector<long long>>& a){
    int n=a.size(),m=n?a[0].size():0;vector<vector<long long>>p(n+1,vector<long long>(m+1));
    for(int i=0;i<n;++i)for(int j=0;j<m;++j)p[i+1][j+1]=a[i][j]+p[i][j+1]+p[i+1][j]-p[i][j];return p;
}
long long rectangle(const vector<vector<long long>>& p,int x,int y,int u,int v){
    return p[u][v]-p[x][v]-p[u][y]+p[x][y];
}
''')
MAX_WINDOW = cpp(r'''
vector<long long> sliding_maximum(const vector<long long>& a,int width) {
    if(width<=0||width>(int)a.size())return {};
    deque<int> pending;vector<long long> result;
    for(int right=0;right<(int)a.size();++right) {
        while(!pending.empty()&&pending.front()<=right-width)pending.pop_front();
        // 新值 >= 旧值且更晚过期，旧值从现在开始都不可能胜出。
        while(!pending.empty()&&a[pending.back()]<=a[right])pending.pop_back();
        pending.push_back(right);
        if(right+1>=width)result.push_back(a[pending.front()]);
    }
    return result;
}
''')
MAX_WINDOW_CONTEST = cpp(r'''
vector<long long> sliding_maximum(const vector<long long>& a,int k){
    if(k<=0||k>(int)a.size())return {};deque<int>q;vector<long long>out;
    for(int r=0;r<(int)a.size();++r){while(!q.empty()&&q.front()<=r-k)q.pop_front();
        while(!q.empty()&&a[q.back()]<=a[r])q.pop_back();q.push_back(r);
        if(r+1>=k)out.push_back(a[q.front()]);}return out;
}
''')
EARLIEST = cpp(r'''
// 返回每个窗口中最小值最早出现的原数组下标。
vector<int> earliest_minimum(const vector<long long>& a,int width) {
    if(width<=0||width>(int)a.size())return {};
    deque<int> pending;vector<int> result;
    for(int right=0;right<(int)a.size();++right) {
        while(!pending.empty()&&pending.front()<=right-width)pending.pop_front();
        // 相等时旧下标更早，不得删掉。队列值改成非递减。
        while(!pending.empty()&&a[pending.back()]>a[right])pending.pop_back();
        pending.push_back(right);
        if(right+1>=width)result.push_back(pending.front());
    }
    return result;
}
''')
EARLIEST_CONTEST = cpp(r'''
vector<int> earliest_minimum(const vector<long long>& a,int k){
    if(k<=0||k>(int)a.size())return {};deque<int>q;vector<int>out;
    for(int r=0;r<(int)a.size();++r){while(!q.empty()&&q.front()<=r-k)q.pop_front();
        while(!q.empty()&&a[q.back()]>a[r])q.pop_back();q.push_back(r);
        if(r+1>=k)out.push_back(q.front());}return out;
}
''')


def variant(identity, title, text, code, contest, oracle, driver):
    return dict(id=identity, title=title, markdown=dedent(text).strip(), code=code, contestCode=contest, oracle=oracle, driver=cpp(driver))


VARIANTS = {
    'two-pointers': [
        variant('count-index-pairs', '从找一对改为统计所有下标对', '''
            找到一次相等就返回，会漏掉重复数的不同下标。[1,1,2,2] 的目标为 3 时有 2×2=4 对，而不是一对。

            相等且两端值不同，数清左侧等值段的份数 p、右侧的份数 q，一次贡献 p×q；两端值相同时，剩余段全相同，应贡献 n(n−1)/2。
            这时排除的是已经完整计数的两个等值段，仍不漏、不重。答案用 long long，时间 O(n)、额外空间 O(1)。
            若题目要“不同的数值对”而不是“不同下标对”，贡献就不能乘份数，须重新定义统计对象。
        ''', COUNT_PAIRS, COUNT_PAIRS_CONTEST, 'pair-count', r'''
            int n;long long target;cin>>n>>target;vector<long long>a(n);for(auto&x:a)cin>>x;
            cout<<count_pairs(a,target)<<'\n';
        '''),
        variant('read-write', '同向读写：原地去重', '''
            目标变成压缩有序数组，不再比较两端的和。read 扫描每一个原元素，write 指向下一处可写槽位；不变量为 [0,write) 恰是已读前缀去重后的结果。
            write≤read，写入不会破坏尚未读取的元素。循环结束返回有效长度，旧尾部必须忽略。
            [1,1,2] 得到长度 2 与前缀 [1,2]；未排序的 [1,2,1] 不能用“只比前一个保留值”删除所有重复，需先明确是否允许排序。
            时间 O(n)，额外空间 O(1)。允许每种保留两份时，应比较 a[write-2]，并重证保留份数上限。
        ''', UNIQUE, UNIQUE_CONTEST, 'unique', r'''
            int n;cin>>n;vector<long long>a(n);for(auto&x:a)cin>>x;
            int size=unique_prefix(a);cout<<size<<'\n';for(int i=0;i<size;++i)cout<<a[i]<<' ';
        '''),
    ],
    'sliding-window': [
        variant('shortest-at-least', '从最长不过界改为最短达到目标', '''
            输入仍须非负，target 必须大于 0。加入右端后，sum≥target 时已经有合法答案：先记录当前长度，再删左端尝试更短；循环退出时反而是不合法状态。
            不能沿用“缩到合法以后只记一次”的最长段流程。[2,3,1,2,4,3]、target=7 的最短长度为 2。
            每个左端在首次找到能满足它的右端时已尝试，未来更右的段不可能更短，所以可以永久移出。两个指针总共移动 O(n)，额外空间 O(1)。
            target≤0 涉及是否允许空段，当前实现明确不接受；若允许负数，[1,-1,5]、target=5 会漏掉单元素 [5]，需用前缀和与单调队列等新模型。
        ''', SHORTEST, SHORTEST_CONTEST, 'shortest', r'''
            int n;long long k;cin>>n>>k;vector<long long>a(n);for(auto&x:a)cin>>x;
            cout<<shortest_window(a,k)<<'\n';
        '''),
        variant('count-at-most-exactly', '从求长度改为统计段数，再得到恰好等于', '''
            缩到 sum≤limit 后，固定右端 right，合法起点恰为 left..right。非负性保证删去更多左端不会变大，因此贡献为 right−left+1，不能只加 1。
            对每个右端计数，任意非空段只有一个右端，故没有重复。恰好和为 K 的集合，等于“和≤K”减去“和≤K−1”；这一步基于整数总和与集合包含关系。
            [0,0]、K=0 有三个非空段。limit<0 必须返回 0，使 K=0 也成立；不能拿正数窗口的“遇到相等计一次”代替，否则零会造成多组起点。
            两次窗口扫描仍为 O(n)，段数上界 n(n+1)/2，使用 long long。负数不满足合法起点为连续后缀的证明。
        ''', COUNT_WINDOWS, COUNT_WINDOWS_CONTEST, 'count-windows', r'''
            int n;long long k;cin>>n>>k;vector<long long>a(n);for(auto&x:a)cin>>x;
            cout<<windows_at_most(a,k)<<' '<<windows_exactly(a,k)<<'\n';
        '''),
        variant('fixed-length', '固定长度：不再依赖非负性', '''
            窗口宽度固定为 width，每次移出一项、移入一项。总和能用加减维护即可，允许负数；没有“过大就缩短”的决策。
            初始化先算 [0,width)，其后 right 从 width 开始。新左端为 right−width+1，旧移出位置为 right−width，最后一个窗口必须处理。
            同时记录最小和与起点，严格变小时更新会保留最早起点。width=1、width=n、全负数、并列最小都要测。O(n) 时间、O(1) 额外空间。
            若把总和换成最小值，删掉旧最小值后无法仅凭一个数恢复新最小值，应使用单调队列，不能照搬 sum-=old。
        ''', FIXED, FIXED_CONTEST, 'fixed', r'''
            int n,k;cin>>n>>k;vector<long long>a(n);for(auto&x:a)cin>>x;
            auto [value,start]=minimum_fixed(a,k);cout<<value<<' '<<start<<'\n';
        '''),
    ],
    'binary-search': [
        variant('last-true', '最后一个成立：重新定义区间与空答案', '''
            这里的条件必须先 true 后 false，和基础版的方向相反。仍在 [left,right) 查找，但维护“第一个 false”的候选边界：mid 为 true 时令 left=mid+1，否则 right=mid。
            停止后 left 是第一个 false 或原 right；有 true 才减 1。若 left 等于原 begin，说明没有 true，返回 nullopt，不能用 begin−1，因为 begin 可能为 LLONG_MIN。
            右端不被调用，空区间直接无答案。O(log W) 次判定、O(1) 空间；若判定本身 O(n)，总复杂度为 O(n log W)。
            不要把最小化模板里两个比较号一起反转；本版的返回类型、未命中语义、保留 mid 的方向都已改变。
        ''', LAST_TRUE, LAST_TRUE_CONTEST, 'last', r'''
            long long l,r,t;cin>>l>>r>>t;auto p=last_true(l,r,[&](long long x){return x<=t;});
            if(p)cout<<*p;else cout<<"none";
        '''),
        variant('lower-upper', '重复值的左右边界与出现次数', '''
            非递减数组 [1,3,3,3,7] 中查 3：第一个 ≥3 在 1，第一个 >3 在 4，所以相等区间是 [1,4)，出现 3 次。
            两个函数的真假分界不同，应分别检查：lower 左侧全 <x、右侧全 ≥x；upper 左侧全 ≤x、右侧全 >x。
            都用 [0,n) 与 n 哨兵；返回 n 后绝不能读 a[n]。查一个值是否存在，还须验证位置未越界并且相等；单有 lower 并不代表命中。
            每次 O(log n)、额外空间 O(1)。未排序的 [3,1,3] 无相应单调分界，先排序会改变原下标语义，不能悄悄排序后当作原位置。
        ''', BOUNDS, BOUNDS_CONTEST, 'bounds', r'''
            int n;long long x;cin>>n>>x;vector<long long>a(n);for(auto&v:a)cin>>v;
            cout<<lower_position(a,x)<<' '<<upper_position(a,x)<<'\n';
        '''),
    ],
    'prefix-difference': [
        variant('rectangle-sum', '二维查询：实际减去了哪两块', '''
            p[i][j] 记录前 i 行、前 j 列的矩形，不再是一条线段。求 [x1,x2)×[y1,y2) 时，从右下大矩形减去上侧、左侧，再加回被减两次的左上角。
            构建同理：上方前缀+左方前缀−重叠+当前格。初始化第 0 行、第 0 列为 0，按行从上到下、列从左到右，三个被依赖的前缀都已完成。
            [[1,2],[3,4]] 的右下单格查询应为 4，不能得 3；空矩形为 0，单行与负数不改变加减关系。
            建表 O(nm)、查询 O(1)、空间 O(nm)。这只适合静态可加量；矩形最小值不能用相减得到，修改后的动态查询也不能沿用旧前缀。
        ''', PREFIX2D, PREFIX2D_CONTEST, 'rectangle', r'''
            int n,m;cin>>n>>m;vector<vector<long long>>a(n,vector<long long>(m));for(auto&r:a)for(auto&x:r)cin>>x;
            int x,y,u,v;cin>>x>>y>>u>>v;cout<<rectangle(prefix_2d(a),x,y,u,v)<<'\n';
        '''),
    ],
    'window-extrema': [
        variant('maximum', '最大值队列：用支配关系证明删除', '''
            最小值版删掉“不小于新值”的旧候选，因为新值更小且更晚过期。最大值版必须重新证明：新值更大或相等、且更晚过期，旧值此后不会胜出，所以删掉 ≤ 新值的队尾。
            队列下标仍递增，值改成严格递减；过期条件仍是下标≤right−width，窗口凑齐以后才输出。
            比较方向改变是这个新证明的结果，过期与输出边界没有随之改变。重复值保留较晚下标可缩短队列，但若题目要求最早出现的位置，这种平局处理不再合适。
            递增、递减、全相等、width=1、width=n、非法宽度分别核对；每个下标最多进出一次，O(n) 时间、O(width) 额外空间。
        ''', MAX_WINDOW, MAX_WINDOW_CONTEST, 'maximum', r'''
            int n,k;cin>>n>>k;vector<long long>a(n);for(auto&x:a)cin>>x;
            for(auto x:sliding_maximum(a,k))cout<<x<<' ';
        '''),
        variant('earliest-index', '最小值的最早下标：相等元素不能删', '''
            输出对象从值变成“最早下标”。基础版在相等时保留新下标，对 [2,2]、width=2 会得到下标 1，而最早答案是 0。
            改成只删严格大于新值的队尾，让相等候选按先后保留；队列值因此允许相等。队首过期后，后一个同值候选自然接上。
            删除的旧值必须严格更差，等值旧下标虽然更早过期，却在过期以前仍是更优答案。这个平局规则来自题目要求，不能当作纯性能细节。
            返回原数组 0 开始的下标，需要 1 开始时只在输出加 1。时间 O(n)、队列空间 O(width)，全相等时空间确会达到 width。
        ''', EARLIEST, EARLIEST_CONTEST, 'earliest', r'''
            int n,k;cin>>n>>k;vector<long long>a(n);for(auto&x:a)cin>>x;
            for(auto x:earliest_minimum(a,k))cout<<x<<' ';
        '''),
    ],
}


def notes():
    return {
        'two-pointers': dedent('''
            ## 从条件识别双指针

            先问：一次移动能永久排除哪些候选？“有两个循环变量”并不足以使用双指针。这里的基本任务是：在非递减数组中找两个不同下标，使两项和等于目标。

            left、right 从两端开始，剩余可配对位置在 [left,right] 内。和过小时，即使给 left 配上剩余最大的 right 也不够，因此所有含 left 的未检查配对都可排除；和过大时同理排除 right。负数也允许，因为依据是排序，不是正数。

            每步至少排除一端，left<right 时比较，重合时结束，避免一个位置用两次。两个端点共移动 O(n) 次，额外空间 O(1)；若需要先排序，则再计 O(n log n)。求和先转 __int128，不能在溢出之后再转换。

            ### 何时失效、可以改什么

            未排序的 [3,1,2]、目标 3：照搬两端规则会丢掉 1+2。允许排序时，也要保留原下标才能回答“原来的两个位置”。如果题目要求相邻、原连续段或有时间顺序，排序通常破坏题意。

            返回一对、统计下标对、统计不同值对和找最优值是不同目标，答案统计和等值处理都要重写。改移动依据时，须证明被丢弃的整批候选都不可能改善答案；改同向读写时，须另证不会覆盖未读数据。
        ''').strip(),
        'sliding-window': dedent('''
            ## 从条件识别滑动窗口

            基本任务：非负数组中，求总和不超过 limit 的最长连续段。先保留原顺序；连续段不允许排序。left 从 0 开始，sum=0、best=0，right 从左向右逐项加入。

            sum 始终等于当前 [left,right] 的和。超过 limit 时不断删左端；恢复合法后再记录 right−left+1。非负性保证：一个左端如果当前已经超预算，未来加入更多非负数也不会重新合法，删掉它不会漏解。每个元素最多入、出各一次，总 O(n)、额外 O(1)。

            limit=0 仍允许零元素段；单项大于预算时可收缩为空段。使用 long long 前先核对最大总和，不能只看单项范围。

            ### 条件失效的具体位置

            [4,-3,2]、limit=3：第一步会删掉 4，后来却有合法整段总和 3、长度 3。负数使“以后只会更大”的证明失效。反例不是多改一个比较符号能修复的，应改为前缀和配合适当查询结构。

            维护量也必须支持删除：总和可减回左端，字符种类数需维护频次并在频次降到 0 时减少种类；最值不能靠减去旧值维护，应用单调队列。固定长度窗口则无需上述非负性。下面三种变体的目标、循环停止状态与答案统计分别核对。
        ''').strip(),
        'binary-search': dedent('''
            ## 先定义答案，再选边界

            本模板在 [left,right) 中找第一个条件成立的位置。必须证明判定结果为 false…false,true…true；原 right 是“没有找到”的哨兵，不要求、也不会调用 feasible(right)。

            初始化允许空区间。循环中 mid 总在真实查找域内，成立就保留 mid 并缩右端，不成立就排除到 mid 为止的左半段。循环保持：left 左侧都已判定为 false，right 右侧到原边界前都已判定为 true；尚未排除的答案边界在 [left,right]。两端重合时结束。

            使用 __int128 先计算跨度和中点，支持负边界与 long long 两端极值；不能先做可能溢出的 right-left。判定次数 O(log W)，总时间还要乘判定成本；判定额外空间也计入总体空间。

            ### 如何修改，何时不能修改

            在有序数组中，条件可为 a[mid]≥x 或 a[mid]>x，但返回值含义随之改变。二分答案时，须先证明候选答案的可行性单调，并说明上界为什么包含所有可能答案；“判定函数能运行”不等于有单调性。

            例如条件只在偶数成立，结果 true,false,true,false，没有单调分界，二分会漏掉合法位置。浮点二分需要精度或迭代次数的新停止准则，不能继续使用 mid+1。下方的“最后一个成立”还处理了不存在答案时的溢出风险。
        ''').strip(),
        'prefix-difference': dedent('''
            ## 区分在累计什么

            静态区间和：prefix[i] 是原数组前 i 项，即 [0,i) 的和。初始化 prefix[0]=0，按 i 从左到右令 prefix[i+1]=prefix[i]+a[i]。查询 [left,right) 时取 prefix[right]-prefix[left]，空区间自然为 0。预处理 O(n)、每问 O(1)、空间 O(n)，负数不影响等式。

            离线区间加：difference 记录“从这里开始多了多少增量”。全零初始化，给 [left,right) 加 delta，就在 left 加、right 减；最后一次扫描的 current 是所有仍生效事件之和。右端要额外一格，当 right=n 时停止事件仍可写，但不作为原数组输出。

            Difference 还原的是增量，不是原数组；需要原值时再逐项相加。若输入用 1 开始闭区间 [l,r]，转换为 0 开始 [l-1,r)，不是把 r 也减 1。n 项 10^9 可超 int，累计类型按总范围决定。

            ### 改目标时重做哪一步

            若统计覆盖次数达到 k 的点，要先还原次数，再变成每点 0/1，再为这些 0/1 建查询前缀；不能直接对次数求和。若更新和查询交错，旧前缀已失效，离线差分也不能立即回答总和，需树状数组或线段树。

            区间最小值不可相减：前缀最小值均为 1 的 [1,4,3]，减不出后两项最小值 3。二维的可加查询可推广，但需要明确重叠区域，见下方变体。
        ''').strip(),
        'window-extrema': dedent('''
            ## 窗口移动以后，谁还可能成为最值

            要输出每个固定宽度窗口的最小值。pending 存候选下标，前后下标递增、对应值严格递增；right 是刚加入的位置。初始化空队列，先移出下标≤right−width 的过期候选，再删除被新值支配的队尾，最后压入 right。

            若旧值≥新值，而且旧下标更早，那么旧值既不更小、又更早过期；从此不会优于新值，可以永久删除。队首就是当前最小值；right+1≥width 后窗口才完整，才输出。仅存数值无法判断哪一份重复值过期。

            每个下标最多入队、出队各一次；某一步弹出很多项仍只有总 O(n)，额外队列空间 O(width)，输出另占 O(n−width+1)。width≤0 或 width>n 时当前函数返回空结果。

            ### 平局与更新范围是前提

            基础版删除相等旧值，保留较晚下标，适合只输出值；需要最早位置时必须保留相等旧项，下面另给实现。求最大值需要重新建立“更大且更晚”的支配证明。

            这不是通用任意区间查询：若右端以后倒退，或左端要向左恢复，被永久删除的候选可能重新有用。不能把固定向右滑动的队列直接用于这些操作；实验的回退应恢复历史快照，而不是反向调用入队。
        ''').strip(),
    }


MIGRATIONS = {
    'two-pointers': dict(problemId='lab:codeforces:580B', title='580B · Kefa and Company',
        markdown='''基本配对模板比较两端和；本题要选一组朋友，限制的是最大财富减最小财富严格小于 d，优化的却是友谊值总和。先按财富排序，在同向窗口内累加友谊；当 money[right]-money[left]>=d 时移出左端。排序后中间所有朋友都可纳入，是因为友谊值非负，补上中间人不会降低答案。\n\n状态由一个目标和改为有序的 (money,friendship)、left 与 friendshipSum；答案统计最大总和而非最大人数。单人合法、财富相同、差恰等于 d、最大和 10^14 分别核对；不能把最大人数的窗口模板只改输出变量。时间 O(n log n)、空间 O(n)。''',
        code=cpp(r'''
            #include <bits/stdc++.h>
            using namespace std;
            int main(){ios::sync_with_stdio(false);cin.tie(nullptr);
                int n;long long d;cin>>n>>d;vector<pair<long long,long long>>friends(n);
                for(auto&[money,friendship]:friends)cin>>money>>friendship;
                sort(friends.begin(),friends.end());int left=0;long long sum=0,best=0;
                for(int right=0;right<n;++right){sum+=friends[right].second;
                    while(friends[right].first-friends[left].first>=d)sum-=friends[left++].second;
                    best=max(best,sum);}cout<<best<<'\n';}
        '''), oracle='friends'),
    'sliding-window': dict(problemId='lab:codeforces:279B', title='279B · Books',
        markdown='''原题是连续读书，单本耗时为 1..10000，n≤100000、t≤10^9。对应 longest_window：状态 sum 是当前段耗时，答案是本数；不能把书按耗时排序，否则破坏原来的连续次序。n×10000 不超过 10^9，仍用 long long 为同型任务留出范围。\n\n读取 n,t 与数组，调用基础版后输出长度。官方样例 [3,1,2,1]、t=5 输出 3；[2,2,3]、t=3 输出 1。另测全部能读、单本都超预算、最佳段在末尾。窗口扩展、删左端、计答案的顺序与讲解版逐项相同，时间 O(n)、额外空间 O(1)。''',
        code='#include <bits/stdc++.h>\n#include <cassert>\nusing namespace std;\n'+LONGEST+cpp(r'''
            int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n;long long t;cin>>n>>t;
                vector<long long>a(n);for(auto&x:a)cin>>x;cout<<longest_window(a,t)<<'\n';}
        '''), oracle='books'),
    'binary-search': dict(problemId='luogu-training-P2249', title='P2249 · 查找',
        markdown='''原题已保证非递减，n≤10^6、m≤10^5，元素与查询在 0..10^9，要求第一次出现的 1 开始编号，不存在为 -1。把判定设为 a[mid]>=query，求得 lower_position，再独立检查位置<n 且数值相等；否则这个位置可能只是更大元素或 n 哨兵。\n\n[1,3,3,3,5] 查 3 得 0 开始位置 1，输出 2；查 4 得位置 4，但 a[4]=5，所以输出 -1。官方 11 项、三次查询输出 1 2 -1。每问 O(log n)，总 O(n+m log n)，空间 O(n)。本题保留原有排序，不擅自改数据或使用额外排序。''',
        code='#include <bits/stdc++.h>\n#include <cassert>\nusing namespace std;\n'+BOUNDS+cpp(r'''
            int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n,m;cin>>n>>m;
                vector<long long>a(n);for(auto&x:a)cin>>x;
                while(m--){long long q;cin>>q;int p=lower_position(a,q);
                    cout<<(p<n&&a[p]==q?p+1:-1)<<' ';}}
        '''), oracle='lookup'),
    'prefix-difference': dict(problemId='lab:codeforces:816B', title='816B · Karen and Coffee',
        markdown='''原题的温度为 1..200000，配方推荐闭区间 [l,r]；查询的是至少被 k 份配方推荐的整数温度数量。这里直接沿原题 1 开始编号，差分在 l 加 1、r+1 减 1，数组额外保留 200001。\n\n先还原 cover，再把 cover>=k 转为每点最多贡献 1，good[t] 是 1..t 的合格温度数。查询 [a,b] 得 good[b]-good[a-1]。三份 [1,3]、[2,4]、[4,5]、k=2：cover=[1,2,2,2,1]，合格点数为 3，而覆盖总次数为 8。\n\n原题样例、单点区间、覆盖恰好 k、覆盖大于 k、右端 200000 单独核对；不能将 r+1 停止事件写到 r。U=200000，总 O(n+U+q)、空间 O(U)。''',
        code=cpp(r'''
            #include <bits/stdc++.h>
            using namespace std;
            int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n,k,q;cin>>n>>k>>q;
                const int U=200000;vector<int>difference(U+2),good(U+1);
                for(int i=0,l,r;i<n;++i){cin>>l>>r;++difference[l];--difference[r+1];}
                int cover=0;for(int t=1;t<=U;++t){cover+=difference[t];good[t]=good[t-1]+(cover>=k);}
                while(q--){int a,b;cin>>a>>b;cout<<good[b]-good[a-1]<<'\n';}}
        '''), oracle='coffee'),
    'window-extrema': dict(problemId='luogu-training-P1886', title='P1886 · 单调队列 / 滑动窗口',
        markdown='''原题 n≤10^6、1≤k≤n，元素为 32 位有符号整数，要先输出全部窗口最小值，再输出全部最大值。保留基础的最小值函数，加入已经单独证明的最大值函数，分别扫描两次；不是交替输出两类值。\n\n官方 [1,3,-1,-3,5,3,6,7]、k=3 输出两行。复测全相等、递增、递减与 -2147483648，k=1 及 k=n。使用 long long 读取与输出兼容最小负数；这里仅比较，不需要取负来求最大值。两次扫描仍 O(n)，数组、输出 O(n)，单次队列 O(k)。''',
        oracle='extrema'),
}


def additions():
    return [dict(id='builtin:two-pointers', title='双指针：相向查找与同向读写', category='基础算法',
                 summary='先证明移动不会漏解；区分一对、下标对计数与原地保留。', tags=['双指针'],
                 language='cpp17', builtin=True, code='#include <bits/stdc++.h>\n#include <cassert>\nusing namespace std;\n'+PAIR,
                 contestCode='#include <bits/stdc++.h>\n#include <cassert>\nusing namespace std;\n'+PAIR_CONTEST,
                 example='int main(){assert((pair_sum({-3,0,2,4},1)==pair<int,int>(0,3)));assert((pair_sum({1},2)==pair<int,int>(-1,-1)));}\n',
                 contestExample='int main(){assert((pair_sum({-3,0,2,4},1)==pair<int,int>(0,3)));assert((pair_sum({1},2)==pair<int,int>(-1,-1)));}\n',
                 notes='输入已排序；允许负数。O(n) 查找、O(1) 额外空间；需要排序时另计复杂度与原下标。',
                 contestNotes='已排序，允许负数；返回不同的 0 开始下标或 {-1,-1}。', practiceIds=[], learningPath='two-pointers'),
            dict(id='builtin:sliding-window', title='滑动窗口：非负和的最长连续段', category='基础算法',
                 summary='明确维护量、非负前提和计答案的时机；另验最短、计数与固定长度。', tags=['双指针','滑动窗口'],
                 language='cpp17', builtin=True, code='#include <bits/stdc++.h>\n#include <cassert>\nusing namespace std;\n'+LONGEST,
                 contestCode='#include <bits/stdc++.h>\n#include <cassert>\nusing namespace std;\n'+LONGEST_CONTEST,
                 example='int main(){assert(longest_window({3,1,2,1},5)==3);assert(longest_window({0,0},0)==2);assert(longest_window({},0)==0);}\n',
                 contestExample='int main(){assert(longest_window({3,1,2,1},5)==3);assert(longest_window({0,0},0)==2);assert(longest_window({},0)==0);}\n',
                 notes='数组非负、limit>=0，总和可存入 long long。O(n) 时间、O(1) 额外空间；不满足条件时先更换模型。',
                 contestNotes='非负数组、非负预算、long long 总和；最长和不超过预算的段。', practiceIds=[], learningPath='two-pointers')]
