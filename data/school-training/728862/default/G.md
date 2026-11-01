## G. String Task

### 题意

给定长度不超过 $100$ 的英文字符串，删除元音 `AOYEUI`，每个辅音前加点号，并把辅音改为小写。题面保证结果非空。

### 从零讲：char 与 string

**字符和字符串。** `char` 保存一个字符，`string` 保存字符序列；单引号如 `'.'` 是字符，双引号如 `"abc"` 是字符串。范围循环按顺序读取每个字符。`ch-'A'+'a'` 只用于已确认是大写英文字母的字符，不能用于任意文字。

### 思路

从左到右扫描字符串，先把大写字母转成小写；如果它属于 `"aoyeui"` 就跳过，否则输出一个点号和这个小写字母。

每个原字符独立决定是否保留，按原顺序输出，因此正好完成三项操作。注意 `'y'` 在本题也是元音。长度为 $m$ 时，时间 $O(m)$，除输入外额外空间 $O(1)$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string s;
    cin >> s;
    for (char ch : s) {
        if ('A' <= ch && ch <= 'Z') ch = char(ch - 'A' + 'a');
        bool vowel = ch == 'a' || ch == 'o' || ch == 'y'
                  || ch == 'e' || ch == 'u' || ch == 'i';
        // 只为保留的辅音输出点号，原字符顺序不变。
        if (!vowel) cout << '.' << ch;
    }
    cout << '\n';
}
```

### 易错点

元音包含 `'y'`；先统一大小写；元音前也不输出点号。
