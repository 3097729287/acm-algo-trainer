## P3370 字符串哈希

原题：[P3370](https://www.luogu.com.cn/problem/P3370)

### 从问题到算法

题目只需要判断字符串是否完全相同，不需要保留顺序，也不需要输出每种字符串的出现次数。集合正好提供去重语义。

读取每个字符串后插入 unordered_set：若此前已有相同内容，集合大小不变；否则新增一种。哈希用于选择桶，真正判等仍比较字符串内容，所以使用标准字符串键不会产生手写单模哈希那种碰撞判等错误。

最后 size 就是不同字符串数。预留桶容量可减少大量插入时的重建，但不影响正确性。

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
