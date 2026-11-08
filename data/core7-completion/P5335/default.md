## P5335 补退选

原题：[P5335](https://www.luogu.com.cn/problem/P5335)

### 思路

维护每个前缀当前学生数。人数第一次升到 h 时，记录事件编号。查询人数曾经超过 v 的最早时间，直接取第一次达到 v+1 的记录；退课只改当前人数。

### 复杂度

设所有操作字符串总长为 S，时间 O(10S)，空间 O(S)。

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
        int child = -1, next = -1, letter = 0, count = 0, first = 0, history = -1;
    };
    vector<Node> trie(1);
    trie.reserve(60LL * n + 1);
    vector<vector<int>> history;
    long long last = 0;
    for (int event = 1; event <= n; event++) {
        int type;
        string s;
        cin >> type >> s;
        int v = 0;
        bool found = true;
        for (char c : s) {
            int u = trie[v].child;
            while (u >= 0 && trie[u].letter != c - 'a')
                u = trie[u].next;
            if (u < 0) {
                if (type == 3) {
                    found = false;
                    break;
                }
                u = trie.size();
                Node node;
                node.letter = c - 'a';
                node.next = trie[v].child;
                trie.push_back(node);
                trie[v].child = u;
            }
            v = u;
            if (type != 3) {
                trie[v].count += type == 1 ? 1 : -1;
                if (trie[v].count == 1 && !trie[v].first)
                    trie[v].first = event;
                else if (trie[v].count >= 2) {
                    int h = trie[v].history;
                    if (h < 0) {
                        h = history.size();
                        history.push_back({});
                        trie[v].history = h;
                    }
                    if (trie[v].count > (int)history[h].size() + 1)
                        history[h].push_back(event);
                }
            }
        }
        if (type == 3) {
            long long a, b, c;
            cin >> a >> b >> c;
            long long threshold = ((__int128)a * llabs(last) + b) % c;
            last = -1;
            if (found) {
                if (threshold == 0 && trie[v].first)
                    last = trie[v].first;
                else if (threshold >= 1 && trie[v].history >= 0) {
                    auto &h = history[trie[v].history];
                    if (threshold - 1 < (long long)h.size())
                        last = h[threshold - 1];
                }
            }
            cout << last << '\n';
        }
    }

    return 0;
}
```

### 实现提醒

查询也占事件编号；退课保留历史；解码用上次答案绝对值；同名学生分别计数。
