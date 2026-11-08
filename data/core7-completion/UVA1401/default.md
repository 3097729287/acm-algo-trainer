## UVA1401 Remember the Word

原题：[UVA1401](https://www.luogu.com.cn/problem/UVA1401)

### 思路

dp[i] 表示后缀 i..末尾的分词数。从每个 i 沿字典 Trie 向右匹配，遇到一个完整单词就把后面的 dp 加进来，模 20071027。

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
