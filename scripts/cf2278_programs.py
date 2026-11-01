"""Independent reference programs and exhaustive small-instance baselines."""
from pathlib import Path
import datetime as dt
import shutil

ROOT=Path(__file__).resolve().parents[1]
CONTENT=ROOT/'data/contest-editorials/div3-1131'
ARCHIVE=Path('D:/Data/Code/题解/Codeforces/Div.3/1131')
OUT=ROOT/'.backups/div3-1131'
LETTERS='ABCDEFG'
META={
 'A':('Fraction and Six','模拟',800,[]),
 'B':('Stakes and Shapes','构造[主] + 贪心',800,['integer']),
 'C':('Math and Physics','贪心',1100,['vector','integer']),
 'D':('Lock and Unlock','贪心[主] + 排序',1600,['vector','integer']),
 'E':('Swap and Negate','贪心[主] + 排序',1700,['vector','integer']),
 'F':('Modulo and Counting','线性 DP[主] + 前缀和 + 取模与同余',2100,['vector','prefix','integer']),
 'G':('0s and 1s','位运算[主] + DFS',2100,['bitwise','vector','integer']),
}

PROGRAMS={
'A':r'''
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n, m;
        string p, q;
        cin >> n >> m >> p >> q;
        int count[26] = {};
        for (char c : p) ++count[c - 'a'];
        for (char c : q) --count[c - 'a'];
        // 再扣掉目标，所有差值为零才表示分母清空、分子恰好剩 six。
        for (char c : string("six")) --count[c - 'a'];
        bool ok = true;
        for (int value : count) if (value != 0) ok = false;
        cout << (ok ? "YES" : "NO") << '\n';
    }
}
''',
'B':r'''
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int x, y, z;
        cin >> x >> y >> z;
        char move;
        // 始终克制 Alice 出现最多的手势，赢局数便不会小于输局数。
        if (x >= y && x >= z) move = 'P';
        else if (y >= z) move = 'R';
        else move = 'S';
        cout << string(x + y + z, move) << '\n';
    }
}
''',
'C':r'''
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<long long> a(n);
        long long sum = 0;
        bool movable = false, inner = false;
        for (int i = 0; i < n; ++i) {
            cin >> a[i]; sum += a[i];
            if (a[i] >= 2) {
                movable = true;
                if (i > 0 && i + 1 < n) inner = true;
            }
        }
        if (!movable) cout << -1 << '\n';
        else if (inner) cout << sum - 1 << '\n';
        else cout << a.front() + a.back() - 1 << '\n';
    }
}
''',
'D':r'''
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<long long> a(n);
        for (auto &v : a) cin >> v;
        sort(a.begin(), a.end());
        long long median = a[n / 2], cost = 0;
        // 中位数两侧的距离之和等于按每个相邻差付出的最小锁定成本。
        for (long long v : a) cost += (v >= median ? v - median : median - v);
        cout << cost << ' ' << a.back() - a.front() << '\n';
    }
}
''',
'E':r'''
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<long long> b(n);
        for (int i = 0; i < n; ++i) {
            cin >> b[i];
            if (i % 2 == 1) b[i] = -b[i];
        }
        // 原操作恰好变成 b 的相邻交换，因此 b 可任意重排。
        sort(b.begin(), b.end());
        long long answer = 0;
        for (int i = 0; i < n; ++i) {
            if (i < n / 2) answer -= b[i];
            else answer += b[i];
        }
        cout << answer << '\n';
    }
}
''',
'F':r'''
#include <bits/stdc++.h>
using namespace std;
const int MOD = 998244353;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n, m;
        cin >> n >> m;
        int maximum = m + 2;
        vector<int> dp(maximum + 1), next_dp(maximum + 1), prefix(maximum + 1);
        dp[maximum] = 1;
        int answer = 0;
        for (int length = 1; length <= n; ++length) {
            // 长度不足 n 时，结束于 2 的前缀以全 1 后缀唯一补齐。
            answer += dp[2];
            if (answer >= MOD) answer -= MOD;
            if (length == n) break;
            prefix[0] = 0;
            for (int v = 1; v <= maximum; ++v) {
                prefix[v] = prefix[v - 1] + dp[v];
                if (prefix[v] >= MOD) prefix[v] -= MOD;
            }
            for (int v = 2; v <= maximum; ++v) {
                // 合法前驱 u 满足 v <= u < 2v。
                int hi = min(maximum, 2 * v - 1);
                next_dp[v] = prefix[hi] - prefix[v - 1];
                if (next_dp[v] < 0) next_dp[v] += MOD;
            }
            dp.swap(next_dp);
        }
        cout << answer << '\n';
    }
}
''',
'G':r'''
#include <bits/stdc++.h>
using namespace std;
const long long MOD = 998244353;
struct State { int node, parent, depth, carry; };
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<vector<int>> graph(n);
        for (int i = 1, u, v; i < n; ++i) {
            cin >> u >> v; --u; --v;
            graph[u].push_back(v); graph[v].push_back(u);
        }
        string x, y;
        cin >> x >> y;
        vector<int> bit(n, -1);
        vector<long long> power(n, 1);
        for (int i = 1; i < n; ++i) power[i] = power[i - 1] * 2 % MOD;
        vector<State> stack = {{0, -1, 0, 0}};
        bool possible = true;
        long long answer = 0;
        while (!stack.empty()) {
            State current = stack.back(); stack.pop_back();
            int u = current.node, depth = current.depth;
            int xb = x[u] - '0', yb = y[u] - '0';
            int needed = xb ^ yb ^ current.carry;
            if (bit[depth] == -1) {
                bit[depth] = needed;
                answer = (answer + needed * power[depth]) % MOD;
            } else if (bit[depth] != needed) {
                possible = false; break;
            }
            // 同一深度共用 K 的这一位，但每条根路径的进位可以不同。
            int next_carry = (xb + needed + current.carry) / 2;
            for (int v : graph[u]) if (v != current.parent)
                stack.push_back({v, u, depth + 1, next_carry});
        }
        cout << (possible ? answer : -1) << '\n';
    }
}
''',
}

