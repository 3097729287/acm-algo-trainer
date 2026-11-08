## P4407 电子字典

原题：[P4407](https://www.luogu.com.cn/problem/P4407)

### 思路

若查询词已在字典中，输出 -1。否则枚举删除一个字符、替换一个字符、插入一个字符产生的所有字符串，用字典查找，并把命中的单词去重计数。

### 复杂度

平均时间 O(M·26L²+NL)，空间 O(NL+26L²)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    unordered_set<string> dict;
    while (n--) {
        string s;
        cin >> s;
        dict.insert(s);
    }
    while (m--) {
        string s;
        cin >> s;
        if (dict.count(s)) {
            cout << -1 << '\n';
            continue;
        }
        unordered_set<string> found;
        auto test = [&](const string &v) {
            if (dict.count(v))
                found.insert(v);
        };
        for (int i = 0; i < (int)s.size(); i++) {
            test(s.substr(0, i) + s.substr(i + 1));
            string v = s;
            for (char c = 'a'; c <= 'z'; c++) {
                v[i] = c;
                test(v);
            }
        }
        for (int i = 0; i <= (int)s.size(); i++)
            for (char c = 'a'; c <= 'z'; c++)
                test(s.substr(0, i) + c + s.substr(i));
        cout << found.size() << '\n';
    }

    return 0;
}
```

### 实现提醒

先判断完全相等；命中单词要去重；插入位置包含末尾。
