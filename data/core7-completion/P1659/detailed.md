## P1659 拉拉队排练

原题：[P1659](https://www.luogu.com.cn/problem/P1659)

### 从问题到算法

若中心最大回文长度为 L，它恰好提供长度 L、L−2、……、一的各一个回文。先用 count[L] 统计最大长度正好为 L 的中心个数。

降序扫描所有正奇数长度，累加 count 后的 running 就是当前长度的回文数量。需要的前 K 个一定先取较长长度；这一批取 min(K,running) 个，把长度的相应次方乘到答案，继续减少 K。

每个中心贡献的不同长度对应不同位置子串，不会重复统计。扫描结束仍有 K 未满足则回文总数不足，输出 −1。模数不必是质数，快速幂仅用乘法。

### 复杂度

时间 O(n+n log K)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

pair<vector<int>, vector<int>> manacher(const string &s) {
    int n = s.size();
    vector<int> odd(n), even(n);
    for (int i = 0, l = 0, r = -1; i < n; i++) {
        int k = i > r ? 1 : min(odd[l + r - i], r - i + 1);
        while (i - k >= 0 && i + k < n && s[i - k] == s[i + k])
            k++;
        odd[i] = k;
        if (i + k - 1 > r) {
            l = i - k + 1;
            r = i + k - 1;
        }
    }
    for (int i = 0, l = 0, r = -1; i < n; i++) {
        int k = i > r ? 0 : min(even[l + r - i + 1], r - i + 1);
        while (i - k - 1 >= 0 && i + k < n && s[i - k - 1] == s[i + k])
            k++;
        even[i] = k;
        if (i + k - 1 > r) {
            l = i - k;
            r = i + k - 1;
        }
    }
    return {move(odd), move(even)};
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long K;
    string s;
    cin >> n >> K >> s;
    auto [odd, even] = manacher(s);
    vector<long long> cnt(n + 1);
    for (int r : odd)
        cnt[2 * r - 1]++;
    const long long P = 19930726;
    auto power = [&](long long a, long long b) {
        long long r = 1;
        for (; b; b >>= 1, a = a * a % P)
            if (b & 1)
                r = r * a % P;
        return r;
    };
    long long active = 0, ans = 1;
    for (int length = n % 2 ? n : n - 1; length >= 1; length -= 2) {
        active += cnt[length];
        long long take = min(K, active);
        ans = ans * power(length, take) % P;
        K -= take;
        if (!K)
            break;
    }
    cout << (K ? -1 : ans) << '\n';

    return 0;
}
```

### 实现提醒

只统计奇回文；频次要向短长度累加；K 可能达到万亿。
