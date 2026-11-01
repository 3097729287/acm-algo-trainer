"""Reference programs for the two newly authored rounds; no network submissions."""
from pathlib import Path
import datetime as dt
import shutil

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / 'data/contest-editorials/20261102'
ARCHIVE = Path('D:/Data/Code/题解')
ROUNDS = {
    'week168': ('牛客', '周赛', '168', 'https://ac.nowcoder.com/acm/contest/142559', 'BCDEFG'),
    'abc482': ('AtCoder', 'ABC', '482', 'https://atcoder.jp/contests/abc482', 'BCDEF'),
    'white139': ('牛客', '小白月赛', '139', 'https://ac.nowcoder.com/acm/contest/141882', 'BCDEF'),
}

PROGRAMS = {}
BRUTES = {}

PROGRAMS['week168', 'B'] = r'''
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m, ans = 0;
    cin >> n >> m;
    for (int i = 0; i < n; ++i) {
        string s;
        cin >> s;
        for (int j = 0; j < m; ++j) {
            // 用一个条件取边界的并集，角和单行、单列均只计一次。
            if (s[j] == '#' && (i == 0 || i == n - 1 || j == 0 || j == m - 1)) ++ans;
        }
    }
    cout << ans << '\n';
}
'''
BRUTES['week168', 'B'] = r'''
#include <bits/stdc++.h>
using namespace std;
int main(){int n,m;cin>>n>>m;vector<string>s(n);for(auto &x:s)cin>>x;
set<pair<int,int>> border;for(int i=0;i<n;i++){border.insert({i,0});border.insert({i,m-1});}
for(int j=0;j<m;j++){border.insert({0,j});border.insert({n-1,j});}
int ans=0;for(auto p:border)ans+=s[p.first][p.second]=='#';cout<<ans<<'\n';}
'''

PROGRAMS['week168', 'C'] = r'''
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    long long m, total = 0, prefix = 0;
    cin >> n >> m;
    vector<long long> a(n);
    for (auto &x : a) { cin >> x; total += x; }
    int ans = 0;
    for (long long x : a) {
        // 此时 prefix 是当前位置之前的和；两边都包含当前的 x。
        long long suffix = total - prefix;
        prefix += x;
        if ((prefix - suffix) % m == 0) ++ans;
    }
    cout << ans << '\n';
}
'''
BRUTES['week168', 'C'] = r'''
#include <bits/stdc++.h>
using namespace std;
int main(){int n;long long m;cin>>n>>m;vector<long long>a(n);for(auto &x:a)cin>>x;int ans=0;
for(int i=0;i<n;i++){long long l=0,r=0;for(int j=0;j<=i;j++)l+=a[j];for(int j=i;j<n;j++)r+=a[j];if((l-r)%m==0)ans++;}cout<<ans<<'\n';}
'''

PROGRAMS['week168', 'D'] = r'''
#include <bits/stdc++.h>
using namespace std;
vector<int> parent_link;
int find_next(int x) {
    int root = x;
    while (parent_link[root] != root) root = parent_link[root];
    // 路径压缩：以后直接跳到当前第一个可用位置。
    while (x != root) { int next = parent_link[x]; parent_link[x] = root; x = next; }
    return root;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<long long> a(n + 1);
    for (int i = 1; i <= n; ++i) cin >> a[i];
    parent_link.resize(n + 2);
    iota(parent_link.begin(), parent_link.end(), 0);
    int pos = 1;
    long long answer = 0;
    for (int turn = 0; turn < m; ++turn) {
        long long d;
        cin >> d;
        // d 按原来的 n 个格子计算，不能只在空格中数步数。
        int start = 1 + (pos - 1 + d) % n;
        pos = find_next(start);
        if (pos == n + 1) pos = find_next(1);
        answer += a[pos];
        parent_link[pos] = find_next(pos + 1);
    }
    cout << answer << ' ' << pos << '\n';
}
'''
BRUTES['week168', 'D'] = r'''
#include <bits/stdc++.h>
using namespace std;
int main(){int n,m;cin>>n>>m;vector<long long>a(n);for(auto &x:a)cin>>x;vector<bool>used(n);int p=0;long long ans=0;
for(int i=0;i<m;i++){long long d;cin>>d;p=(p+d)%n;while(used[p])p=(p+1)%n;used[p]=true;ans+=a[p];}cout<<ans<<' '<<p+1<<'\n';}
'''

