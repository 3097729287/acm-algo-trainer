## P11280 Jom & Terry

原题：[P11280](https://www.luogu.com.cn/problem/P11280)

### 从问题到算法

记两人到根距离为 da、db。若 da≤db，Terry 每步沿最短路前进。在 Terry 的第 t 步之前，Jom 到根的距离至少是 db−t+1，而 Terry 要走到的点距根为 da−t，后者严格更小，因此不会走进 Jom 所在位置，最终能先到根。

若 da>db，Jom 每步沿最短路到根，然后一直停在那里。Terry 无论走哪条路都至少需要 da 步，无法在 Jom 之前到根，此后根被占据，Terry 也不能进入。因此这个判据充分且必要。

重边与自环不会改变 BFS 的正确性。开头按题目要求输出固定的 I'm here!，再回答全部询问。

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
