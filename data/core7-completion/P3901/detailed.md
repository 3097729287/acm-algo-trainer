## P3901 数列找不同

原题：[P3901](https://www.luogu.com.cn/problem/P3901)

### 从问题到算法

区间内出现重复，等价于存在某个位置 i，它与相同值的前一次出现位置 pre[i] 都落在 [l,r] 中，即 l<=pre[i]<i<=r。

维护 bad[r]=max(pre[1],…,pre[r])。若 bad[r]>=l，产生该最大值的位置 i 一定大于 pre[i]、不超过 r，因此它与前驱都在查询区间内，存在重复。若 bad[r]<l，所有位置的同值前驱都在区间外，不可能出现重复。

读取数组时用 last[value] 得到前驱，再更新 bad 的前缀最大值。每次查询只比较一个整数，不需要莫队或线段树。

### 复杂度

时间 O(n+q)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    cin >> n >> q;
    vector<int> last(n + 1), bad(n + 1);
    for (int i = 1; i <= n; i++) {
        int x;
        cin >> x;
        bad[i] = max(bad[i - 1], last[x]);
        last[x] = i;
    }
    while (q--) {
        int l, r;
        cin >> l >> r;
        cout << (bad[r] < l ? "Yes" : "No") << '\n';
    }

    return 0;
}
```

### 实现提醒

比较是严格小于 l；last 的零表示从未出现。
