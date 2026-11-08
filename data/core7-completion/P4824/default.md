## P4824 Censoring S

原题：[P4824](https://www.luogu.com.cn/problem/P4824)

### 思路

逐字读入原串，把字符与当前模式匹配长度一起压栈。每当匹配完整个待删串，就弹出对应长度；新的匹配状态从栈顶恢复。

看原串 aababa、模式 aba：第一次删掉末尾 aba 后，栈里还剩 a，匹配长度应恢复为 1；后面读入 ba 会再次删除。若错误地清零，就会漏掉第二次匹配。

![删除后为什么要恢复栈顶状态](assets/stack-kmp.svg)

### 复杂度

时间 O(|原串|+|待删串|)，空间 O(|原串|+|待删串|)。

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

    string s, t;
    cin >> s >> t;
    auto p = prefix(t);
    string out;
    vector<int> state;
    for (char c : s) {
        int j = state.empty() ? 0 : state.back();
        while (j && c != t[j])
            j = p[j - 1];
        if (c == t[j])
            j++;
        out.push_back(c);
        state.push_back(j);
        if (j == (int)t.size()) {
            out.resize(out.size() - t.size());
            state.resize(state.size() - t.size());
        }
    }
    cout << out << '\n';

    return 0;
}
```

### 实现提醒

删除后恢复旧栈顶状态；模式可能重叠；不要每次重新扫描完整结果。
