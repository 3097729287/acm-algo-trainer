## P13278 PVP

原题：[P13278](https://www.luogu.com.cn/problem/P13278)

### 思路

先找敌方攻击第一次累计达到 m 的时刻。在它之前，我方原始伤害为 D、攻击次数为 c。道具 x 能赢当且仅当 D+cx≥m；不能赢时，存在死亡时刻则输，否则平局。

### 复杂度

时间 O(n+q)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    long long m;
    cin >> n >> m >> q;
    long long taken = 0, damage = 0, count = 0;
    bool dead = false;
    for (int i = 0; i < n; i++) {
        long long a;
        cin >> a;
        if (dead)
            continue;
        if (a < 0) {
            taken -= a;
            if (taken >= m)
                dead = true;
        } else {
            damage += a;
            count++;
        }
    }
    while (q--) {
        long long x;
        cin >> x;
        cout << (damage + count * x >= m ? "Yes" : dead ? "No" : "Tie") << '\n';
    }

    return 0;
}
```

### 实现提醒

死亡之后的攻击不再累计；负数攻击没有加成；总伤害使用 long long。
