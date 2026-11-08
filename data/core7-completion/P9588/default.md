## P9588 队列

原题：[P9588](https://www.luogu.com.cn/problem/P9588)

### 思路

每次加入 1..x 只记录为一个块。所有加入元素使用全局连续编号，弹出只增加已删除总数；第 z 个元素二分定位所属块，最大值用各未删完块的 x 的单调队列维护。

### 复杂度

时间 O(q log q)，空间 O(q)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int caseId, q;
    cin >> caseId >> q;
    vector<long long> ends, lengths;
    deque<int> maximum;
    long long total = 0, removed = 0;
    while (q--) {
        int type;
        cin >> type;
        if (type == 1) {
            long long x;
            cin >> x;
            total += x;
            ends.push_back(total);
            lengths.push_back(x);
            int i = ends.size() - 1;
            while (!maximum.empty() && lengths[maximum.back()] <= x)
                maximum.pop_back();
            maximum.push_back(i);
        } else if (type == 2) {
            long long y;
            cin >> y;
            removed += y;
            while (!maximum.empty() && ends[maximum.front()] <= removed)
                maximum.pop_front();
        } else if (type == 3) {
            long long z;
            cin >> z;
            long long p = removed + z;
            int i = lower_bound(ends.begin(), ends.end(), p) - ends.begin();
            cout << p - (ends[i] - lengths[i]) << '\n';
        } else
            cout << lengths[maximum.front()] << '\n';
    }

    return 0;
}
```

### 实现提醒

半删块的最大值仍是 x；全局编号不回收；二分找第一个 end≥p。
