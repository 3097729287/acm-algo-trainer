## P3924 康娜的线段树

原题：[P3924](https://www.luogu.com.cn/problem/P3924)

### 从问题到算法

每个线段树节点的值是它区间内叶子值之和。随机走树时，某节点对期望的贡献是“到达概率×节点值”。把求和顺序交换，改为固定某个叶子的 a[i]，它会被所有祖先节点包含。

根深度为零，每次左右等概率，所以祖先深度 d 的到达概率为 1/2^d。叶深 D 的总系数为 Σ(d=0..D)2^(−d)=2−2^(−D)。这个系数只依赖分割方式，不随 a[i] 或修改改变。

取所有叶子的最大深度 H，把系数同时乘 2^H 转成整数 weight[i]=2^(H+1)−2^(H−D)。维护加权和 V=Σa[i]weight[i]；区间加 x 只需 V+=x·Σ区间weight。系数前缀和使每次修改成为 O(1)。

输出时再乘 qwq 并除以 2^H。按题目保证最终是整数，程序用 __int128 保存累计乘积，避免多次大范围加法后的中间溢出。

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
