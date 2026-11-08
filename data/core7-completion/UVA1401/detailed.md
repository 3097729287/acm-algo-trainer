## UVA1401 Remember the Word

原题：[UVA1401](https://www.luogu.com.cn/problem/UVA1401)

### 从问题到算法

每个划分有唯一第一个单词。若 s[i..j] 是字典词，则这个选择的方案数为 dp[j+1]；对所有可行单词求和即可。空后缀有一种划分，设 dp[n]=1。

从右向左计算 i，Trie 从根开始逐字走，若无对应边立即停止，若到达单词结点便加 dp[j+1]。这样避免为每个字典词重复比较相同前缀。

字典表示可用词集合，相同单词只应标为同一个终止结点，不能因重复输入虚增方案。每组读一个目标串和词数，直到文件结束，按 Case 编号输出。

### 复杂度

设最长词长 L、字典总长 S，时间 O(S+nL)，空间 O(S+n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string s;
    int caseNo = 0;
    while (cin >> s) {
        int count;
        cin >> count;
        struct Node {
            array<int, 26> next{};
            bool terminal = false;
        };
        vector<Node> trie(1);
        int maxLength = 0;
        while (count--) {
            string word;
            cin >> word;
            maxLength = max(maxLength, (int)word.size());
            int v = 0;
            for (char c : word) {
                int x = c - 'a';
                if (!trie[v].next[x]) {
                    trie[v].next[x] = trie.size();
                    trie.emplace_back();
                }
                v = trie[v].next[x];
            }
            trie[v].terminal = true;
        }
        const int P = 20071027;
        int n = s.size();
        vector<int> dp(n + 1);
        dp[n] = 1;
        for (int i = n - 1; i >= 0; i--) {
            int v = 0;
            for (int j = i; j < n && j < i + maxLength; j++) {
                v = trie[v].next[s[j] - 'a'];
                if (!v)
                    break;
                if (trie[v].terminal) {
                    dp[i] += dp[j + 1];
                    if (dp[i] >= P)
                        dp[i] -= P;
                }
            }
        }
        cout << "Case " << ++caseNo << ": " << dp[0] << '\n';
    }

    return 0;
}
```

### 实现提醒

空后缀为一；词与词可以相接；每次累加取模。