PROGRAMS['week168', 'E'] = r'''
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int T;
    cin >> T;
    while (T--) {
        int n, m, k;
        cin >> n >> m >> k;
        vector<long long> a(n + 1), b(m + 1);
        vector<int> c(n + 1), d(m + 1);
        for (int i = 1; i <= n; ++i) { cin >> a[i] >> c[i]; a[i] += a[i - 1]; }
        for (int j = 1; j <= m; ++j) { cin >> b[j] >> d[j]; b[j] += b[j - 1]; }
        vector<vector<array<char, 2>>> can(n + 1, vector<array<char, 2>>(m + 1, {0, 0}));
        for (int i = 0; i <= n && i <= k; ++i) {
            for (int j = 0; j <= m && i + j <= k; ++j) {
                bool empty = i + j == 0;
                if (i < n && (empty || can[i][j][1] || (can[i][j][0] && c[i] == 0)))
                    can[i + 1][j][0] = 1;
                if (j < m && (empty || can[i][j][0] || (can[i][j][1] && d[j] == 0)))
                    can[i][j + 1][1] = 1;
            }
        }
        long long best = LLONG_MIN;
        for (int i = max(0, k - m); i <= min(n, k); ++i) {
            int j = k - i;
            // 相同前缀的总价值固定；DP 只需记录能否到达。
            if (k == 0 || can[i][j][0] || can[i][j][1]) best = max(best, a[i] + b[j]);
        }
        if (best == LLONG_MIN) cout << "IMPOSSIBLE\n";
        else cout << best << '\n';
    }
}
'''
BRUTES['week168', 'E'] = r'''
#include <bits/stdc++.h>
using namespace std;
int n,m,k;vector<long long>a,b;vector<int>c,d;long long ans;
void dfs(int i,int j,int last,long long sum){if(i+j==k){ans=max(ans,sum);return;}
if(i<n&&(last!=0||c[i-1]==0))dfs(i+1,j,0,sum+a[i]);
if(j<m&&(last!=1||d[j-1]==0))dfs(i,j+1,1,sum+b[j]);}
int main(){int T;cin>>T;while(T--){cin>>n>>m>>k;a.resize(n);b.resize(m);c.resize(n);d.resize(m);
for(int i=0;i<n;i++){cin>>a[i]>>c[i];}for(int i=0;i<m;i++){cin>>b[i]>>d[i];}ans=LLONG_MIN;dfs(0,0,2,0);
if(ans==LLONG_MIN)cout<<"IMPOSSIBLE\n";else cout<<ans<<'\n';}}
'''

PROGRAMS['week168', 'F'] = r'''
#include <bits/stdc++.h>
using namespace std;
const long long MOD = 1000000007;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int T;
    cin >> T;
    while (T--) {
        int n;
        cin >> n;
        vector<int> a(n);
        for (int &x : a) cin >> x;
        sort(a.begin(), a.end());
        vector<long long> rook(n + 1);
        rook[0] = 1;
        for (int i = 0; i < n; ++i) {
            // 倒序保证 rook[j-1] 仍属于处理当前朋友之前。
            for (int j = i + 1; j >= 1; --j) {
                long long choices = max(0, a[i] - j + 1);
                rook[j] = (rook[j] + rook[j - 1] * choices) % MOD;
            }
        }
        long long pairs = 1LL * n * (n - 1) / 2 % MOD;
        long long ans = (2 * rook[n - 2] - (n - 1) * rook[n - 1] + pairs * rook[n]) % MOD;
        cout << (ans + MOD) % MOD << '\n';
    }
}
'''
BRUTES['week168', 'F'] = r'''
#include <bits/stdc++.h>
using namespace std;
int main(){int T;cin>>T;while(T--){int n;cin>>n;vector<int>a(n),p(n);for(int &x:a)cin>>x;iota(p.begin(),p.end(),1);long long ans=0;
do{int bad=0;for(int i=0;i<n;i++)bad+=p[i]>a[i];ans+=bad==2;}while(next_permutation(p.begin(),p.end()));cout<<ans<<'\n';}}
'''

