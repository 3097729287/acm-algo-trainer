## P1381 单词背诵

原题：[P1381](https://www.luogu.com.cn/problem/P1381)

### 从问题到算法

有些待背单词根本没有出现在文章中，无论截取多长都无法包含它们。所以第一问先求字典与文章出现词的交集种数 need，第二问只要求覆盖这 need 种。

用字典把待背词映射到编号，文章中的其它词标为 −1。右端逐词加入，某词频次从零变一时覆盖种数加一。当覆盖数达到 need 时，记录当前长度并不断右移左端：删除不需要的词，或删除仍有其它副本的词，直到缺少一种为止。

对于固定右端，这样得到最靠右且仍合法的左端，窗口最短；右端遍历全部位置，就覆盖了全局最优。每个位置至多入窗、出窗各一次。need=0 时直接输出两行零。

### 复杂度

平均时间 O(总输入字符数+n+m)，空间 O(n+m)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    unordered_map<string, int> dict;
    while (n--) {
        string s;
        cin >> s;
        if (!dict.count(s)) {
            int id = dict.size();
            dict[s] = id;
        }
    }
    int m;
    cin >> m;
    vector<int> a(m, -1), exists(dict.size());
    for (int i = 0; i < m; i++) {
        string s;
        cin >> s;
        auto it = dict.find(s);
        if (it != dict.end()) {
            a[i] = it->second;
            exists[it->second] = 1;
        }
    }
    int need = accumulate(exists.begin(), exists.end(), 0);
    cout << need << '\n';
    if (!need) {
        cout << 0 << '\n';
        return 0;
    }
    vector<int> freq(dict.size());
    int have = 0, l = 0, best = m + 1;
    for (int r = 0; r < m; r++) {
        if (a[r] >= 0 && freq[a[r]]++ == 0)
            have++;
        while (have == need) {
            best = min(best, r - l + 1);
            if (a[l] >= 0 && --freq[a[l]] == 0)
                have--;
            l++;
        }
    }
    cout << best << '\n';

    return 0;
}
```

### 实现提醒

按种类而非出现次数统计；无关词仍计入片段长度；need=0 特判。
