## F. Twins

### 题意

给定至多 $100$ 枚正面值硬币，取尽量少的硬币，使已取总面值严格大于剩余总面值。

### 从零讲：sort 与迭代器范围

**排序范围。** `std::sort(first,last)` 对左闭右开区间原地升序排序，要求随机访问迭代器；`vector` 的 `begin()` 与 `end()` 正好指定全部元素。`end()` 不能解引用。排序一般花 $O(n\log n)$ 次比较；本题从末尾往前取值，不需要自定义比较器。

### 思路

把硬币按面值排序，从最大面值开始拿，直到已拿总额严格大于剩余总额。

对固定的枚数 $k$，最大的 $k$ 枚硬币的总额一定最大：任何选了较小硬币、漏了较大硬币的方案，都可交换而不降低总额。因此，当最大的 $k$ 枚还不够时，其他任意 $k$ 枚也不够；第一次满足条件的枚数就是最小答案。时间 $O(n\log n)$，空间 $O(n)$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, total = 0;
    cin >> n;
    vector<int> a(n);
    for (int &v : a) { cin >> v; total += v; }
    sort(a.begin(), a.end());
    int chosen = 0, answer = 0;
    // 固定枚数时，取最大的这些硬币能得到最大总额。
    for (int i = n - 1; i >= 0 && chosen <= total - chosen; --i) {
        chosen += a[i];
        ++answer;
    }
    cout << answer << '\n';
}
```

### 易错点

相等时仍不满足要求；先取最大面值，排序后从末尾扫描。
