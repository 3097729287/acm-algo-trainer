## P4391 Radio Transmission 无线传输

原题：[P4391](https://www.luogu.com.cn/problem/P4391)

### 思路

求整个字符串的最长真前后缀长度 b，答案为 n−b。电台发送的最后一轮可以不完整，因此不要求周期长度整除 n。

### 复杂度

时间 O(n)，空间 O(n)。

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

    int n;
    string s;
    cin >> n >> s;
    auto p = prefix(s);
    cout << n - p.back() << '\n';

    return 0;
}
```

### 实现提醒

无需检验 n%周期；输入含给定长度。
