## P14253 旅行（trip）

原题：[P14253](https://www.luogu.com.cn/problem/P14253)

### 从问题到算法

令 S[0]=0、S[i]=a1+…+ai。对起点 l，子段的零前缀恰好对应 S[j]=S[l−1] 的后续位置 j。固定 l 后，延长右端不会减少零的个数，因此可以一直取到 n。

若某个前缀和值共出现 f 次，从它第一次出现的位置之后开始，恰好能得到 f−1 个零前缀；其它起点不可能得到更多。对所有前缀和值取最大频次即可，S[0] 也必须计入。

代码使用带随机混合的整数哈希，避免简单整型哈希在特殊构造输入上退化。前缀和可能达到万亿，使用 long long。

### 复杂度

每组期望时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct Hash {
    static uint64_t mix(uint64_t x) {
        x += 0x9e3779b97f4a7c15ULL;
        x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9ULL;
        x = (x ^ (x >> 27)) * 0x94d049bb133111ebULL;
        return x ^ (x >> 31);
    }
    size_t operator()(long long x) const {
        static const uint64_t seed = chrono::steady_clock::now().time_since_epoch().count();
        return mix(x + seed);
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        int n;
        cin >> n;
        unordered_map<long long, int, Hash> cnt;
        cnt.reserve(2 * n + 1);
        cnt[0] = 1;
        long long sum = 0;
        int ans = 0;
        for (int i = 0; i < n; i++) {
            long long x;
            cin >> x;
            sum += x;
            ans = max(ans, ++cnt[sum] - 1);
        }
        cout << ans << '\n';
    }

    return 0;
}
```

### 实现提醒

包含 S[0]=0；答案是频次减一；每组重新清空。
