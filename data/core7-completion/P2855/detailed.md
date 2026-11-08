## P2855 River Hopscotch S

原题：[P2855](https://www.luogu.com.cn/problem/P2855)

### 从问题到算法

跳距要求越小越容易满足，所以可对答案二分。固定 D 后，若当前石头距离上次保留点不足 D，它不能保留；若已足够，优先保留最靠左的石头会给后续留下最多空间，不会比保留更右的石头更差。

按位置顺序扫描，统计必须删除的石头。终点固定不可删除；若最后一次到终点距离不足 D，可以改为删除最后保留的内部石头。其前一个保留点到最后石头已至少 D，所以删掉后到终点更远，一次删除足够。代码把终点处的这次冲突计为一次删除，数值等价。

可行时提高下界，不可行时降低上界。石头位置先排序，起点零与终点 L 不计入可主动移走的 M 块。

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
