## P4824 Censoring S

原题：[P4824](https://www.luogu.com.cn/problem/P4824)

### 从问题到算法

删除一个出现后，原来两侧的字符会接到一起，可能产生新的出现，所以不能只在原串上标记所有匹配位置。应实时维护删除后的字符串。

用字符串模拟栈，另一个栈保存加入每个字符后的 KMP 匹配长度。新字符到来时，从当前长度沿前缀函数回退，再尝试扩展，随后把字符和新长度压入。若长度达到模式长度，删除栈尾同样多的字符与状态。

删除后恢复到新的栈顶状态，恰好等于剩余字符串对应的 KMP 状态，因此后续能发现跨删除边界的新匹配。每个字符只入栈一次、出栈至多一次；KMP 回退总量也线性。

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
