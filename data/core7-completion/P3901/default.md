## P3901 数列找不同

原题：[P3901](https://www.luogu.com.cn/problem/P3901)

### 思路

记录每个位置的值上次出现在哪里。令 bad[r] 是前 r 项中这些前驱位置的最大值，则 [l,r] 全部不同当且仅当 bad[r]<l。

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
