## P3065 First! G

原题：[P3065](https://www.luogu.com.cn/problem/P3065)

### 从问题到算法

两个单词的字典序由第一个不同的字母决定。如果候选词经过字符 x 的分支，而同一节点还有字符 y 的其它分支，就必须规定 x 排在 y 前面。把所有这样的要求建成二十六个字母上的有向边。

若沿候选路径已经遇到一个单词终点，说明另一个单词是候选的真前缀。无论如何重排字母，短前缀都在前面，因此候选不可行。到候选终点后的更长扩展则没有影响，因为候选本身更短。

约束图无环时，存在一个拓扑序作为完整字母表，所有字典树分歧都按候选更小排列，候选就排在全部其它词前面；有环时相互矛盾，不可能实现。按输入顺序收集全部可行词。

### 复杂度

时间 O(L·26+n·26²)，空间 O(L+n)，L 为总词长。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct Node {
    array<int, 26> child = {};
    bool end = false;
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<string> words(n);
    vector<Node> trie(1);
    for (auto &s : words) {
        cin >> s;
        int v = 0;
        for (char c : s) {
            int b = c - 'a';
            if (!trie[v].child[b]) {
                trie[v].child[b] = trie.size();
                trie.push_back(Node());
            }
            v = trie[v].child[b];
        }
        trie[v].end = true;
    }
    vector<string> ans;
    for (auto &s : words) {
        bool edge[26][26] = {};
        bool ok = true;
        int v = 0;
        for (char c : s) {
            if (trie[v].end) {
                ok = false;
                break;
            }
            int x = c - 'a';
            for (int y = 0; y < 26; y++)
                if (y != x && trie[v].child[y])
                    edge[x][y] = true;
            v = trie[v].child[x];
        }
        int in[26] = {};
        for (int x = 0; x < 26; x++)
            for (int y = 0; y < 26; y++)
                in[y] += edge[x][y];
        queue<int> q;
        for (int x = 0; x < 26; x++)
            if (!in[x])
                q.push(x);
        int count = 0;
        while (!q.empty()) {
            int x = q.front();
            q.pop();
            count++;
            for (int y = 0; y < 26; y++)
                if (edge[x][y] && --in[y] == 0)
                    q.push(y);
        }
        if (ok && count == 26)
            ans.push_back(s);
    }
    cout << ans.size() << '\n';
    for (auto &s : ans)
        cout << s << '\n';

    return 0;
}
```

### 实现提醒

前缀冲突单独判断；约束是候选字母→其它字母；重边不重复加入入度。
