## P6099 Dishwashing G

原题：[P6099](https://www.luogu.com.cn/problem/P6099)

### 思路

把新盘放到堆底编号大于它的最左堆中；若该堆顶较小，就先冲洗掉这些更小盘。记录已经冲洗过的最大编号，一旦新盘小于它，当前前缀便不可能排好。

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
    cin >> n;
    vector<int> a(n);
    for (int &x : a)
        cin >> x;
    vector<int> bottom;
    vector<vector<int>> stacks;
    int washed = 0;
    for (int i = 0; i < n; i++) {
        int x = a[i];
        if (x < washed) {
            cout << i << '\n';
            return 0;
        }
        int p = lower_bound(bottom.begin(), bottom.end(), x) - bottom.begin();
        if (p == (int)bottom.size()) {
            bottom.push_back(x);
            stacks.push_back({});
        }
        while (!stacks[p].empty() && stacks[p].back() < x) {
            washed = max(washed, stacks[p].back());
            stacks[p].pop_back();
        }
        stacks[p].push_back(x);
    }
    cout << n << '\n';

    return 0;
}
```

### 实现提醒

washed 只增不减；找最左的较大堆底；失败盘不计入前缀。
