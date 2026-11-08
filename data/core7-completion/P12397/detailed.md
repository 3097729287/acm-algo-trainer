## P12397 函数大师

原题：[P12397](https://www.luogu.com.cn/problem/P12397)

### 从问题到算法

函数 f_k(x) 的首项就是 x，其余项只依赖 x 的数位和 s。虽然 x 范围很大，s 的范围很小：不超过十九位十进制数的数位和上界 171。

对每个候选 s，预处理 H_k(s)=s+s(s)+…，共 k 项。每次取数位和很快变成一位数；之后这个值不再变化，可以直接乘上剩余项数，不必循环到十亿。

每次询问 m 时，固定 s 就只有一个可能原数 x=m−H_k(s)。若 x>0 且真实数位和等于 s，就得到一个解。不同 s 不会重复同一个 x。k=0 时 f_0(x)=x，答案恒为一。

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
