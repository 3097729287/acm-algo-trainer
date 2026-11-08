## UVA11475 Extend to Palindrome

原题：[UVA11475](https://www.luogu.com.cn/problem/UVA11475)

### 从问题到算法

假设原串分为 A+B，其中 B 是回文，那么追加 reverse(A) 后得到 A+B+reverse(A)，显然是回文。要添加最少，就要让 B 尽可能长。

令 rev=reverse(s)，对 rev+# +s 求前缀函数。末尾的 border 同时是 rev 的前缀和 s 的后缀，意味着这段后缀等于自身反转，因此正好是最长回文后缀。分隔符防止匹配越过反串边界。

答案可以直接输出原串，再输出 rev 从该回文长度之后的部分。输入多行直到 EOF，每个串单独处理，单字符与原本就是回文的串无需添加。

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
