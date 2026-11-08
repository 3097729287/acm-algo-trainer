## UVA11078 Open Credit System

原题：[UVA11078](https://www.luogu.com.cn/problem/UVA11078)

### 从问题到算法

要求 i<j 且最大化 a[i]−a[j]。当后者 j 固定时，减数固定，只需选择前面最大 a[i]，所以无需枚举所有数对。

先读第一项作为历史最大，从第二项开始更新“历史最大减当前值”，然后再更新历史最大，保证比较的两个位置不同且顺序合法。

数组严格递增时所有差都是负数，题目仍要输出最大的负差，不能把答案初始化为零。

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
