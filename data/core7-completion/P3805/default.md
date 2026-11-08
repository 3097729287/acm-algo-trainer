## P3805 Manacher

原题：[P3805](https://www.luogu.com.cn/problem/P3805)

### 思路

分别计算字符为中心的奇回文半径和字符间隙为中心的偶回文半径。利用当前最右回文的对称位置初始化，只扩展尚未确定的部分，最终取最大长度。

### 复杂度

时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

pair<vector<int>, vector<int>> manacher(const string &s) {
    int n = s.size();
    vector<int> odd(n), even(n);
    for (int i = 0, l = 0, r = -1; i < n; i++) {
        int k = i > r ? 1 : min(odd[l + r - i], r - i + 1);
        while (i - k >= 0 && i + k < n && s[i - k] == s[i + k])
            k++;
        odd[i] = k;
        if (i + k - 1 > r) {
            l = i - k + 1;
            r = i + k - 1;
        }
    }
    for (int i = 0, l = 0, r = -1; i < n; i++) {
        int k = i > r ? 0 : min(even[l + r - i + 1], r - i + 1);
        while (i - k - 1 >= 0 && i + k < n && s[i - k - 1] == s[i + k])
            k++;
        even[i] = k;
        if (i + k - 1 > r) {
            l = i - k;
            r = i + k - 1;
        }
    }
    return {move(odd), move(even)};
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string s;
    cin >> s;
    auto [odd, even] = manacher(s);
    int ans = 0;
    for (int i = 0; i < (int)s.size(); i++)
        ans = max({ans, 2 * odd[i] - 1, 2 * even[i]});
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

奇半径含中心，偶半径不含；偶回文镜像下标与奇回文不同；不要逐个中心从零扩展。
