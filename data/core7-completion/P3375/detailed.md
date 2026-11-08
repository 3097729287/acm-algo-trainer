## P3375 KMP

原题：[P3375](https://www.luogu.com.cn/problem/P3375)

### 从问题到算法

前缀函数 pi[i] 表示模式前缀 0…i 的最长相等真前后缀长度。计算时令 j=pi[i−1]，若新字符不能接在长度 j 的前缀之后，就退到 pi[j−1]，直到能匹配或 j 为零。

扫描文本时，j 同样表示已匹配的模式前缀长度。匹配成功就 j++，失配则沿同一条前后缀链回退。被跳过的前缀不可能匹配，因为它们不是当前已匹配串的后缀。每个字符至多使 j 前进一步，回退总次数也线性。

当 j 等于模式长度时，一次匹配在当前文本下标结束，转换为从一开始的起点输出。随后令 j=pi[j−1]，这样 aaa 在 aaaaa 中的重叠出现不会遗漏。

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
