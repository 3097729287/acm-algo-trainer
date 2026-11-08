## CF388C Fox and Card Game

原题：[CF388C](https://www.luogu.com.cn/problem/CF388C)

### 从问题到算法

偶数堆的前后两半可以通过配对回应保证：对手从某堆拿一张后，自己从该堆另一端回应，就能守住本方的一半。偏离这种配对不能迫使对方放弃它能够保证的牌。

奇数堆在两侧各取相同数量后，还会剩一张中间牌。它属于谁是唯一未确定的部分；各堆中点之间没有其它相互限制，争夺者总应优先拿当前最大中点。若先拿更小中点而把更大留给对手，交换选择只会提高自己的最终总分。

所以每堆前 floor(s/2) 张累加给 Ciel，后 floor(s/2) 张给 Jiro；所有奇数中点降序排列，从 Ciel 开始交替累加。

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