PROGRAMS['week168', 'G'] = r'''
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int T;
    cin >> T;
    while (T--) {
        int n, m, k;
        cin >> n >> m >> k;
        vector<long long> a(n + 1), b(m + 1);
        vector<int> ones_a(n + 1), ones_b(m + 1);
        for (int i = 1, flag; i <= n; ++i) {
            cin >> a[i] >> flag; a[i] += a[i - 1]; ones_a[i] = ones_a[i - 1] + flag;
        }
        for (int j = 1, flag; j <= m; ++j) {
            cin >> b[j] >> flag; b[j] += b[j - 1]; ones_b[j] = ones_b[j - 1] + flag;
        }
        long long best = LLONG_MIN;
        for (int i = max(0, k - m); i <= min(n, k); ++i) {
            int j = k - i;
            // 仅统计前缀内部的强制换堆；最后一件后无须继续取。
            int cut_a = i ? ones_a[i - 1] : 0;
            int cut_b = j ? ones_b[j - 1] : 0;
            if (cut_a <= j && cut_b <= i) best = max(best, a[i] + b[j]);
        }
        if (best == LLONG_MIN) cout << "IMPOSSIBLE\n";
        else cout << best << '\n';
    }
}
'''
BRUTES['week168', 'G'] = BRUTES['week168', 'E']

PROGRAMS['abc482', 'B'] = r'''
#include <bits/stdc++.h>
using namespace std;
int main() {
    vector<string> s(5);
    for (auto &row : s) cin >> row;
    int answer = 5;
    for (int i = 0; i < 5; ++i) {
        int row = 0, column = 0;
        for (int j = 0; j < 5; ++j) { row += s[i][j] == '.'; column += s[j][i] == '.'; }
        answer = min(answer, min(row, column));
    }
    int main_diagonal = 0, other_diagonal = 0;
    for (int i = 0; i < 5; ++i) { main_diagonal += s[i][i] == '.'; other_diagonal += s[i][4 - i] == '.'; }
    cout << min(answer, min(main_diagonal, other_diagonal)) << '\n';
}
'''
BRUTES['abc482', 'B'] = r'''
#include <bits/stdc++.h>
using namespace std;
int main(){vector<string>s(5);for(auto &x:s)cin>>x;int ans=5;
int di[]={1,0,1,1},dj[]={0,1,1,-1};for(int x=0;x<5;x++)for(int y=0;y<5;y++)for(int d=0;d<4;d++){
int ex=x+4*di[d],ey=y+4*dj[d];if(ex<0||ex>=5||ey<0||ey>=5)continue;int cost=0;for(int t=0;t<5;t++)cost+=s[x+t*di[d]][y+t*dj[d]]=='.';ans=min(ans,cost);}cout<<ans<<'\n';}
'''

PROGRAMS['abc482', 'C'] = r'''
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int H, W, N, Q;
    cin >> H >> W >> N >> Q;
    vector<int> rows(N), columns(N);
    for (int i = 0; i < N; ++i) cin >> rows[i] >> columns[i];
    sort(rows.begin(), rows.end());
    sort(columns.begin(), columns.end());
    while (Q--) {
        int type, l, r;
        cin >> type >> l >> r;
        const vector<int> &v = type == 1 ? rows : columns;
        // 第一个 > r 的位置，减去第一个 >= l 的位置。
        cout << upper_bound(v.begin(), v.end(), r) - lower_bound(v.begin(), v.end(), l) << '\n';
    }
}
'''
BRUTES['abc482', 'C'] = r'''
#include <bits/stdc++.h>
using namespace std;
int main(){int h,w,n,q;cin>>h>>w>>n>>q;vector<int>a(n),b(n);for(int i=0;i<n;i++)cin>>a[i]>>b[i];while(q--){int t,l,r,ans=0;cin>>t>>l>>r;for(int i=0;i<n;i++){int x=t==1?a[i]:b[i];ans+=l<=x&&x<=r;}cout<<ans<<'\n';}}
'''

