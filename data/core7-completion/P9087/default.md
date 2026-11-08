## P9087 音符

原题：[P9087](https://www.luogu.com.cn/problem/P9087)

### 思路

相邻相同的一处最多覆盖 k−1 个长度 k 窗口。若设置 c 处重音，最少仍有 max(0,n−k+1−c(k−1)) 个干净窗口。代价分段线性，只需检查零、整除点及再多一处。

### 复杂度

每组时间 O(n)，额外空间 O(n) 用于输出。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        int n, k;
        long long a, b;
        cin >> n >> k >> a >> b;
        if (k > n) {
            cout << 0 << '\n';
            for (int i = 0; i < n; i++)
                cout << (i % 2 ? 'b' : 'a');
            cout << '\n';
            continue;
        }
        long long W = n - k + 1, width = k - 1, best = LLONG_MAX, count = 0;
        for (long long c : {0LL, W / width, (W + width - 1) / width}) {
            long long value = c * a + max(0LL, W - c * width) * b;
            if (value < best) {
                best = value;
                count = c;
            }
        }
        string s(n, 'a');
        for (int i = 1; i < n; i++) {
            bool accent = i % width == 0 && i / width <= count;
            s[i] = accent ? s[i - 1] : (s[i - 1] == 'a' ? 'b' : 'a');
        }
        cout << best << '\n' << s << '\n';
    }

    return 0;
}
```

### 实现提醒

重音按相邻一对计数；末次覆盖可以不满；所有乘积六十四位。
