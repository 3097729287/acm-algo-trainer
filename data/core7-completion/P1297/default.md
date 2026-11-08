## P1297 单选错位

原题：[P1297](https://www.luogu.com.cn/problem/P1297)

### 思路

选项数为 u、v 的两题答案独立均匀，相同概率为 min(u,v)/(uv)=1/max(u,v)。将循环相邻两题的概率相加，得到期望。

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
    long long A, B, C, raw;
    cin >> n >> A >> B >> C >> raw;
    long long first = raw % C + 1, previous = first;
    long double ans = 0;
    for (int i = 2; i <= n; i++) {
        raw = (raw * A + B) % 100000001;
        long long current = raw % C + 1;
        ans += 1.0L / max(previous, current);
        previous = current;
    }
    ans += 1.0L / max(previous, first);
    cout << fixed << setprecision(3) << ans << '\n';

    return 0;
}
```

### 实现提醒

生成器用转换前的值；包含末题到首题；保留三位小数。
