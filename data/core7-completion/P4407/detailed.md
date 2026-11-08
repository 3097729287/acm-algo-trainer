## P4407 电子字典

原题：[P4407](https://www.luogu.com.cn/problem/P4407)

### 从问题到算法

编辑距离为一意味着恰好进行一次删除、插入或替换，反过来这三类操作产生的每个不同字典词与查询的距离都为一。因为查询词本身不在字典中，不会混入距离为零的情况。

长度至多二十，删除只有 L 种，替换至多 25L 种，插入至多 26(L+1) 种，数量很小。直接构造每个候选，查询 unordered_set 保存的完整字符串；该容器仍会在哈希冲突时比较实际内容，不会把冲突当相等。

相同候选可能由多个编辑位置产生，例如在重复字母串中删除任意一个相同字母，因此另用集合保存命中字典词，最后取集合大小，不能直接数命中次数。

### 复杂度

平均时间 O(M·26L²+NL)，空间 O(NL+26L²)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    unordered_set<string> dict;
    while (n--) {
        string s;
        cin >> s;
        dict.insert(s);
    }
    while (m--) {
        string s;
        cin >> s;
        if (dict.count(s)) {
            cout << -1 << '\n';
            continue;
        }
        unordered_set<string> found;
        auto test = [&](const string &v) {
            if (dict.count(v))
                found.insert(v);
        };
        for (int i = 0; i < (int)s.size(); i++) {
            test(s.substr(0, i) + s.substr(i + 1));
            string v = s;
            for (char c = 'a'; c <= 'z'; c++) {
                v[i] = c;
                test(v);
            }
        }
        for (int i = 0; i <= (int)s.size(); i++)
            for (char c = 'a'; c <= 'z'; c++)
                test(s.substr(0, i) + c + s.substr(i));
        cout << found.size() << '\n';
    }

    return 0;
}
```

### 实现提醒

先判断完全相等；命中单词要去重；插入位置包含末尾。