PROGRAMS['abc482', 'D'] = r'''
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<long long> x(n);
    for (auto &v : x) cin >> v;
    for (int k = 0; k < n; ++k) {
        if (n == 1) { cout << 0 << '\n'; continue; }
        long long answer = LLONG_MAX;
        // 先感染左邻居，两位传播者再分别向两端移动。
        if (k > 0) answer = min(answer, max(x[k] - x[0], x[n - 1] - x[k - 1]) / 2);
        // 对称地考虑先感染右邻居。
        if (k + 1 < n) answer = min(answer, max(x[k + 1] - x[0], x[n - 1] - x[k]) / 2);
        cout << answer << '\n';
    }
}
'''
BRUTES['abc482', 'D'] = r'''
#include <bits/stdc++.h>
using namespace std;
// 小规模物理模拟：每个整时刻枚举所有人的左右移动与接触传播。
int main(){int n;cin>>n;vector<int>x(n);for(int &v:x)cin>>v;
if(n==1){cout<<0<<'\n';return 0;}
int base=x.back()+3;for(int first=0;first<n;first++){
set<pair<vector<int>,int>> states;states.insert({x,1<<first});int answer=-1;
for(int t=1;t<=x.back()/2+1&&answer==-1;t++){
set<pair<vector<int>,int>> next;
for(const auto &state:states)for(int moves=0;moves<(1<<n);moves++){
vector<int>p=state.first;bool valid=true;for(int i=0;i<n;i++){p[i]+=(moves>>i&1)?1:-1;if(p[i]<0||p[i]>=base)valid=false;}
if(!valid){continue;}int mask=state.second;
for(int repeat=0;repeat<n;repeat++)for(int i=0;i<n;i++)for(int j=0;j<n;j++)if(p[i]==p[j]&&(mask>>i&1))mask|=1<<j;
if(mask==(1<<n)-1){answer=t;break;}next.insert({p,mask});
}states.swap(next);}
cout<<answer<<'\n';}}
'''

PROGRAMS['abc482', 'E'] = r'''
#include <bits/stdc++.h>
using namespace std;
int farthest(int start, const vector<vector<int>> &g, vector<int> &dist, vector<int> &parent) {
    int n = g.size();
    dist.assign(n, -1); parent.assign(n, -1);
    queue<int> q;
    q.push(start); dist[start] = 0;
    int best = start;
    while (!q.empty()) {
        int v = q.front(); q.pop();
        if (dist[v] > dist[best]) best = v;
        for (int u : g[v]) if (dist[u] == -1) {
            dist[u] = dist[v] + 1; parent[u] = v; q.push(u);
        }
    }
    return best;
}
vector<int> endpoint_colors(int root, int blocked, int depth, int target,
                            const vector<vector<int>> &g, const vector<int> &color) {
    vector<int> result;
    vector<array<int, 3>> st = {{root, blocked, depth}};
    while (!st.empty()) {
        auto item = st.back(); st.pop_back();
        int v = item[0], parent = item[1], d = item[2];
        if (d == target) { result.push_back(color[v]); continue; }
        for (int u : g[v]) if (u != parent) st.push_back({u, v, d + 1});
    }
    return result;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<vector<int>> g(n);
    for (int i = 1, u, v; i < n; ++i) { cin >> u >> v; --u; --v; g[u].push_back(v); g[v].push_back(u); }
    vector<int> color(n);
    for (int &c : color) cin >> c;
    vector<int> dist, parent;
    int a = farthest(0, g, dist, parent);
    int b = farthest(a, g, dist, parent);
    int diameter = dist[b], radius = diameter / 2;
    vector<int> path;
    for (int v = b; v != -1; v = parent[v]) path.push_back(v);
    vector<long long> seen(n + 1);
    long long answer = 0;
    if (diameter % 2 == 1) {
        int left = path[radius], right = path[radius + 1];
        for (int c : endpoint_colors(left, right, 0, radius, g, color)) ++seen[c];
        for (int c : endpoint_colors(right, left, 0, radius, g, color)) answer += seen[c];
    } else {
        int center = path[radius];
        for (int u : g[center]) {
            vector<int> group = endpoint_colors(u, center, 1, radius, g, color);
            // 当前分支只与先前分支配对，避免同分支误计。
            for (int c : group) answer += seen[c];
            for (int c : group) ++seen[c];
        }
    }
    cout << answer << '\n';
}
'''
BRUTES['abc482', 'E'] = r'''
#include <bits/stdc++.h>
using namespace std;
int main(){int n;cin>>n;vector<vector<int>>d(n,vector<int>(n,n+1));for(int i=0;i<n;i++)d[i][i]=0;
for(int i=1,u,v;i<n;i++){cin>>u>>v;--u;--v;d[u][v]=d[v][u]=1;}vector<int>c(n);for(int &v:c)cin>>v;
for(int k=0;k<n;k++)for(int i=0;i<n;i++)for(int j=0;j<n;j++)d[i][j]=min(d[i][j],d[i][k]+d[k][j]);
int diam=0;for(auto &row:d)for(int v:row)diam=max(diam,v);long long ans=0;for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)ans+=c[i]==c[j]&&d[i][j]==diam;cout<<ans<<'\n';}
'''

