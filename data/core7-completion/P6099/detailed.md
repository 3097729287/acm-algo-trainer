## P6099 Dishwashing G

原题：[P6099](https://www.luogu.com.cn/problem/P6099)

### 从问题到算法

桌面各堆的底部保持递增。把盘 x 放到堆底大于 x 的最左堆，能够尽量靠左，同时不会让更大的底盘提前挡住它；若不存在，就在最右边开新堆。堆底数组递增，可用二分找位置。

同一堆中，若顶盘小于新来的 x，为了不把较小盘压在 x 下方，必须先把这些顶盘冲洗。它们以及更左堆能够按顺序处理，故记录最大已冲洗编号 washed 即可。之后任何 x<washed 的新盘都应排在已经洗好的大盘下面，却已来不及，说明从这一盘开始失败。

在尚未失败时，上述放置与必要弹栈保持可整理性；遇到失败便输出此前长度。每盘最多进出一个栈一次，二分只依赖堆底，不随弹栈变化。

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
