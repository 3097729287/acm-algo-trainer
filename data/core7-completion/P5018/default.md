## P5018 对称二叉树

原题：[P5018](https://www.luogu.com.cn/problem/P5018)

### 思路

自底向上为 (点权,左子树编号,右子树编号) 分配唯一编号，同时计算交换左右后的镜像编号。两编号相等时，该子树对称；取其中最大节点数。

### 复杂度

时间 O(n log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> w(n + 1), l(n + 1), r(n + 1), id(n + 1), mirror(n + 1), size(n + 1);
    for (int i = 1; i <= n; i++)
        cin >> w[i];
    for (int i = 1; i <= n; i++) {
        cin >> l[i] >> r[i];
        l[i] = max(l[i], 0);
        r[i] = max(r[i], 0);
    }
    vector<int> order = {1};
    for (int i = 0; i < (int)order.size(); i++) {
        int v = order[i];
        if (l[v])
            order.push_back(l[v]);
        if (r[v])
            order.push_back(r[v]);
    }
    map<tuple<int, int, int>, int> ids;
    auto intern = [&](int value, int a, int b) {
        auto key = make_tuple(value, a, b);
        auto it = ids.find(key);
        if (it != ids.end())
            return it->second;
        int index = ids.size() + 1;
        ids.emplace(key, index);
        return index;
    };
    int ans = 0;
    for (int i = n - 1; i >= 0; i--) {
        int v = order[i];
        id[v] = intern(w[v], id[l[v]], id[r[v]]);
        mirror[v] = intern(w[v], mirror[r[v]], mirror[l[v]]);
        size[v] = size[l[v]] + size[r[v]] + 1;
        if (id[v] == mirror[v])
            ans = max(ans, size[v]);
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

孩子 -1 转为空树 0；点权也属于结构；使用真实遍历顺序倒序处理。