PROGRAMS['abc482', 'F'] = r'''
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    long long n;
    int m;
    cin >> n >> m;
    vector<pair<int, int>> factors;
    for (long long p = 2; p * p <= n; p += (p == 2 ? 1 : 2)) {
        if (n % p != 0) continue;
        int exponent = 0;
        while (n % p == 0) { n /= p; ++exponent; }
        factors.push_back({int(p % m), exponent});
    }
    if (n > 1) factors.push_back({int(n % m), 1});
    if (factors.empty()) {
        for (int r = 0; r < m; ++r) cout << (r == 1 % m ? 1 : -1) << '\n';
        return 0;
    }
    int layers = factors.size(), inf = 1000000000;
    vector<int> dist(layers * m, inf);
    vector<char> done(layers * m);
    deque<int> q;
    dist[1 % m] = 0; q.push_back(1 % m);
    while (!q.empty()) {
        int id = q.front(); q.pop_front();
        if (done[id]) continue;
        done[id] = 1;
        int layer = id / m, residue = id % m;
        int next_layer = (layer + 1) % layers;
        int cost = layer == 0;
        long long next_residue = residue;
        for (int e = 0; e <= factors[layer].second; ++e) {
            int to = next_layer * m + int(next_residue);
            if (dist[id] + cost < dist[to]) {
                dist[to] = dist[id] + cost;
                // 开始新一轮花费一，其余因子层不增加轮数。
                if (cost == 0) q.push_front(to); else q.push_back(to);
            }
            next_residue = next_residue * factors[layer].first % m;
        }
    }
    // 只读回到第零层的完整轮次；t 必须是正整数。
    for (int r = 0; r < m; ++r) cout << (dist[r] == inf ? -1 : max(1, dist[r])) << '\n';
}
'''
BRUTES['abc482', 'F'] = r'''
#include <bits/stdc++.h>
using namespace std;
// 直接枚举 N 的每个约数，以乘一个约数作为一条普通 BFS 边。
int main(){long long n;int m;cin>>n>>m;vector<long long>divs;for(long long d=1;d*d<=n;d++)if(n%d==0){divs.push_back(d);if(d*d!=n)divs.push_back(n/d);}
vector<int>dist(m,-1);queue<int>q;dist[1%m]=0;q.push(1%m);while(!q.empty()){int r=q.front();q.pop();for(long long d:divs){int to=r*(d%m)%m;if(dist[to]<0){dist[to]=dist[r]+1;q.push(to);}}}
for(int d:dist)cout<<(d<0?-1:max(1,d))<<'\n';}
'''

def normalized(code):
    return code.strip() + '\n'

def write_programs():
    for (round_key, letter), code in PROGRAMS.items():
        platform, series, number, _, letters = ROUNDS[round_key]
        folder = ARCHIVE / platform / series / number / (letters[0] + '-' + letters[-1]) / letter
        folder.mkdir(parents=True, exist_ok=True)
        portable = CONTENT / round_key / 'programs' / letter
        portable.mkdir(parents=True, exist_ok=True)
        for name, body in [(letter.lower()+'.cpp', code), (letter.lower()+'_brute.cpp', BRUTES[round_key,letter])]:
            body=normalized(body)
            for target in [folder/name, portable/name]:
                if target.exists() and target.read_text('utf8') != body:
                    backup=Path.home()/'.dsh/backups/three-contests-20261102'/dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f')/round_key/letter/target.name
                    backup.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(target,backup)
                target.write_text(body, encoding='utf8', newline='\n')

if __name__ == '__main__':
    write_programs()
    print('Wrote',len(PROGRAMS),'reference programs and independent baselines.')
