## P16943 火**印奔行者

原题：[P16943](https://www.luogu.com.cn/problem/P16943)

### 从问题到算法

树删去两点后，用剩余点数减剩余边数，得到 deg[u]+deg[v]−1−[u,v相邻]。

若最高度 D 至少三点达到，其中必有不相邻一对，否则形成三角形，答案为 2D−1。只有两点达到时检查两点是否相邻。若最高度点唯一为 u，次高度为 S，最优一定包含 u：不含 u 的得分至多 2S−1，而 u 配次高度点至少 D+S−2≥2S−1。因此只需判断是否存在度数 S 且不邻接 u 的点，答案为 D+S−1 或 D+S−2。

每次加叶只增加父亲度数，并新增度一节点。用链表度数桶和两个候选编号维护最高两度数。最高点 u 连续保持唯一时，若次高度不变，旧非邻居证据仍有效，只需检查新入桶的父亲或新叶；若次高度升高，新次高桶只包含本次增度的父亲，直接判断。

只有从并列最高变成唯一最高时才扫描次高度桶寻找证据。此时 S=D−1，扫描至多 min(桶大小,D+1) 个点；桶大小又受树度数和限制为 O(n/(D−1))。这样的重建每个全局最大度至多一次，合计 O(n log n)。相邻关系可直接用创建时父亲数组判断，后续不会改变。

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
