## CF388C Fox and Card Game

原题：[CF388C](https://www.luogu.com.cn/problem/CF388C)

### 思路

每堆上半归先手、下半归后手；奇数堆多出的中间牌拿出来，按数值从大到小由两人轮流分配。把这三部分分别累加。

### 复杂度

时间 O(总牌数+n log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    long long first = 0, second = 0;
    vector<int> middle;
    while (n--) {
        int size;
        cin >> size;
        vector<int> a(size);
        for (int &x : a)
            cin >> x;
        for (int i = 0; i < size / 2; i++) {
            first += a[i];
            second += a[size - 1 - i];
        }
        if (size % 2)
            middle.push_back(a[size / 2]);
    }
    sort(middle.rbegin(), middle.rend());
    for (int i = 0; i < (int)middle.size(); i++)
        if (i % 2)
            second += middle[i];
        else
            first += middle[i];
    cout << first << ' ' << second << '\n';

    return 0;
}
```

### 实现提醒

输入按从顶到底顺序；偶数堆没有中点；先手先拿最大中点。
