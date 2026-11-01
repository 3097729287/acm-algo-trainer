## L. Books

### 题意

有 $n\le10^5$ 本书，每本阅读时间为正数。选一个起点连续向后读，不能跳书，总时间不超过 $t\le10^9$，求最多能完整读几本。

### 从零讲：vector 下标与边界

**数组下标与空窗口。** `std::vector<int> a(n)` 的下标为零至 $n-1$。窗口闭区间的元素个数为 $right-left+1$；当左端恰好越过右端一位时，这个值是零，表示空窗口。代码在 `while (sum > t)` 时取走当前左端元素，由所有用时为正且预算为正保证访问仍在已加入部分内。

### 思路

维护连续窗口和。右端点每次向右加入一本书；若总时间超过 $t$，就不断移走左端书，直到重新满足限制，更新最大窗口长度。

![超时后收缩左端的窗口](assets/l-books.svg)

每本书用时为正，所以左端右移只会减小总时间。对每个右端点，收缩后保留的是以它结尾的最长可行区间；所有右端点都检查后得到全局最优。左右指针各至多走 $n$ 步，时间 $O(n)$，空间 $O(n)$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    long long t;
    cin >> n >> t;
    vector<int> a(n);
    for (int &v : a) cin >> v;
    long long sum = 0;
    int left = 0, answer = 0;
    for (int right = 0; right < n; ++right) {
        sum += a[right];
        while (sum > t) {
            sum -= a[left];
            ++left;
        }
        // 对这个右端点，left 已是最靠左的合法起点。
        answer = max(answer, right - left + 1);
    }
    cout << answer << '\n';
}
```

### 易错点

一次可能要收缩多次；单本超时可得到空窗口；限制是连续阅读。
