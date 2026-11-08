## P5742 评等级

原题：[P5742](https://www.luogu.com.cn/problem/P5742)

### 思路

优秀须同时满足两项分数和大于 140、综合分至少 80。综合分 0.7a+0.3b≥80 等价于 7a+3b≥800，用整数判断即可。

### 复杂度

时间 O(n)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    while (n--) {
        int id, a, b;
        cin >> id >> a >> b;
        cout << ((a + b > 140 && 7 * a + 3 * b >= 800) ? "Excellent" : "Not excellent") << '\n';
    }

    return 0;
}
```

### 实现提醒

总分严格大于 140；加权分至少 80；编号不计入成绩。
