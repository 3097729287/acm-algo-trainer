## P10288 区间

原题：[P10288](https://www.luogu.com.cn/problem/P10288)

### 从问题到算法

序列不会修改，同一数值的出现位置完全固定。读取第 i 个数 x 时，把 i 追加到 x 的位置列表；由于按下标递增读取，每个列表天然有序。

例如 x 出现在位置 2、5、8，查询 [3,8] 时，合法位置是 5、8。lower_bound(l) 找到第一个不小于 l 的位置，upper_bound(r) 找到第一个大于 r 的位置，它们之间的元素恰好落在闭区间内，迭代器相减即为次数。

数值可达十亿，不能按最大值开数组。用 map 将数值映射到 vector。查不到 x 时直接回答零，避免为大量未出现的查询值创建无用列表。每组测试都重新建立映射。

### 复杂度

建表 O(n log n)，每次查询 O(log n)，空间 O(n)。

### 参考代码

```cpp
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
        map<int, vector<int>> pos;
        for (int i = 1; i <= n; i++) {
            int x;
            cin >> x;
            pos[x].push_back(i);
        }
        int q;
        cin >> q;
        while (q--) {
            int l, r, x;
            cin >> l >> r >> x;
            auto it = pos.find(x);
            if (it == pos.end())
                cout << 0 << '\n';
            else {
                auto &v = it->second;
                cout << upper_bound(v.begin(), v.end(), r) - lower_bound(v.begin(), v.end(), l)
                     << '\n';
            }
        }
    }

    return 0;
}
```

### 实现提醒

查询是闭区间；不存在的值回答 0；每组清空位置表。
