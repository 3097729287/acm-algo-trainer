## P12397 函数大师

原题：[P12397](https://www.luogu.com.cn/problem/P12397)

### 思路

原数 x 不超过 m，它的数位和最多 171。固定数位和 s 后，后续反复求和的贡献完全确定，故 x=m−贡献。枚举 s，检查推得的 x 是否正且数位和确实为 s。

### 复杂度

预处理 O(171 log 171)，每次询问 O(171 log m)，空间 O(171)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    long long k;
    cin >> tests >> k;
    auto digitSum = [](long long x) {
        int s = 0;
        for (; x; x /= 10)
            s += x % 10;
        return s;
    };
    vector<long long> contribution(172);
    for (int s = 1; s <= 171; s++) {
        long long value = s, left = k, total = 0;
        while (left && value >= 10) {
            total += value;
            value = digitSum(value);
            left--;
        }
        contribution[s] = total + value * left;
    }
    while (tests--) {
        long long m;
        cin >> m;
        if (!k) {
            cout << 1 << '\n';
            continue;
        }
        int answer = 0;
        for (int s = 1; s <= 171; s++)
            if (m > contribution[s]) {
                long long x = m - contribution[s];
                if (digitSum(x) == s)
                    answer++;
            }
        cout << answer << '\n';
    }

    return 0;
}
```

### 实现提醒

一位数后批量计算剩余项；x 必须为正；k=0 单独处理。
