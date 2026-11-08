## CF119A Epic Game

原题：[CF119A](https://www.luogu.com.cn/problem/CF119A)

### 思路

轮到某人时，用他的固定数字与剩余石子数求 gcd，移走对应数量。当前不能移走的玩家输，逐回合模拟即可。

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
