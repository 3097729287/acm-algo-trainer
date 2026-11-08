## P3805 Manacher

原题：[P3805](https://www.luogu.com.cn/problem/P3805)

### 从问题到算法

odd[i] 包含中心字符，代表区间 i−odd[i]+1 到 i+odd[i]−1；even[i] 的中心在 i−1 与 i 之间，代表 i−even[i] 到 i+even[i]−1。因此对应长度分别为 2odd[i]−1 与 2even[i]。

维护已经求出的、右端最远的回文 [l,r]。若中心 i 在它内部，可以从镜像中心继承半径，但最多继承到 r；超出范围的部分再逐个比较。若 i 在外部，则从最小半径开始。

每次成功扩展到未知区域都会推动最右端，失败比较每个中心最多一次，所以总比较次数为线性。使用两套半径避免构造长度翻倍的带分隔符字符串，适合千万字符输入。

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
