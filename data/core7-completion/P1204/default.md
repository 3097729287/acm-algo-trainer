## P1204 挤牛奶 Milking Cows

原题：[P1204](https://www.luogu.com.cn/problem/P1204)

### 思路

把工作区间按左端点排序，维护当前连续覆盖的左右端点。相交或首尾相接就合并，出现空隙时结算最长忙碌和空闲时间。

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
    vector<pair<int, int>> a(n);
    for (auto &[l, r] : a)
        cin >> l >> r;
    sort(a.begin(), a.end());
    int l = a[0].first, r = a[0].second, busy = 0, idle = 0;
    for (int i = 1; i < n; i++) {
        if (a[i].first <= r)
            r = max(r, a[i].second);
        else {
            busy = max(busy, r - l);
            idle = max(idle, a[i].first - r);
            tie(l, r) = a[i];
        }
    }
    busy = max(busy, r - l);
    cout << busy << ' ' << idle << '\n';

    return 0;
}
```

### 实现提醒

相接时合并；不要漏结算最后一段；时间长度是右端减左端。
