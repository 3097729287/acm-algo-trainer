## P13461 Number Sets

原题：[P13461](https://www.luogu.com.cn/problem/P13461)

### 从问题到算法

两个不同的 p 倍数相差至少 p；如果 p 超过区间宽度 B−A，就不可能同时出现两个倍数，因此无需分解高达十的十二次方的端点。

对每个 P<=p<=B−A 的质数，算出区间内第一个倍数 first=ceil(A/p)p，再把后续 first+p、first+2p… 全部与 first 合并。这相当于把共享该质因子的所有数连成一组，所有质因子处理后，传递合并也由并查集自动完成。

并查集下标使用数值减 A，只需 B−A+1 个元素。每次合并成功就把集合数减一，按 Case #编号输出。

### 复杂度

每组时间 O(D log log D)，空间 O(D)，D=B−A。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct DSU {
    vector<int> p, size;
    explicit DSU(int n) : p(n), size(n, 1) { iota(p.begin(), p.end(), 0); }
    int find(int x) {
        while (p[x] != x) {
            p[x] = p[p[x]];
            x = p[x];
        }
        return x;
    }
    bool join(int a, int b) {
        a = find(a);
        b = find(b);
        if (a == b)
            return false;
        if (size[a] < size[b])
            swap(a, b);
        p[b] = a;
        size[a] += size[b];
        return true;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    for (int test = 1; test <= tests; test++) {
        long long a, b, minimum;
        cin >> a >> b >> minimum;
        int width = b - a;
        vector<char> composite(width + 1);
        DSU d(width + 1);
        int answer = width + 1;
        for (int p = 2; p <= width; p++)
            if (!composite[p]) {
                for (int j = p + p; j <= width; j += p)
                    composite[j] = 1;
                if (p < minimum)
                    continue;
                long long first = (a + p - 1) / p * p;
                for (long long x = first + p; x <= b; x += p)
                    if (d.join(first - a, x - a))
                        answer--;
            }
        cout << "Case #" << test << ": " << answer << '\n';
    }

    return 0;
}
```

### 实现提醒

只筛到区间宽度；端点运算用 long long；质因子阈值含等号。
