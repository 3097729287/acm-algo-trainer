## P3370 字符串哈希

原题：[P3370](https://www.luogu.com.cn/problem/P3370)

### 思路

把每个输入字符串插入 unordered_set，最后输出集合大小。标准容器遇到哈希冲突仍会比较完整字符串，因此不会把不同字符串误认为相同。

### 复杂度

平均时间 O(总输入字符数)，空间 O(不同字符串总长度)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    unordered_set<string> words;
    words.reserve(2 * n);
    while (n--) {
        string s;
        cin >> s;
        words.insert(s);
    }
    cout << words.size() << '\n';

    return 0;
}
```

### 实现提醒

按完整内容判等；不能只用字符串长度去重。
