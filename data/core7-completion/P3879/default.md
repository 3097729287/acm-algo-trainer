## P3879 阅读理解

原题：[P3879](https://www.luogu.com.cn/problem/P3879)

### 思路

按文章编号依次读入，把单词映射到文章编号列表。若列表末尾已经是当前文章，就不重复加入；查询直接输出该词的列表。

### 复杂度

平均时间 O(输入总字符数+输出量)，空间 O(倒排索引大小)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    unordered_map<string, vector<int>> index;
    for (int article = 1; article <= n; article++) {
        int count;
        cin >> count;
        while (count--) {
            string s;
            cin >> s;
            auto &v = index[s];
            if (v.empty() || v.back() != article)
                v.push_back(article);
        }
    }
    int q;
    cin >> q;
    while (q--) {
        string s;
        cin >> s;
        auto it = index.find(s);
        if (it != index.end())
            for (int article : it->second)
                cout << article << ' ';
        cout << '\n';
    }

    return 0;
}
```

### 实现提醒

同一篇文章同词只记一次；编号顺序从 1；不存在输出空行。
