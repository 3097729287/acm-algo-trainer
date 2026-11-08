## UVA11078 Open Credit System

原题：[UVA11078](https://www.luogu.com.cn/problem/UVA11078)

### 思路

逐项作为后面那个人，最优前者就是此前最大分数。用它减当前值更新答案，再把当前值纳入历史最大值。

### 复杂度

每组时间 O(n)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    while (tests--) {
        int n;
        cin >> n;
        long long best;
        cin >> best;
        long long answer = LLONG_MIN;
        for (int i = 1; i < n; i++) {
            long long x;
            cin >> x;
            answer = max(answer, best - x);
            best = max(best, x);
        }
        cout << answer << '\n';
    }

    return 0;
}
```

### 实现提醒

先比较再更新历史最大；答案允许负数；两位置不能相同。
