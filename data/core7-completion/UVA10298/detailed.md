## UVA10298 Power Strings

原题：[UVA10298](https://www.luogu.com.cn/problem/UVA10298)

### 从问题到算法

末尾的最长真前后缀长度为 b 时，字符串以位移 n−b 对齐的部分相等，所以 p=n−b 是最小周期。若长度恰好是周期的整数倍，就能完整切成相同的 p 长块。

若最小周期不能整除 n，不存在另一个更短且能整除 n 的完整重复块，否则它会诱导一个可完整覆盖的最小循环节，与当前周期不整除矛盾。也可由 KMP 周期定理得到这一结论。

前缀函数失配时沿 pi 回退，匹配时长度增加，所有回退总计线性。点号是结束标记，不参与计算。

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
