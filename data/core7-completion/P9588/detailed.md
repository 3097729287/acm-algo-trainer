## P9588 队列

原题：[P9588](https://www.luogu.com.cn/problem/P9588)

### 从问题到算法

将一次入队的 1..x 视为区间块，记录累计右端 end 与块长 x。若全局编号为 p，它属于第一个 end≥p 的块，值就是 p−(end−x)。队头删除 y 个只让 removed 增加 y；第 z 个元素的全局编号是 removed+z。

一个尚未删完的块，无论前端已经删了多少，它的最大元素 x 都还在末尾，所以全队最大值就是所有 end>removed 的块长最大值。维护块长递减的双端队列，新块到来时弹出较小末项；它们更早结束且最大值不更大，之后也不会有用。

删除时弹去已经完全消失的队首块。全局长度可达二乘十的十四次方，累计编号必须用 long long。

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
