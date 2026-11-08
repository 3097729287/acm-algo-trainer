## P1381 单词背诵

原题：[P1381](https://www.luogu.com.cn/problem/P1381)

### 思路

先统计文章中实际出现了多少种待背单词，再用双指针求包含这些种类的最短连续片段。字典之外的词仍占文章位置，但不增加覆盖种数。

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
