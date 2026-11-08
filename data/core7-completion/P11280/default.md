## P11280 Jom & Terry

原题：[P11280](https://www.luogu.com.cn/problem/P11280)

### 思路

从根广搜得到所有距离。Terry 到根的距离不大于 Jom 时输出 Terry，否则输出 Jom。相等时 Terry 先移动，能先到根。

### 复杂度

预处理时间 O(n+m)，每问 O(1)，空间 O(n+m)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m, r;
    cin >> n >> m >> r;
    r--;
    vector<vector<int>> g(n);
    while (m--) {
        int a, b;
        cin >> a >> b;
        a--;
        b--;
        g[a].push_back(b);
        g[b].push_back(a);
    }
    vector<int> d(n, -1), q = {r};
    d[r] = 0;
    for (int i = 0; i < (int)q.size(); i++)
        for (int u : g[q[i]])
            if (d[u] < 0) {
                d[u] = d[q[i]] + 1;
                q.push_back(u);
            }
    cout << "I'm here!\n";
    int Q;
    cin >> Q;
    while (Q--) {
        int a, b;
        cin >> a >> b;
        cout << (d[a - 1] <= d[b - 1] ? "Terry" : "Jom") << '\n';
    }

    return 0;
}
```

### 实现提醒

相等由先手获胜；先输出指定问候语；Jom 主动走到 Terry 位置不算捕获。
