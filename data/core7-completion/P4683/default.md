## P4683 Type Printer

原题：[P4683](https://www.luogu.com.cn/problem/P4683)

### 思路

所有单词组成 Trie。每条非最终路径边至少走去回两次，最终停留路径只需走一次，所以选择最长根路径最后访问。遇到单词结点输出打印操作。

### 复杂度

设总字符数为 S，时间 O(26S)，空间 O(S)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    struct Node {
        array<int, 26> next{};
        bool terminal = false;
        int height = 0;
    };
    vector<Node> trie(1);
    while (n--) {
        string s;
        cin >> s;
        int v = 0;
        for (char c : s) {
            int x = c - 'a';
            if (!trie[v].next[x]) {
                trie[v].next[x] = trie.size();
                trie.emplace_back();
            }
            v = trie[v].next[x];
        }
        trie[v].terminal = true;
    }
    for (int v = (int)trie.size() - 1; v >= 0; v--)
        for (int u : trie[v].next)
            if (u)
                trie[v].height = max(trie[v].height, trie[u].height + 1);
    string ops;
    function<void(int)> dfs = [&](int v) {
        if (trie[v].terminal)
            ops += 'P';
        int last = -1;
        for (int c = 0; c < 26; c++)
            if (trie[v].next[c] &&
                (last < 0 || trie[trie[v].next[c]].height > trie[trie[v].next[last]].height))
                last = c;
        for (int c = 0; c < 26; c++)
            if (trie[v].next[c] && c != last) {
                ops += char('a' + c);
                dfs(trie[v].next[c]);
                ops += '-';
            }
        if (last >= 0) {
            ops += char('a' + last);
            dfs(trie[v].next[last]);
            ops += '-';
        }
    };
    dfs(0);
    while (!ops.empty() && ops.back() == '-')
        ops.pop_back();
    cout << ops.size() << '\n';
    for (char c : ops)
        cout << c << '\n';

    return 0;
}
```

### 实现提醒

最终不要求清空；最长分支最后走；P 也是一次操作。
