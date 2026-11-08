## P16943 火**印奔行者

原题：[P16943](https://www.luogu.com.cn/problem/P16943)

### 思路

删去 u、v 的连通块数是 deg[u]+deg[v]−1−[相邻]。最高两度数决定答案最多只差一；维护最高度点的次高度非邻居，普通加叶只更新这个证据，度数并列结束时才扫描度数桶重建。

### 复杂度

总时间 O(n log n) 摊还，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> parent(n + 1), degree(n + 1), head(n + 1), next(n + 1), previous(n + 1),
        count(n + 1);
    head[0] = 1;
    count[0] = 1;
    auto insert = [&](int v, int d) {
        degree[v] = d;
        previous[v] = 0;
        next[v] = head[d];
        if (head[d])
            previous[head[d]] = v;
        head[d] = v;
        count[d]++;
    };
    auto increase = [&](int v) {
        int d = degree[v], p = previous[v], q = next[v];
        if (p)
            next[p] = q;
        else
            head[d] = q;
        if (q)
            previous[q] = p;
        count[d]--;
        insert(v, d + 1);
    };
    auto adjacent = [&](int a, int b) { return parent[a] == b || parent[b] == a; };
    int top = 1, second = 0, previousUnique = 0, cachedSecond = 0, witness = 0;
    string output;
    output.reserve(8LL * n);
    for (int v = 2; v <= n; v++) {
        int p;
        cin >> p;
        parent[v] = p;
        increase(p);
        insert(v, 1);
        if (p != top) {
            if (degree[p] > degree[top]) {
                second = top;
                top = p;
            } else if (p != second && degree[p] > degree[second])
                second = p;
        }
        if (!second || degree[v] > degree[second])
            second = v;
        int D = degree[top], S = degree[second], answer;
        if (D == S) {
            answer = 2 * D - 1 - (count[D] == 2 && adjacent(top, second));
            previousUnique = 0;
        } else {
            if (previousUnique != top) {
                witness = 0;
                for (int u = head[S]; u; u = next[u])
                    if (!adjacent(top, u)) {
                        witness = u;
                        break;
                    }
            } else if (S != cachedSecond) {
                witness = p != top && degree[p] == S && !adjacent(top, p) ? p : 0;
            } else if (!witness) {
                if (p != top && degree[p] == S && !adjacent(top, p))
                    witness = p;
                if (S == 1 && !adjacent(top, v))
                    witness = v;
            }
            answer = D + S - 1 - (witness == 0);
            previousUnique = top;
            cachedSecond = S;
        }
        output += to_string(answer);
        output += v == n ? '\n' : ' ';
    }
    cout << output;

    return 0;
}
```

### 实现提醒

两点相邻额外减一；最高度至少三点必有非邻居；只有旧节点父亲度数增加。
