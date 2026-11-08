## P1204 挤牛奶 Milking Cows

原题：[P1204](https://www.luogu.com.cn/problem/P1204)

### 从问题到算法

同一时刻多名农夫工作仍只计一段忙碌时间，不能累加每个人的工作时长。排序后，尚未处理的区间左端不会比当前区间更早，因此只需维护最后一段合并区间。

若下一区间左端不大于当前右端，覆盖连续，右端更新为两者较大值。否则中间存在长度为新左端减旧右端的空闲段；先结算旧忙碌长度，再开始新的忙碌段。扫描结束还需结算最后一段。

只计算第一次开始工作到最后一次结束之间的空闲，前后无限长的无工作时间不计入。首尾相接没有正长度空隙，应当合并。

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
