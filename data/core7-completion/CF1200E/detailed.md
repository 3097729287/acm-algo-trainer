## CF1200E Compress Words

原题：[CF1200E](https://www.luogu.com.cn/problem/CF1200E)

### 从问题到算法

前面合并出的结果不能改变顺序，只能把新单词接在末尾。可省略的字符必须同时是新词前缀和已有结果后缀，因此找最长这样的重合即可。

重合长度不会超过新词长度，所以从已有结果只截取最后 min(结果长度,新词长度) 个字符。构造 word+# +tail，分隔符不会出现在原字母串中，末位置的前缀函数就只能表示 word 的前缀与 tail 的后缀相等的长度。

把 word 从该长度之后的部分追加。每次处理长度至多新词长度的常数倍，因此总时间与全部输入长度成正比。结果使用 string 原地追加，避免反复复制整个旧结果。

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
