## P2855 River Hopscotch S

原题：[P2855](https://www.luogu.com.cn/problem/P2855)

### 思路

给定最小跳距 D，从起点开始尽量保留最靠左的可用石头；与上个保留点距离不足 D 的石头移走。所需移走数不超过 M 时 D 可行，二分最大可行值。

### 复杂度

时间 O(n log L+n log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int length, n, m;
    cin >> length >> n >> m;
    vector<int> a(n + 1);
    for (int i = 0; i < n; i++)
        cin >> a[i];
    sort(a.begin(), a.begin() + n);
    a[n] = length;
    auto ok = [&](int gap) {
        int removed = 0, last = 0;
        for (int x : a)
            if (x - last < gap)
                removed++;
            else
                last = x;
        return removed <= m;
    };
    int l = 0, r = length;
    while (l < r) {
        int mid = l + (r - l + 1) / 2;
        if (ok(mid))
            l = mid;
        else
            r = mid - 1;
    }
    cout << l << '\n';

    return 0;
}
```

### 实现提醒

终点必须保留；最后一段冲突需要计一次删除；求最大可行值。
