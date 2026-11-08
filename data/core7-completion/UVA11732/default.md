## UVA11732 "strcmp()" Anyone?

原题：[UVA11732](https://www.luogu.com.cn/problem/UVA11732)

### 思路

两串比较次数为 2·LCP+1，相同字符串再多一次结束判断。排序后任意两串 LCP 等于其间相邻 LCP 的最小值，用单调栈求所有区间最小值之和。

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
