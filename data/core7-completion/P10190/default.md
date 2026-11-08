## P10190 Target Practice II S

原题：[P10190](https://www.luogu.com.cn/problem/P10190)

### 思路

右下角必须用正斜率、右上角必须用负斜率。左端顶点按高度排序，低的分给负斜率、高的分给正斜率。随后分别二分正斜率截距的最大下界与负斜率截距的最小上界。

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
