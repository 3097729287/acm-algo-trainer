## AT_arc172_c Election

原题：[AT_arc172_c](https://www.luogu.com.cn/problem/AT_arc172_c)

### 从问题到算法

第一位投票者之外的顺序固定，所以全部可能顺序只由第一张票插入在什么位置决定。从最前插入开始，逐次把它与下一张票交换，就枚举了所有 n 种顺序。

比较相邻两种顺序：交换前后，在这两张票之前的票数完全相同，在两张都开出后也完全相同。只有开出其中第一张时，公布的领先或平局结果可能不同。用 A=+1、B=−1，设此前差为 d，比较 sign(d+第一票) 与 sign(d+当前票)。不同就产生一个新结果序列。

每次交换改变的是一个此前从未改动过的公布位置，之后也不会再改变它。因此一旦产生新序列，就不可能与更早的序列重复。答案正好是一加上发生变化的交换数，无须保存或哈希全部长度 n 的序列。

### 复杂度

时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    string s;
    cin >> n >> s;
    auto sign = [](int x) { return (x > 0) - (x < 0); };
    int first = s[0] == 'A' ? 1 : -1, difference = 0, ans = 1;
    for (int i = 1; i < n; i++) {
        int v = s[i] == 'A' ? 1 : -1;
        if (sign(difference + first) != sign(difference + v))
            ans++;
        difference += v;
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

统计公布结果的不同序列，不是开票顺序；差值需在比较后再加入当前票。
