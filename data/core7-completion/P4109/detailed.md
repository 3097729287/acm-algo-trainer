## P4109 定价

原题：[P4109](https://www.luogu.com.cn/problem/P4109)

### 从问题到算法

去掉末尾零后，荒谬度只取决于剩余位数，以及最后一位是不是五。设价格是 q·10^k，枚举 k 后，可行 q 落在一个整数区间。

在同一 k 下，最小 q 的位数不会比其它候选更大，它给出了普通偶数荒谬度的最优候选。若末位为五可能降低一，则还需检查不小于下界且模十为五的最小 q；更大的同类 q 不会有更少位数，也不会有更小价格。

对这两类候选都重新按题意去零计算荒谬度，避免它实际上带有更多尾零时误判。所有 k 的最优候选中，先比较荒谬度，再比较价格。上界至多十亿，只有十种幂需要考虑。

### 复杂度

每组时间 O(log² R)，空间 O(1)。

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
        long long l, r;
        cin >> l >> r;
        int best = INT_MAX;
        long long answer = l;
        auto test = [&](long long p) {
            if (p < l || p > r)
                return;
            long long x = p;
            while (x % 10 == 0)
                x /= 10;
            int score = 2 * (int)to_string(x).size() - (x % 10 == 5);
            if (score < best || (score == best && p < answer)) {
                best = score;
                answer = p;
            }
        };
        for (long long power = 1; power <= r; power *= 10) {
            long long q = (l + power - 1) / power;
            test(q * power);
            long long five = q + (5 - q % 10 + 10) % 10;
            test(five * power);
        }
        cout << answer << '\n';
    }

    return 0;
}
```

### 实现提醒

候选必须在 [L,R]；并列取更小；最小倍数使用向上取整。
