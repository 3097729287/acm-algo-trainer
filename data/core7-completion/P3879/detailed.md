## P3879 阅读理解

原题：[P3879](https://www.luogu.com.cn/problem/P3879)

### 从问题到算法

查询要的是哪些文章包含这个词，同一文章中出现多次仍只输出一次。用单词到编号列表的映射建立倒排索引。

按文章 1 到 n 依次处理，同一个词的文章编号天然递增；当前词若已经在本文章出现，它列表的最后一个编号必定等于当前文章。因此仅比较末尾就能去掉本文章内的重复，无需给每篇文章另外建立一个集合。

查询存在的词时按列表顺序输出即可，既递增又不重复。不存在的词仍输出一个空行，以保留它对应的查询位置。

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
