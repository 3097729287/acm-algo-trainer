## P1766 液体滴落

原题：[P1766](https://www.luogu.com.cn/problem/P1766)

### 从问题到算法

在“非水平非竖直轨道、每次首次命中唯一”的明确情形中，液滴只会交替经历竖直下落与整段下滑。对下落横坐标 x，轨道两端横坐标 l<r，交点高度为 (y_l(r−l)+(y_r−y_l)(x−l))/(r−l)。要求 l<x<r，因为端点不属于轨道。

找到不高于当前高度的最高交点，然后按题意忽略滑动途中的其它交点，直接到较低端，再重复。离开端点后可能立即碰到另一条轨道同高的内部，因此高度比较必须允许相等。每次沿非水平轨道都严格下降，不会重复使用轨道。

**原题边界仍未定义：**它允许轨道相交，却没有规定竖直下落同时命中两个内部交点时选哪条。例如输入 `2 0`、轨道 `−1 2 1 0` 和 `−1 0 1 2`，两种合法选择分别落在 x=1、x=−1。水平与竖直轨道也缺少明确处理规则。代码不替原题发明规则：检测到这种未定义情形就不输出伪造答案；验证仅覆盖前述唯一运动情形。完整反例说明保留在工作区语义核对文档中。

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
