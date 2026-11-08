## CF808G Anthem of Berland

原题：[CF808G](https://www.luogu.com.cn/problem/CF808G)

### 从问题到算法

仅贪心地优先完成眼前一次出现，可能影响后续重叠，因此要保留不同的模式匹配状态。令 dp[j] 为处理当前文本前缀、KMP 状态为 j 时能得到的最多出现次数。

先由模式前缀函数建立自动机：每个状态与每个字母对应一个新状态，以及是否刚完成一次匹配。完成后把状态回退到 pi[m−1]，因为已经匹配的后缀还能作为下一次匹配开头。

固定字符只做对应转移；问号枚举二十六个字母，并对新状态取最大。每一份问号替换方案都沿着一条状态路径，不同路径落在相同状态时，仅保留更大得分，未来不会受损。最后取所有状态中的最大值。

长度乘积限制使 O(26|s||t|) 可行；若模式比文本还长，直接输出零。

### 复杂度

时间 O(26|s||t|)，空间 O(26|t|)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

vector<int> prefix(const string &s) {
    vector<int> p(s.size());
    for (int i = 1; i < (int)s.size(); i++) {
        int j = p[i - 1];
        while (j && s[i] != s[j])
            j = p[j - 1];
        if (s[i] == s[j])
            j++;
        p[i] = j;
    }
    return p;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string s, t;
    cin >> s >> t;
    int n = s.size(), m = t.size();
    if (m > n) {
        cout << 0 << '\n';
        return 0;
    }
    auto p = prefix(t);
    vector<array<int, 26>> next(m), gain(m);
    for (int state = 0; state < m; state++)
        for (int c = 0; c < 26; c++) {
            int v;
            if (t[state] - 'a' == c)
                v = state + 1;
            else
                v = state ? next[p[state - 1]][c] : 0;
            gain[state][c] = v == m;
            next[state][c] = v == m ? p[m - 1] : v;
        }
    const int neg = -1000000000;
    vector<int> dp(m, neg), updated(m);
    dp[0] = 0;
    for (char ch : s) {
        fill(updated.begin(), updated.end(), neg);
        int first = ch == '?' ? 0 : ch - 'a', last = ch == '?' ? 25 : first;
        for (int state = 0; state < m; state++)
            if (dp[state] >= 0)
                for (int c = first; c <= last; c++)
                    updated[next[state][c]] =
                        max(updated[next[state][c]], dp[state] + gain[state][c]);
        dp.swap(updated);
    }
    cout << *max_element(dp.begin(), dp.end()) << '\n';

    return 0;
}
```

### 实现提醒

完整匹配后保留 border；问号只改变当前位置；利用长度乘积保证。
