## C. Fence

### 题意

给定 $n$ 块木板高度，找总高度最小的连续 $k$ 块，输出其左端编号。$1\le k\le n\le150000$，高度在 $1$ 到 $100$ 之间。

### 从零讲：vector：长度可变的连续数组

**动态数组 `vector`。** `std::vector<int> a(n)` 创建含有 $n$ 个整数的连续数组，有效下标为零至 $n-1$；下标访问为 $O(1)$。`for (int &v : a)` 中的引用让输入直接写进原数组。不要访问 `a[n]`；容器中途增容可能使旧引用、指针或迭代器失效，本题读入后不增容。

### 思路

先求前 $k$ 块木板的高度和。窗口每次右移一格，减去离开的木板高度、加上新进入的木板高度，记录最小和及其左端点。

![固定长度窗口右移](assets/c-window.svg)

图中窗口从第 $1$–$3$ 块移到第 $2$–$4$ 块，公共的两块保留，所以新和为 $9-1+1=9$。每个长度为 $k$ 的连续段恰好被检查一次，故不会漏掉最优段。时间 $O(n)$，保存输入需要 $O(n)$ 空间。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, k;
    cin >> n >> k;
    vector<int> h(n);
    for (int &v : h) cin >> v;
    int sum = 0;
    for (int i = 0; i < k; ++i) sum += h[i];
    int best = sum, answer = 1;
    for (int r = k; r < n; ++r) {
        // 窗口右移：去掉最左木板，加入新右端木板。
        sum += h[r] - h[r - k];
        if (sum < best) {
            best = sum;
            answer = r - k + 2;  // 转为从一开始的左端点。
        }
    }
    cout << answer << '\n';
}
```

### 易错点

输出从一开始的左端点；窗口不能绕过数组末尾；并列最优可任选。