BRUTES={
'A':r'''
#include <bits/stdc++.h>
using namespace std;
int main() {
    int t;
    cin >> t;
    while (t--) {
        int n, m;
        string p, q;
        cin >> n >> m >> p >> q;
        bool ok = true;
        for (char c : q) {
            size_t pos = p.find(c);
            if (pos == string::npos) { ok = false; break; }
            p.erase(pos, 1);
        }
        sort(p.begin(), p.end());
        cout << (ok && p == "isx" ? "YES" : "NO") << '\n';
    }
}
''',
'B':r'''
#include <bits/stdc++.h>
using namespace std;
int score(char b,char a){if(b==a)return 0;return ((b=='R'&&a=='S')||(b=='S'&&a=='P')||(b=='P'&&a=='R'))?1:-1;}
bool ok(const string &bob,vector<int>&a,int at,int sum){if(at==(int)bob.size())return sum>=0;string moves="RSP";for(int i=0;i<3;i++){if(a[i]==0)continue;--a[i];bool good=ok(bob,a,at+1,sum+score(bob[at],moves[i]));++a[i];if(!good)return false;}return true;}
bool search(string &s,int n,vector<int>&a){if((int)s.size()==n)return ok(s,a,0,0);for(char c:string("RSP")){s+=c;if(search(s,n,a))return true;s.pop_back();}return false;}
int main(){int t;cin>>t;while(t--){vector<int>a(3);cin>>a[0]>>a[1]>>a[2];int n=a[0]+a[1]+a[2];string s;search(s,n,a);cout<<s<<'\n';}}
''',
'C':r'''
#include <bits/stdc++.h>
using namespace std;
map<vector<int>,int> memo;
int solve(vector<int> a){if(a.size()==1)return a[0];if(memo.count(a))return memo[a];int best=-1;
for(int i=0;i<(int)a.size();++i){for(int left=1;left<a[i];++left){vector<int>b=a;if(i>0)b[i-1]+=left;if(i+1<(int)a.size())b[i+1]+=a[i]-left;b.erase(b.begin()+i);best=max(best,solve(b));}}
return memo[a]=best;}
int main(){int t;cin>>t;while(t--){int n;cin>>n;vector<int>a(n);for(int &v:a)cin>>v;memo.clear();cout<<solve(a)<<'\n';}}
''',
'D':r'''
#include <bits/stdc++.h>
using namespace std;
// 直接枚举锁定子集和方向，在平移等价类上做字典序最短路。
int main(){int t;cin>>t;while(t--){int n;cin>>n;vector<int>a(n);for(int &v:a)cin>>v;int low=*min_element(a.begin(),a.end());for(int &v:a)v-=low;
using Cost=pair<int,int>;using Entry=pair<Cost,vector<int>>;map<vector<int>,Cost>dist;priority_queue<Entry,vector<Entry>,greater<Entry>>q;dist[a]={0,0};q.push({{0,0},a});
while(!q.empty()){auto entry=q.top();q.pop();Cost cost=entry.first;auto current=entry.second;if(dist[current]!=cost)continue;if(*max_element(current.begin(),current.end())==0){cout<<cost.first<<' '<<cost.second<<'\n';break;}
for(int mask=1;mask<(1<<n)-1;mask++)for(int dir:{-1,1}){auto next=current;for(int i=0;i<n;i++)if(!(mask>>i&1))next[i]+=dir;int mn=*min_element(next.begin(),next.end());for(int &v:next)v-=mn;Cost nc={cost.first+__builtin_popcount((unsigned)mask),cost.second+1};if(!dist.count(next)||nc<dist[next]){dist[next]=nc;q.push({nc,next});}}}
}}
''',
'E':r'''
#include <bits/stdc++.h>
using namespace std;
int main(){int t;cin>>t;while(t--){int n;cin>>n;vector<int>a(n);for(int &v:a)cin>>v;set<vector<int>>seen;queue<vector<int>>q;seen.insert(a);q.push(a);long long best=LLONG_MIN;
while(!q.empty()){auto v=q.front();q.pop();long long sum=0;for(int x:v)sum+=x;best=max(best,sum);for(int i=0;i+1<n;i++){auto w=v;w[i]=-v[i+1];w[i+1]=-v[i];if(seen.insert(w).second)q.push(w);}}cout<<best<<'\n';}}
''',
'F':r'''
#include <bits/stdc++.h>
using namespace std;
int n,m;long long answer;
void dfs(int length,int previous,int sum){if(length==n){answer+=sum==m;return;}for(int v=1;v<=previous;v++){int next=sum+previous%v;if(next<=m)dfs(length+1,v,next);}}
int main(){int t;cin>>t;while(t--){cin>>n>>m;answer=0;for(int first=1;first<=m+2;first++)dfs(1,first,0);cout<<answer%998244353<<'\n';}}
''',
'G':r'''
#include <bits/stdc++.h>
using namespace std;
int main(){int t;cin>>t;while(t--){int n;cin>>n;vector<vector<int>>g(n),children(n);for(int i=1,u,v;i<n;i++){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}vector<int>parent(n,-1),order={0};parent[0]=0;for(int at=0;at<n;at++){int u=order[at];for(int v:g[u])if(v!=parent[u]){parent[v]=u;children[u].push_back(v);order.push_back(v);}}
string x,y;cin>>x>>y;set<string>seen;int pulses=0,answer=-1;while(seen.insert(x).second){if(x==y){answer=pulses;break;}vector<int>q={0};for(int at=0;at<(int)q.size();at++){int u=q[at];if(x[u]=='0')x[u]='1';else{x[u]='0';for(int v:children[u])q.push_back(v);}}++pulses;}cout<<answer<<'\n';}}
''',
}

def put(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.read_text('utf8')!=text:
        saved=Path.home()/'.dsh/backups/div3-1131'/dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f')/path.parent.name/path.name
        saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,saved)
    path.write_text(text,encoding='utf8',newline='\n')

def main():
    for letter in LETTERS:
        for name,code in [(letter.lower()+'.cpp',PROGRAMS[letter]),(letter.lower()+'_brute.cpp',BRUTES[letter])]:
            for folder in [ARCHIVE/('A-G' if letter=='A' else 'B-G')/letter,CONTENT/'programs'/letter]:put(folder/name,code.strip()+'\n')
    print('Wrote seven references and seven independent baselines.')

if __name__=='__main__':main()
