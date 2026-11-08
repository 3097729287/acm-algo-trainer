## CF119A Epic Game

原题：[CF119A](https://www.luogu.com.cn/problem/CF119A)

### 从问题到算法

每一步移走的数量由当前剩余石子数唯一决定，没有可以优化的策略。令 turn=0 表示 Simon，turn=1 表示 Antisimon；按对应固定数字计算 gcd，并从石堆中扣除。

石子数为正时 gcd 至少为一且不会超过石子数，因此总会向结束推进。石子数为零时 gcd(a,0)=a，当前玩家无法移动，所以另一人获胜。代码在取走最后一颗后切换回合，最后输出当前回合的另一方。

求 gcd 使用欧几里得算法，它利用 gcd(a,b)=gcd(b,a%b)，直到余数为零。

### 复杂度

时间 O(n log max(a,b,n))，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int a, b, n;
    cin >> a >> b >> n;
    int turn = 0;
    while (n) {
        n -= gcd(turn ? b : a, n);
        turn ^= 1;
    }
    cout << (turn ^ 1) << '\n';

    return 0;
}
```

### 实现提醒

取完石子后换手，再判另一方获胜；gcd(a,0) 不为零。
