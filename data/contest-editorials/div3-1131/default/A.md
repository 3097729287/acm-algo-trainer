## A. Fraction and Six

### 题意

[原题链接](https://codeforces.com/contest/2278/problem/A)

分子字符串 $p$、分母字符串 $q$ 都由小写字母组成，每个字符表示一个相乘的变量。同字母可一对一约掉，剩余字母可以重排。判断能否让分母为空、分子恰好剩下 $\texttt{six}$。每个字符串的长度均在一到一百之间。



### 思路

只需检查：对每个字母，分子次数减去分母次数，是否恰好等于它在 $\texttt{six}$ 中的次数。

例如 $p=\texttt{sinx}$、$q=\texttt{n}$：两边各一个 $n$ 抵消，剩下 $s$、$i$、$x$ 各一个，重排即为目标。因此顺序不用模拟，但次数必须精确匹配；多一个字符或分母少约掉一个字符都会失败。

用二十六个计数槽分别保存 $a$ 到 $z$ 的次数差。遍历分子时加一，遍历分母时减一，再把目标 six 的三个字符各减一；最后所有槽都应为零。必要性来自同字母才能约分；反过来，次数关系成立就能将每个分母字符配给一个相同的分子字符，恰好留下目标，所以条件也充分。

代码中 $\verb@int count[26] = {}@$ 将二十六个计数初始化为零；$\verb@c - 'a'@$ 把小写字母映射到零到二十五，例如 $b$ 对应一。负值说明分子缺少所需字符，正值说明还有多余字符，两者都不允许。$\verb@for (char c : p)@$ 按顺序读出字符串的每个字符。

时间为 $O(n+m+26)$，计数数组使用 $O(26)$ 空间，输入字符串另用 $O(n+m)$ 空间。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n, m;
        string p, q;
        cin >> n >> m >> p >> q;
        int count[26] = {};
        for (char c : p) ++count[c - 'a'];
        for (char c : q) --count[c - 'a'];
        // 再扣掉目标，所有差值为零才表示分母清空、分子恰好剩 six。
        for (char c : string("six")) --count[c - 'a'];
        bool ok = true;
        for (int value : count) if (value != 0) ok = false;
        cout << (ok ? "YES" : "NO") << '\n';
    }
}
```

### 易错点

不能把字符串当作一个整体变量，也不能只比较长度差为三。约分后既不能留有分母字符，也不能让分子多出字符。
