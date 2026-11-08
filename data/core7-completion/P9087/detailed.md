## P9087 音符

原题：[P9087](https://www.luogu.com.cn/problem/P9087)

### 从问题到算法

把相邻字符是否相同视为边。一个长度 k 子串有重音，当且仅当它内部 k−1 条边至少一条被选中。总窗口数 W=n−k+1，一条重音边最多覆盖 k−1 个窗口，所以 c 处至少留下 max(0,W−c(k−1)) 个干净窗口。

这个下界可以达到：把重音边放在 k−1、2(k−1)、……处，它们覆盖的窗口连续且不重复，最后一处允许覆盖不足 k−1 个。其它边让相邻字符不同，只用 a、b 两个字母就能实现任意边选择。

总费用 c·a+max(0,W−c(k−1))·b，在最后一次覆盖前后分别线性，所以只需 c=0、floor(W/(k−1))、ceil(W/(k−1)) 三种候选。k>n 时没有长度 k 窗口，直接输出交替串、费用零。

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
