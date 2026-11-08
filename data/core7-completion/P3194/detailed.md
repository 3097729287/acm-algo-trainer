## P3194 水平可见直线

原题：[P3194](https://www.luogu.com.cn/problem/P3194)

### 从问题到算法

从上方看到的正是所有直线的逐点最大值，也叫上包络。斜率越大的线越可能在更右侧占优，因此按斜率从小到大处理，可见区间也按横坐标递增。

平行线中截距较小者永远被覆盖，先去掉。对新线与栈顶线求交点 x；如果 x 不大于栈顶开始可见的位置，那么栈顶线还没获得正长度的可见区间就被新线压住，必须弹出，并继续与更前一条比较。

最终保留的直线各自拥有一个非空开区间可见。三线恰在一点交会时，中间线若只在一个点达到最大，不算看见一段线，因此相等时也要弹出。输出原始编号并按编号排序。

### 复杂度

时间 O(n log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct Line {
    long long k, b;
    int id;
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<Line> a(n);
    for (int i = 0; i < n; i++) {
        cin >> a[i].k >> a[i].b;
        a[i].id = i + 1;
    }
    sort(a.begin(), a.end(), [](Line a, Line b) {
        if (a.k != b.k)
            return a.k < b.k;
        return a.b > b.b;
    });
    vector<Line> h;
    vector<long double> start;
    for (auto line : a) {
        if (!h.empty() && line.k == h.back().k)
            continue;
        long double x = -numeric_limits<long double>::infinity();
        while (!h.empty()) {
            x = (long double)(h.back().b - line.b) / (line.k - h.back().k);
            if (x > start.back())
                break;
            h.pop_back();
            start.pop_back();
        }
        if (h.empty())
            x = -numeric_limits<long double>::infinity();
        h.push_back(line);
        start.push_back(x);
    }
    vector<int> ans;
    for (auto line : h)
        ans.push_back(line.id);
    sort(ans.begin(), ans.end());
    for (int id : ans)
        cout << id << ' ';
    cout << '\n';

    return 0;
}
```

### 实现提醒

同斜率保留最高截距；只在单个交点出现不算可见；输出原编号。
