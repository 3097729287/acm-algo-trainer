## P3375 KMP

原题：[P3375](https://www.luogu.com.cn/problem/P3375)

### 思路

先求模式串的前缀函数。扫描文本时，失配沿前缀函数回退，匹配到整个模式就输出起点并继续回退，以保留重叠匹配。最后输出模式串前缀函数。

### 复杂度

时间 O(|文本|+|模式|)，空间 O(|模式|)。

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

    string text, pattern;
    cin >> text >> pattern;
    auto p = prefix(pattern);
    int j = 0;
    for (int i = 0; i < (int)text.size(); i++) {
        while (j && text[i] != pattern[j])
            j = p[j - 1];
        if (text[i] == pattern[j])
            j++;
        if (j == (int)pattern.size()) {
            cout << i - j + 2 << '\n';
            j = p[j - 1];
        }
    }
    for (int x : p)
        cout << x << ' ';
    cout << '\n';

    return 0;
}
```

### 实现提醒

匹配输出使用 1 起始位置；完整匹配后回退而非清零。
