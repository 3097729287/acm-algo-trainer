## P2441 角色属性树

原题：[P2441](https://www.luogu.com.cn/problem/P2441)

### 从问题到算法

gcd 大于一当且仅当两个属性含有共同质因子。静态 DFS 进入 u 前，last[p] 记录祖先链最近的含 p 结点，对 u 的不同质因子取最深 last 即为答案；随后令这些 last 指向 u，退出时恢复旧值。

修改次数最多五十，没必要维护通用动态树。将修改标记为 dirty，下一次查询前完整重建一次，其间多次修改合并处理；一次重建后所有查询常数时间。

所有初值和修改值预先分解并缓存，把质数离散成小编号，重建时只访问数组，不重复因数分解或哈希。先用确定性的三十二位 Miller–Rabin 快速识别质数，其余用四万六千以内质数试除。原树与 DFS 进入退出序固定，重建用显式事件序列避免深链递归。

### 复杂度

设不同值数 U、每值不同质因子最多 F、修改数 C≤50，重建总计 O((C+1)nF)，试除最坏 O(U√A/log A)；空间 O(nF+k+UF)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

long long pow32(long long a, long long d, long long mod) {
    long long r = 1;
    for (; d; d >>= 1, a = a * a % mod)
        if (d & 1)
            r = r * a % mod;
    return r;
}
bool prime32(int x) {
    if (x < 2)
        return false;
    for (int p : {2, 3, 5, 7, 11}) {
        if (x % p == 0)
            return x == p;
    }
    int s = 0;
    long long d = x - 1;
    while (!(d & 1)) {
        d >>= 1;
        s++;
    }
    for (int a : {2, 3, 5, 7}) {
        long long y = pow32(a, d, x);
        if (y == 1 || y == x - 1)
            continue;
        bool ok = false;
        for (int i = 1; i < s; i++) {
            y = y * y % x;
            if (y == x - 1) {
                ok = true;
                break;
            }
        }
        if (!ok)
            return false;
    }
    return true;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, k;
    cin >> n >> k;
    vector<int> a(n);
    for (int &x : a)
        cin >> x;
    vector<vector<int>> children(n);
    vector<int> parent(n, -1);
    for (int i = 1; i < n; i++) {
        int x, y;
        cin >> x >> y;
        x--;
        y--;
        children[x].push_back(y);
        parent[y] = x;
    }
    struct Op {
        int type, u, x;
    };
    vector<Op> ops(k);
    vector<int> values = a;
    for (auto &op : ops) {
        cin >> op.type >> op.u;
        op.u--;
        op.x = 0;
        if (op.type == 2) {
            cin >> op.x;
            values.push_back(op.x);
        }
    }
    vector<int> primes;
    vector<bool> composite(46341);
    for (int i = 2; i <= 46340; i++)
        if (!composite[i]) {
            primes.push_back(i);
            if (1LL * i * i <= 46340)
                for (int j = i * i; j <= 46340; j += i)
                    composite[j] = 1;
        }
    unordered_map<int, int> profileId, primeId;
    vector<vector<int>> profiles;
    for (int value : values)
        if (!profileId.count(value)) {
            int x = value;
            vector<int> factor;
            if (prime32(x))
                factor.push_back(x);
            else {
                for (int p : primes) {
                    if (1LL * p * p > x)
                        break;
                    if (x % p == 0) {
                        factor.push_back(p);
                        while (x % p == 0)
                            x /= p;
                        if (prime32(x))
                            break;
                    }
                }
                if (x > 1)
                    factor.push_back(x);
            }
            vector<int> ids;
            for (int p : factor) {
                if (!primeId.count(p))
                    primeId[p] = primeId.size();
                ids.push_back(primeId[p]);
            }
            profileId[value] = profiles.size();
            profiles.push_back(move(ids));
        }
    vector<int> current(n);
    for (int i = 0; i < n; i++)
        current[i] = profileId[a[i]];
    int root = find(parent.begin(), parent.end(), -1) - parent.begin();
    vector<int> depth(n), events, order = {root};
    for (int i = 0; i < n; i++)
        for (int u : children[order[i]]) {
            depth[u] = depth[order[i]] + 1;
            order.push_back(u);
        }
    vector<pair<int, bool>> stack = {{root, false}};
    while (!stack.empty()) {
        auto [v, leave] = stack.back();
        stack.pop_back();
        events.push_back(leave ? -v - 1 : v + 1);
        if (!leave) {
            stack.push_back({v, true});
            for (int u : children[v])
                stack.push_back({u, false});
        }
    }
    vector<int> answer(n), last(primeId.size(), -1);
    vector<array<int, 10>> saved(n);
    bool dirty = true;
    auto rebuild = [&]() {
        fill(last.begin(), last.end(), -1);
        for (int event : events) {
            int v = abs(event) - 1;
            auto &f = profiles[current[v]];
            if (event > 0) {
                int best = -1;
                for (int j = 0; j < (int)f.size(); j++) {
                    int p = f[j], u = last[p];
                    if (u >= 0 && (best < 0 || depth[u] > depth[best]))
                        best = u;
                    saved[v][j] = u;
                    last[p] = v;
                }
                answer[v] = best;
            } else
                for (int j = 0; j < (int)f.size(); j++)
                    last[f[j]] = saved[v][j];
        }
        dirty = false;
    };
    for (auto op : ops)
        if (op.type == 2) {
            current[op.u] = profileId[op.x];
            dirty = true;
        } else {
            if (dirty)
                rebuild();
            cout << (answer[op.u] < 0 ? -1 : answer[op.u] + 1) << '\n';
        }

    return 0;
}
```

### 实现提醒

只找严格祖先，先查询 last 再写自己；重复质因子只算一次；修改后查询前才重建。
