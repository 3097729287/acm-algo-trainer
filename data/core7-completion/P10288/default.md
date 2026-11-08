## P10288 区间

原题：[P10288](https://www.luogu.com.cn/problem/P10288)

### 思路

把每个值的出现下标按顺序存入列表。查询 x 在 [l,r] 出现几次，就是位置列表中不超过 r 的个数减去小于 l 的个数。

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
