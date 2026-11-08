## P1766 液体滴落

原题：[P1766](https://www.luogu.com.cn/problem/P1766)

### 思路

在非水平、非竖直且每次首次命中唯一的情形，枚举下落时的最高交点，再滑到轨道较低端。交点用有理数比较。原题未定义同时命中多条轨道的选择，详细题解保留反例，代码不猜定该规则。

### 复杂度

唯一命中情形时间 O(N²)，空间 O(N)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long x;
    cin >> n >> x;
    struct Segment {
        long long l, yl, r, yr;
    };
    vector<Segment> a(n);
    for (auto &s : a) {
        cin >> s.l >> s.yl >> s.r >> s.yr;
        if (s.l > s.r) {
            swap(s.l, s.r);
            swap(s.yl, s.yr);
        }
    }
    long long y = 1000000001LL;
    vector<char> used(n);
    for (int step = 0; step <= n; step++) {
        int best = -1;
        long long bestNum = 0, bestDen = 1;
        bool tie = false;
        for (int i = 0; i < n; i++)
            if (!used[i]) {
                auto s = a[i];
                if (s.l == s.r) {
                    if (x == s.l && min(s.yl, s.yr) < y)
                        return 0;
                    continue;
                }
                if (!(s.l < x && x < s.r))
                    continue;
                if (s.yl == s.yr && s.yl <= y)
                    return 0;
                long long den = s.r - s.l, num = s.yl * den + (s.yr - s.yl) * (x - s.l);
                if ((__int128)num > (__int128)y * den)
                    continue;
                if (best < 0 || (__int128)num * bestDen > (__int128)bestNum * den) {
                    best = i;
                    bestNum = num;
                    bestDen = den;
                    tie = false;
                } else if ((__int128)num * bestDen == (__int128)bestNum * den)
                    tie = true;
            }
        if (best < 0) {
            cout << x << '\n';
            return 0;
        }
        if (tie)
            return 0;
        used[best] = 1;
        auto s = a[best];
        if (s.yl < s.yr) {
            x = s.l;
            y = s.yl;
        } else {
            x = s.r;
            y = s.yr;
        }
    }

    return 0;
}
```

### 实现提醒

端点严格排除；同高内部可再次命中；高度比较用 __int128；同时首次命中仍需原题补充规则。
