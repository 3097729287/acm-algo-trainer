## UVA10298 Power Strings

原题：[UVA10298](https://www.luogu.com.cn/problem/UVA10298)

### 思路

设 p=n−pi[n−1]。若 n 能被 p 整除，原串由 n/p 个循环节组成；否则只能看成自身重复一次。逐个处理直到读到点号。

### 复杂度

每串时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string s;
    while (cin >> s && s != ".") {
        int n = s.size();
        vector<int> pi(n);
        for (int i = 1; i < n; i++) {
            int j = pi[i - 1];
            while (j && s[i] != s[j])
                j = pi[j - 1];
            if (s[i] == s[j])
                j++;
            pi[i] = j;
        }
        int p = n - pi.back();
        cout << (n % p ? 1 : n / p) << '\n';
    }

    return 0;
}
```

### 实现提醒

必须检查 n%p；前后缀不能等于整个串；点号停止。
