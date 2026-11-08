## P1878 舞蹈课

原题：[P1878](https://www.luogu.com.cn/problem/P1878)

### 思路

用双向链表表示还在队伍中的人，把相邻异性对按技术差、左端编号放入最小堆。弹出时检查是否仍相邻，删除有效的一对，并加入新产生的邻接对。

### 复杂度

时间 O(n log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    string gender;
    cin >> n >> gender;
    vector<int> a(n), left(n), right(n);
    vector<char> alive(n, 1);
    for (int &x : a)
        cin >> x;
    for (int i = 0; i < n; i++) {
        left[i] = i - 1;
        right[i] = i + 1 < n ? i + 1 : -1;
    }
    using P = tuple<int, int, int>;
    priority_queue<P, vector<P>, greater<P>> heap;
    auto push = [&](int l, int r) {
        if (l >= 0 && r >= 0 && gender[l] != gender[r])
            heap.push({abs(a[l] - a[r]), l, r});
    };
    for (int i = 1; i < n; i++)
        push(i - 1, i);
    vector<pair<int, int>> ans;
    while (!heap.empty()) {
        auto [diff, l, r] = heap.top();
        heap.pop();
        if (!alive[l] || !alive[r] || right[l] != r)
            continue;
        ans.push_back({l + 1, r + 1});
        alive[l] = alive[r] = 0;
        int L = left[l], R = right[r];
        if (L >= 0)
            right[L] = R;
        if (R >= 0)
            left[R] = L;
        push(L, R);
    }
    cout << ans.size() << '\n';
    for (auto [l, r] : ans)
        cout << l << ' ' << r << '\n';

    return 0;
}
```

### 实现提醒

技术差取绝对值；同差按左端编号；堆内过期对必须跳过。
