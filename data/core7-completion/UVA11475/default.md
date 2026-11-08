## UVA11475 Extend to Palindrome

原题：[UVA11475](https://www.luogu.com.cn/problem/UVA11475)

### 思路

只允许向末尾添加字符，故保留原串最长的回文后缀，把前面剩余部分反转后追加。用反串与原串构造 KMP 前缀函数求该后缀长度。

### 复杂度

每串时间 O(n)，空间 O(n)。

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

    string s;
    while (cin >> s) {
        string rev = s;
        reverse(rev.begin(), rev.end());
        int len = prefix(rev + '#' + s).back();
        cout << s << rev.substr(len) << '\n';
    }

    return 0;
}
```

### 实现提醒

求最长回文后缀而非前缀；输入到 EOF；保留原串。
