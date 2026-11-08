## P7023 Equal Numbers

原题：[P7023](https://www.luogu.com.cn/problem/P7023)

### 从问题到算法

要让一种原值彻底消失，必须修改它全部出现位置，代价等于频数；只改一部分不会减少这种原值。

第一类方案不出现任何新值。被消除的值必须能乘到某个保留的原值，因此它必有其它原值作为真倍数。反过来，所有这类非极大值都能沿整除关系最终乘到某个极大原值，极大值不被消除，故任取若干非极大种类消除都可行。要减少 r 种，代价为这些频数中最小 r 项之和。

第二类方案出现至少一种新值。若净减少 r 种，就至少让 r+1 个原种类消失，修改次数不小于全部频数中最小 r+1 项之和。这个下界也能达到：把这些种类的每个位置都乘到它们的一个共同倍数，新值只算一种；若共同倍数恰是保留原值，只会更好。

用倍数筛标记非极大值，分别排序两份频数并求前缀和。为每个减少量记录最少代价，再对操作预算做前缀最优，输出 0 到 n 次的答案。多余操作可以乘一，不改变结果。

### 复杂度

时间 O(A log A+n log n)，空间 O(A+n)。

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
    int maximum = 0;
    for (int &x : a) {
        cin >> x;
        maximum = max(maximum, x);
    }
    vector<int> frequency(maximum + 1);
    for (int x : a)
        frequency[x]++;
    vector<int> all, removable;
    for (int x = 1; x <= maximum; x++)
        if (frequency[x]) {
            all.push_back(frequency[x]);
            bool hasMultiple = false;
            for (int y = x + x; y <= maximum; y += x)
                if (frequency[y]) {
                    hasMultiple = true;
                    break;
                }
            if (hasMultiple)
                removable.push_back(frequency[x]);
        }
    sort(all.begin(), all.end());
    sort(removable.begin(), removable.end());
    vector<int> prefix(all.size() + 1), cheap(removable.size() + 1);
    for (int i = 0; i < (int)all.size(); i++)
        prefix[i + 1] = prefix[i] + all[i];
    for (int i = 0; i < (int)removable.size(); i++)
        cheap[i + 1] = cheap[i] + removable[i];
    int distinct = all.size();
    vector<int> answer(n + 1, distinct);
    for (int reduction = 1; reduction < distinct; reduction++) {
        int cost = prefix[reduction + 1];
        if (reduction < (int)cheap.size())
            cost = min(cost, cheap[reduction]);
        answer[cost] = min(answer[cost], distinct - reduction);
    }
    for (int k = 1; k <= n; k++)
        answer[k] = min(answer[k], answer[k - 1]);
    for (int k = 0; k <= n; k++)
        cout << answer[k] << (k == n ? '\n' : ' ');

    return 0;
}
```

### 实现提醒

一种值消失要修改全部副本；无新值时只消除非极大值；新值方案多消除一种。
