## P13278 PVP

原题：[P13278](https://www.luogu.com.cn/problem/P13278)

### 从问题到算法

道具只增加我方伤害，不影响我方的死亡时刻，因此可以先只看负数攻击，确定敌人最早什么时候会打败我。

在这一时刻之前的正数攻击，总原始伤害 D、次数 c 都固定。加成后敌人受到的累计伤害为 D+cx，且随战斗推进单调不减。所以它达到 m，当且仅当某次我方攻击已经提前击败敌人。敌方造成死亡的那一次是负数攻击，不存在双方同时死亡的平局问题。

如果所有负数攻击都不致死，最后仍未击败敌人就为 Tie；否则为 No。预处理之后每个道具只需一次乘加判断。

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
