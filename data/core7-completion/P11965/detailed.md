## P11965 等价消除

原题：[P11965](https://www.luogu.com.cn/problem/P11965)

### 从问题到算法

一次删除让同一字母出现次数减少二，不改变奇偶性，因此每个字母偶数次是必要条件；每种字母自行两两删除又证明它充分。题目没有要求被删除字符相邻。

设前缀状态 mask 的第 c 位为字母 c 出现次数的奇偶。子串 l..r 的状态是 prefix[r] xor prefix[l−1]，为零等价于两个前缀状态相同。

初始空前缀状态零出现一次。每读一个字母就翻转对应位，将之前相同状态的次数加到答案，再将当前状态次数加一。答案最多 n(n+1)/2，使用 long long。

### 复杂度

平均时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    string s;
    cin >> n >> s;
    unordered_map<int, long long> cnt;
    cnt.reserve(2 * n + 1);
    cnt[0] = 1;
    int mask = 0;
    long long ans = 0;
    for (char c : s) {
        mask ^= 1 << (c - 'a');
        ans += cnt[mask];
        cnt[mask]++;
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

删除字符不要求相邻；空前缀要预先加入；查询计数后再增加当前频次。
