## UVA1390 互联 Interconnect

原题：[UVA1390](https://www.luogu.com.cn/problem/UVA1390)

### 思路

道路的具体形状只影响当前连通块。把状态压成排序后的各块大小，随机选中不同块的概率为 size[i]·size[j]/C(n,2)，合并这两块；选中同一块的原地项移到等式左边。

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
