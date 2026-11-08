## UVA11019 Matrix Matcher

原题：[UVA11019](https://www.luogu.com.cn/problem/UVA11019)

### 从问题到算法

二维匹配可以先固定横向宽度：正文某行某个结束列的长度 Y 子串，若等于某个模式行，就记它的编号。重复模式行必须使用同一个编号，因为它们的内容没有区别。

将模式各行加入 AC 自动机，一次扫描每个正文行即可得到所有列的行编号；所有模式行等长，所以一个位置最多匹配一种不同模式行，不必遍历很多输出链。字符未命中任何模式行时记为 −1。

对每个结束列，沿行方向读取这些编号，使用 KMP 匹配模式行编号序列。命中 X 个编号就找到一个高 X、宽 Y 的模式子矩阵，之后按失配函数回退以支持重叠。自动机使用字节字符表，避免擅自限制原题未规定的字母范围。

### 复杂度

字节字符集大小固定 256，时间 O(NM+256XY)，空间 O(NM+256XY+M)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        int N, M;
        cin >> N >> M;
        vector<string> text(N);
        for (auto &s : text)
            cin >> s;
        int X, Y;
        cin >> X >> Y;
        struct Node {
            array<int, 256> next{};
            int fail = 0, id = -1;
        };
        vector<Node> ac(1);
        vector<int> pattern(X);
        int labels = 0;
        for (int i = 0; i < X; i++) {
            string s;
            cin >> s;
            int v = 0;
            for (unsigned char c : s) {
                if (!ac[v].next[c]) {
                    ac[v].next[c] = ac.size();
                    ac.emplace_back();
                }
                v = ac[v].next[c];
            }
            if (ac[v].id < 0)
                ac[v].id = labels++;
            pattern[i] = ac[v].id;
        }
        queue<int> q;
        for (int c = 0; c < 256; c++)
            if (ac[0].next[c])
                q.push(ac[0].next[c]);
        while (!q.empty()) {
            int v = q.front();
            q.pop();
            for (int c = 0; c < 256; c++) {
                int u = ac[v].next[c];
                if (u) {
                    ac[u].fail = ac[ac[v].fail].next[c];
                    q.push(u);
                } else
                    ac[v].next[c] = ac[ac[v].fail].next[c];
            }
        }
        vector<int> pi(X);
        for (int i = 1; i < X; i++) {
            int j = pi[i - 1];
            while (j && pattern[i] != pattern[j])
                j = pi[j - 1];
            if (pattern[i] == pattern[j])
                j++;
            pi[i] = j;
        }
        vector<int> vertical(M);
        long long ans = 0;
        for (auto &s : text) {
            int v = 0;
            for (int j = 0; j < M; j++) {
                v = ac[v].next[(unsigned char)s[j]];
                int id = ac[v].id, k = vertical[j];
                while (k && id != pattern[k])
                    k = pi[k - 1];
                if (id == pattern[k])
                    k++;
                if (k == X) {
                    ans++;
                    k = pi[k - 1];
                }
                vertical[j] = k;
            }
        }
        cout << ans << '\n';
    }

    return 0;
}
```

### 实现提醒

相同模式行共用编号；每列独立保存竖向匹配状态；重叠出现也计数。
