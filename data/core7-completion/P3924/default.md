## P3924 康娜的线段树

原题：[P3924](https://www.luogu.com.cn/problem/P3924)

### 思路

深度为 d 的节点被走到的概率为 2^(−d)。一个叶子数值会出现在其所有祖先区间和中，系数为 1+1/2+…+1/2^depth=2−2^(−depth)。预处理系数前缀和，区间加直接更新总期望。

### 复杂度

预处理 O(n)，每次修改 O(1)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    long long denominator;
    cin >> n >> m >> denominator;
    int h = 0;
    while ((1 << h) < n)
        h++;
    long long base = 1LL << h;
    vector<long long> a(n + 1), weight(n + 1), prefix(n + 1);
    for (int i = 1; i <= n; i++)
        cin >> a[i];
    function<void(int, int, int)> build = [&](int l, int r, int depth) {
        if (l == r) {
            weight[l] = 2 * base - (1LL << (h - depth));
            return;
        }
        int mid = (l + r) / 2;
        build(l, mid, depth + 1);
        build(mid + 1, r, depth + 1);
    };
    build(1, n, 0);
    __int128 value = 0;
    for (int i = 1; i <= n; i++) {
        prefix[i] = prefix[i - 1] + weight[i];
        value += (__int128)a[i] * weight[i];
    }
    auto print = [](__int128 x) {
        if (x < 0) {
            cout << '-';
            x = -x;
        }
        string s;
        do {
            s.push_back('0' + x % 10);
            x /= 10;
        } while (x);
        reverse(s.begin(), s.end());
        cout << s << '\n';
    };
    while (m--) {
        int l, r;
        long long x;
        cin >> l >> r >> x;
        value += (__int128)x * (prefix[r] - prefix[l - 1]);
        print(value * denominator / base);
    }

    return 0;
}
```

### 实现提醒

使用题目给出的按中点分割；叶深不一定全相等；中间加权和用 __int128。
