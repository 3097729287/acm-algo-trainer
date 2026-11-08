## UVA1390 互联 Interconnect

原题：[UVA1390](https://www.luogu.com.cn/problem/UVA1390)

### 从问题到算法

一条新道路是否推进连通性，只取决于两端属于哪些连通块，而与块内道路无关。大小相同的连通块也可互换，因此用排序后的大小列表作为记忆化状态。

设全部城市对数量为 total=C(n,2)，跨块对数 cross=Σ(i<j)size[i]size[j]。从状态 s 选中跨块 i、j 后合并为新状态 s′；选中同块则原地不动。期望满足 E=1+(total−cross)E/total+Σsize[i]size[j]E(s′)/total。

移项得 E=(total+Σsize[i]size[j]E(s′))/cross。只剩一个块时 E=0。每次有效转移都减少块数，不会形成递归环；n<=30 时不同整数分拆状态数量足够小。初始块用并查集求出，重复道路不重复合并。

### 复杂度

状态数至多整数分拆 p(n)，每状态 O(n³) 内处理合并与排序，空间 O(n·p(n))。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct DSU {
    vector<int> p, size;
    explicit DSU(int n) : p(n), size(n, 1) { iota(p.begin(), p.end(), 0); }
    int find(int x) {
        while (p[x] != x) {
            p[x] = p[p[x]];
            x = p[x];
        }
        return x;
    }
    bool join(int a, int b) {
        a = find(a);
        b = find(b);
        if (a == b)
            return false;
        if (size[a] < size[b])
            swap(a, b);
        p[b] = a;
        size[a] += size[b];
        return true;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    while (cin >> n >> m) {
        DSU d(n);
        while (m--) {
            int a, b;
            cin >> a >> b;
            d.join(a - 1, b - 1);
        }
        vector<int> state;
        for (int i = 0; i < n; i++)
            if (d.find(i) == i)
                state.push_back(d.size[i]);
        sort(state.begin(), state.end());
        map<vector<int>, double> memo;
        function<double(vector<int>)> solve = [&](vector<int> s) -> double {
            if (s.size() == 1)
                return 0;
            auto found = memo.find(s);
            if (found != memo.end())
                return found->second;
            double cross = 0, numerator = 1.0 * n * (n - 1) / 2;
            for (int i = 0; i < (int)s.size(); i++)
                for (int j = i + 1; j < (int)s.size(); j++) {
                    double weight = s[i] * s[j];
                    cross += weight;
                    vector<int> next;
                    for (int k = 0; k < (int)s.size(); k++)
                        if (k != i && k != j)
                            next.push_back(s[k]);
                    next.push_back(s[i] + s[j]);
                    sort(next.begin(), next.end());
                    numerator += weight * solve(next);
                }
            return memo[s] = numerator / cross;
        };
        cout << fixed << setprecision(9) << solve(state) << '\n';
    }

    return 0;
}
```

### 实现提醒

随机选的是不同城市，不是不同连通块；同块新路仍耗一年；输入到 EOF。
