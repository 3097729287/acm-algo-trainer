## UVA1665 岛屿 Islands

原题：[UVA1665](https://www.luogu.com.cn/problem/UVA1665)

### 思路

把格子按高度降序、询问按海平面降序处理。高于当前海平面的格子才是陆地，逐个激活并与四邻陆地合并，维护连通块数。

### 复杂度

时间 O(nm log(nm)+T log T)，空间 O(nm+T)。

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

    int tests;
    cin >> tests;
    while (tests--) {
        int n, m;
        cin >> n >> m;
        int count = n * m;
        vector<int> height(count), order(count);
        for (int &x : height)
            cin >> x;
        iota(order.begin(), order.end(), 0);
        sort(order.begin(), order.end(), [&](int a, int b) { return height[a] > height[b]; });
        int q;
        cin >> q;
        vector<pair<int, int>> queries(q);
        for (int i = 0; i < q; i++) {
            cin >> queries[i].first;
            queries[i].second = i;
        }
        sort(queries.rbegin(), queries.rend());
        DSU d(count);
        vector<char> active(count);
        vector<int> answer(q);
        int position = 0, islands = 0;
        for (auto [water, id] : queries) {
            while (position < count && height[order[position]] > water) {
                int v = order[position++], x = v / m, y = v % m;
                active[v] = 1;
                islands++;
                for (auto [dx, dy] : vector<pair<int, int>>{{1, 0}, {-1, 0}, {0, 1}, {0, -1}}) {
                    int a = x + dx, b = y + dy;
                    if (a >= 0 && a < n && b >= 0 && b < m && active[a * m + b] &&
                        d.join(v, a * m + b))
                        islands--;
                }
            }
            answer[id] = islands;
        }
        for (int i = 0; i < q; i++)
            cout << answer[i] << (i + 1 == q ? '\n' : ' ');
    }

    return 0;
}
```

### 实现提醒

海水能进入所有低格，无需从边界灌水；严格高于水位才激活；使用四邻域。
