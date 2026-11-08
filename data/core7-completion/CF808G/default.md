## CF808G Anthem of Berland

原题：[CF808G](https://www.luogu.com.cn/problem/CF808G)

### 思路

状态记录已经处理的文本前缀，以及当前匹配的模式前缀长度。问号枚举替换字母，完成一次模式就增加答案并回退到最长 border，以允许重叠。题目保证两串长度乘积不超过一千万。

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
