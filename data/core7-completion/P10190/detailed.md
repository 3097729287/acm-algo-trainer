## P10190 Target Practice II S

原题：[P10190](https://www.luogu.com.cn/problem/P10190)

### 从问题到算法

射向右上角的线若为正斜率，会先穿过矩形内部，所以必须负斜率；右下角同理必须正斜率。左侧两个顶点没有符号限制。正负斜率数量均至少 N 才可能完成。

所有左端横坐标相同。若较低左顶点分给正斜率、较高顶点分给负斜率，交换它们会让正斜率牛的截距升高、负斜率牛的截距降低，两个新截距都位于原两截距之间。因此可以把最小的“负斜率数−N”个左顶点分给负斜率，其余分给正斜率。

记斜率绝对值为 s，正斜率截距为 y−sx，负斜率截距为 y+sx。所有正斜率截距的最大值不会超过某个负斜率截距：每个顶点高度总有相应矩形右上角高度不低于它；对最低值有对称论证。因此整体最小值由正组决定、最大值由负组决定，两组匹配可独立优化。

正组要求所有截距≥L，等价于每个目标允许 s≤floor((y−L)/x)；负组要求截距≤U，等价于 s≤floor((U−y)/x)。把斜率和允许上限分别排序，逐项比较即可判定匹配存在。分别二分最大 L、最小 U，答案 U−L。

### 复杂度

时间 O(N log N log V)，V 为截距范围；空间 O(N)。

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
        int n;
        long long X;
        cin >> n >> X;
        vector<pair<long long, long long>> positive, negative;
        vector<long long> leftY;
        for (int i = 0; i < n; i++) {
            long long y1, y2, x2;
            cin >> y1 >> y2 >> x2;
            positive.push_back({x2, y1});
            negative.push_back({x2, y2});
            leftY.push_back(y1);
            leftY.push_back(y2);
        }
        vector<long long> p, q;
        for (int i = 0; i < 4 * n; i++) {
            long long s;
            cin >> s;
            if (s > 0)
                p.push_back(s);
            else
                q.push_back(-s);
        }
        if ((int)p.size() < n || (int)q.size() < n) {
            cout << -1 << '\n';
            continue;
        }
        sort(p.begin(), p.end());
        sort(q.begin(), q.end());
        sort(leftY.begin(), leftY.end());
        int lowCount = q.size() - n;
        for (int i = 0; i < 2 * n; i++)
            (i < lowCount ? negative : positive).push_back({X, leftY[i]});
        auto feasible = [&](const vector<pair<long long, long long>> &points,
                            const vector<long long> &slopes, long long bound, bool lower) {
            vector<long long> caps;
            caps.reserve(points.size());
            for (auto [x, y] : points) {
                long long numerator = lower ? y - bound : bound - y;
                if (numerator < 0)
                    return false;
                caps.push_back(numerator / x);
            }
            sort(caps.begin(), caps.end());
            for (int i = 0; i < (int)caps.size(); i++)
                if (slopes[i] > caps[i])
                    return false;
            return true;
        };
        long long lo = -1000000000000000000LL, hi = 1000000000LL;
        while (lo < hi) {
            long long mid = lo + (hi - lo + 1) / 2;
            if (feasible(positive, p, mid, true))
                lo = mid;
            else
                hi = mid - 1;
        }
        long long L = lo;
        lo = 0;
        hi = 2000000000000000000LL;
        while (lo < hi) {
            long long mid = lo + (hi - lo) / 2;
            if (feasible(negative, q, mid, false))
                hi = mid;
            else
                lo = mid + 1;
        }
        cout << lo - L << '\n';
    }

    return 0;
}
```

### 实现提醒

右侧角点符号不能反；左端点按高度分配；乘积与截距需六十四位。
