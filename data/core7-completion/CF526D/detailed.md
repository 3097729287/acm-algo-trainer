## CF526D Om Nom and Necklace

原题：[CF526D](https://www.luogu.com.cn/problem/CF526D)

### 从问题到算法

题目要求的 ABAB…A 可写为 k 个同长块 AB 加一个不超过整块长的前缀 A。A、B 可以为空，因此块长 p 只要至少一，额外长度可从零到 p。

若 Z[p]≥(k−1)p，则前 kp 个字符是 k 次重复。接下来与开头相同的长度为 Z[kp]，所以合法总长度是区间 [kp,kp+min(p,Z[kp])]，并截断到 n。当 kp=n，额外只能为零。

枚举 p≤n/k，将每个区间加到差分数组，最后前缀和大于零的位置输出一。k=1 时所有前缀都合法，也由同一公式得到。

### 复杂度

时间 O(n+n/k)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

vector<int> zfunction(const string &s) {
    int n = s.size();
    vector<int> z(n);
    z[0] = n;
    for (int i = 1, l = 0, r = 0; i < n; i++) {
        if (i <= r)
            z[i] = min(r - i + 1, z[i - l]);
        while (i + z[i] < n && s[z[i]] == s[i + z[i]])
            z[i]++;
        if (i + z[i] - 1 > r) {
            l = i;
            r = i + z[i] - 1;
        }
    }
    return z;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, k;
    string s;
    cin >> n >> k >> s;
    auto z = zfunction(s);
    z.push_back(0);
    vector<int> diff(n + 2);
    for (int p = 1; 1LL * k * p <= n; p++)
        if (z[p] >= (k - 1) * p) {
            int l = k * p, r = min(n, l + min(p, z[l]));
            diff[l]++;
            diff[r + 1]--;
        }
    int active = 0;
    for (int i = 1; i <= n; i++) {
        active += diff[i];
        cout << (active ? '1' : '0');
    }
    cout << '\n';

    return 0;
}
```

### 实现提醒

允许 A 或 B 为空；kp 本身也合法；Z[n] 按零处理。
