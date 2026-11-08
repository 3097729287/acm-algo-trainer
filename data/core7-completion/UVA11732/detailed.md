## UVA11732 "strcmp()" Anyone?

原题：[UVA11732](https://www.luogu.com.cn/problem/UVA11732)

### 从问题到算法

按原题 strcmp 伪代码，每个相同的非空字符要做字符相等与是否结束两次比较，第一次不同只做一次；完全相同还要对结束符做两次。因此每对贡献 2LCP+1，再对完全相同的一对补一。伪代码可核对[原题 PDF](https://onlinejudge.org/external/117/11732.pdf)。

将所有字符串字典序排序，令 h[i] 为相邻两串的 LCP。排序后第 l、r 两串的 LCP 恰好是 h[l+1..r] 的最小值。因此全部 LCP 之和等价于 h 所有非空子数组的最小值之和。

单调递增栈按“以当前元素结尾的子数组”维护最小值与数量。弹出不小于新 h 的栈项，将这些项的数量合并给新值，同时更新当前结尾的最小值总和。最后答案为 n(n−1)/2+2·LCP总和+同串对数。这个方法避免为长字母数字串建立巨大字符表。

### 复杂度

设输入总长度为 S，时间 O(S log n+n)，空间 O(S+n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, caseNo = 0;
    while (cin >> n && n) {
        vector<string> a(n);
        for (auto &s : a)
            cin >> s;
        sort(a.begin(), a.end());
        long long same = 0;
        for (int l = 0; l < n;) {
            int r = l + 1;
            while (r < n && a[r] == a[l])
                r++;
            same += 1LL * (r - l) * (r - l - 1) / 2;
            l = r;
        }
        vector<pair<int, int>> st;
        long long ending = 0, totalLcp = 0;
        for (int i = 1; i < n; i++) {
            int h = 0;
            while (h < (int)min(a[i].size(), a[i - 1].size()) && a[i][h] == a[i - 1][h])
                h++;
            int count = 1;
            while (!st.empty() && st.back().first >= h) {
                ending -= 1LL * st.back().first * st.back().second;
                count += st.back().second;
                st.pop_back();
            }
            st.push_back({h, count});
            ending += 1LL * h * count;
            totalLcp += ending;
        }
        cout << "Case " << ++caseNo << ": " << 1LL * n * (n - 1) / 2 + 2 * totalLcp + same << '\n';
    }

    return 0;
}
```

### 实现提醒

相同串额外补一次；输入含大小写字母和数字；答案六十四位。
