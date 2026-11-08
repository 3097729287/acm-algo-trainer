## P7960 报数

原题：[P7960](https://www.luogu.com.cn/problem/P7960)

### 从问题到算法

一个整数不合法，当且仅当能被某个含七的数整除。扫描到含七且未禁用的 i 时，筛掉它的倍数；若 i 早已被筛掉，它的所有倍数也已被某个更小含七因子筛掉，无须重复操作。

每个不合法数都有含七因子，该因子自身被处理或已经被更小因子覆盖，因此筛法完整。之后倒序扫描，维护最近的合法数 next：先保存当前数的严格后继，再在当前合法时更新 next。

预处理范围必须超过最大询问，直到确认其中存在比最大询问更大的合法数。代码采用可扩大的上界，若尾部全被禁用就翻倍重筛，避免依赖未经证明的固定余量。

### 复杂度

设最终预处理上界为 L，时间 O(L log L)，空间 O(L)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    vector<int> queries(T);
    int maximum = 0;
    for (int &x : queries) {
        cin >> x;
        maximum = max(maximum, x);
    }
    int limit = max(128, maximum + 128);
    vector<bool> bad;
    vector<int> next;
    for (;;) {
        bad.assign(limit + 1, false);
        for (int i = 1; i <= limit; i++)
            if (!bad[i]) {
                int x = i;
                bool seven = false;
                while (x) {
                    if (x % 10 == 7)
                        seven = true;
                    x /= 10;
                }
                if (seven)
                    for (int j = i; j <= limit; j += i)
                        bad[j] = true;
            }
        int last = 0;
        next.assign(limit + 1, 0);
        for (int i = limit; i >= 1; i--) {
            next[i] = last;
            if (!bad[i])
                last = i;
        }
        if (next[maximum])
            break;
        limit *= 2;
    }
    for (int x : queries)
        cout << (bad[x] ? -1 : next[x]) << '\n';

    return 0;
}
```

### 实现提醒

倍数不一定含七；后继必须严格更大；非法询问输出 −1。
