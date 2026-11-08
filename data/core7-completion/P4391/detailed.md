## P4391 Radio Transmission 无线传输

原题：[P4391](https://www.luogu.com.cn/problem/P4391)

### 从问题到算法

如果一个长度为 n 的字符串可以由长度 p 的循环节生成，那么第 p 个字符之后的部分，应与从开头开始的 n−p 个字符相等，这正是长度为 n−p 的 border。

反过来，若前 n−p 个字符等于后 n−p 个字符，就有 s[i]=s[i−p] 对所有 i>=p 成立，所以首 p 个字符不断重复即可生成整段接收内容。最短周期对应最长 border，故 p=n−pi[n−1]。

接收可能在某个循环节中途停止，所以不能套用“若 n 不能整除 p 就取 n”的整串幂判断。这里即使没有整除关系，p 仍是合法答案。

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
