## P1878 舞蹈课

原题：[P1878](https://www.luogu.com.cn/problem/P1878)

### 从问题到算法

删除一对后，只有左侧邻居与右侧邻居之间出现一个新的相邻关系，其它候选对的技术差不变。因此不必每轮重新扫描全部队伍。

初始将所有相邻异性对入堆，关键字先比较技术绝对差，再比较左端编号。原始编号随队伍保持顺序，左端编号最小正好表示最左一对。

堆内旧候选不必立即删除，弹出时检查两人未离队且 next[left]==right，失效就丢弃。有效对离队后，将前后邻居接起来，若性别不同则插入新候选。每次删除最多产生一对，所有堆项数量为线性。

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
