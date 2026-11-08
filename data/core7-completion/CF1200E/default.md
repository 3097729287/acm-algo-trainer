## CF1200E Compress Words

原题：[CF1200E](https://www.luogu.com.cn/problem/CF1200E)

### 思路

每次只需比较新单词的前缀与当前结果的后缀。对“新单词#当前结果的末尾部分”求前缀函数，得到最大重合长度，把新单词剩余部分追加。

### 复杂度

总时间 O(全部单词长度)，空间 O(结果长度+最长单词长度)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

vector<int> prefix(const string &s) {
    vector<int> p(s.size());
    for (int i = 1; i < (int)s.size(); i++) {
        int j = p[i - 1];
        while (j && s[i] != s[j])
            j = p[j - 1];
        if (s[i] == s[j])
            j++;
        p[i] = j;
    }
    return p;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    string result;
    while (n--) {
        string word;
        cin >> word;
        if (result.empty()) {
            result = word;
            continue;
        }
        string probe = word + '#' + result.substr(result.size() - min(result.size(), word.size()));
        int overlap = prefix(probe).back();
        result += word.substr(overlap);
    }
    cout << result << '\n';

    return 0;
}
```

### 实现提醒

只取当前结果的必要后缀；分隔符必须不在单词中。
