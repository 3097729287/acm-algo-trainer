## P1297 单选错位

原题：[P1297](https://www.luogu.com.cn/problem/P1297)

### 从问题到算法

第 i 题的答案被抄到下一题。只有两个正确选项编号相同，下一题才会答对。可相同的编号有 min(a[i],a[next]) 个，每一对答案等概率，因此正确概率为其除以 a[i]a[next]，化简为较大选项数的倒数。

期望具有线性性，各题是否正确即使有相关性也能直接相加。首尾循环的一对不能遗漏。

生成序列分两步：先用原始递推值生成下一原始值，再将当前值对 C 取模加一作为选项数。不能把已转成选项数的值带回生成器。只保留原始前值、前一个选项数、首项，即可常数空间累加。

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
