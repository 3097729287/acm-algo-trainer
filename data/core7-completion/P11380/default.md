## P11380 排队

原题：[P11380](https://www.luogu.com.cn/problem/P11380)

### 思路

每人最多有一个必须紧邻的前驱和后继。若出现冲突或有向环就无解；否则各条定向链内部顺序固定，把链当作整体任意排列，答案为链数的阶乘。

### 复杂度

时间 O(n+m)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<int> next(n + 1), previous(n + 1);
    bool ok = true;
    while (m--) {
        int a, b;
        cin >> a >> b;
        if (a == b || (next[a] && next[a] != b) || (previous[b] && previous[b] != a))
            ok = false;
        else {
            next[a] = b;
            previous[b] = a;
        }
    }
    int chains = 0, visited = 0;
    for (int i = 1; i <= n; i++)
        if (!previous[i]) {
            chains++;
            for (int v = i; v; v = next[v])
                visited++;
        }
    if (!ok || visited != n) {
        cout << 0 << '\n';
        return 0;
    }
    long long ans = 1;
    for (int i = 1; i <= chains; i++)
        ans = ans * i % 1000000007;
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

重复约束不重复计数；自环无解；检查所有点是否属于某条链。
