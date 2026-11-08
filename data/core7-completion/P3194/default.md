## P3194 水平可见直线

原题：[P3194](https://www.luogu.com.cn/problem/P3194)

### 思路

同斜率只保留最高一条。按斜率递增加入直线，维护每条线开始成为最高线的横坐标；新交点不在上条线可见区间右侧时弹掉上条线。

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
