## CF1151E Number of Components

原题：[CF1151E](https://www.luogu.com.cn/problem/CF1151E)

### 思路

把保留下来的位置看作原路径图的顶点，连续段数等于保留点数减相邻保留边数。交换对值域区间的求和，值 x 的点贡献 x(n−x+1)，相邻值 u,v 的边贡献 min(u,v)(n−max(u,v)+1)。

### 复杂度

时间 O(n)，空间 O(n)，也可只保存前一个值降为空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long long> a(n);
    long long ans = 0;
    for (auto &x : a) {
        cin >> x;
        ans += x * (n - x + 1);
    }
    for (int i = 1; i < n; i++)
        ans -= min(a[i - 1], a[i]) * (n - max(a[i - 1], a[i]) + 1);
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

相邻关系来自原下标；点减边；乘积与总答案用 long long。
