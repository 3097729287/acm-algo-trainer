## P5335 补退选

原题：[P5335](https://www.luogu.com.cn/problem/P5335)

### 从问题到算法

查询问的是过去任何事件之后的首次越界，不仅是当前人数。人数每次只能增加或减少一，因此首次超过 v 就是首次达到 v+1。为每个前缀保存一组按人数递增的首次到达时间，永远不删除历史。

姓名插入或删除时沿前缀树逐层加减当前人数。只有超过历史最高人数时，才追加当前事件编号。查询沿名字找到对应前缀，阈值用上次答案解码后，按人数直接索引历史；没有该记录则输出 −1。

长姓名可能形成大量只达到一次的节点。代码将首次达到一的时间直接放在节点里，只为达到二及以上的前缀分配额外历史数组；孩子采用兄弟链，字母只有十种，每层最多检查十项。

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
