## P4683 Type Printer

原题：[P4683](https://www.luogu.com.cn/problem/P4683)

### 从问题到算法

输入所有词必须被打印，Trie 中的每条边都至少向下经过一次。若最终停在深度 L 的结点，只有根到该结点的 L 条边可以不返回，其余边还必须向上走一次。因此操作数至少为 2·边数−L+词数，选择最深单词可使下界最小。

DFS 遍历 Trie，进入孩子时输出字母、回到父亲时输出减号，单词结点输出 P。每个结点把通向最深后代的孩子留到最后，这让整体最后打印的词具有最大深度。

遍历结束后去掉尾部所有减号，恰好省掉最终根路径的返回操作，达到下界。单词最长二十，递归深度安全；代码输出的操作序列用独立模拟器检查打印词集合和最小操作数。

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
