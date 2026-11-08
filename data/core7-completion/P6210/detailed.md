## P6210 Easy Math Problems

原题：[P6210](https://www.luogu.com.cn/problem/P6210)

### 从问题到算法

因为 gcd(x+n,n)=gcd(x,n)，合法性每 n 个数重复一次。预处理 prefix[i] 表示 1 到 i 中 gcd 不超过 c 的个数，令 total=prefix[n]。

第 f 小的数，先对 f−1 做 total 的除法。商 q 表示前面完整经过多少个周期，余数 r 表示本周期中从零开始的排名。二分找到 prefix[pos]>=r+1 的最小 pos，答案为 qn+pos。计数 F(X) 则把 X 除以 n，得到商 q 与余数 r，返回 q·total+prefix[r]。最终第二问为 F(R)−F(L−1)。

为避免对一千万个数逐个求 gcd，使用线性筛递推 g[i·p]=g[i]·gcd(p,n/g[i])。p 为质数，最后的 gcd 只有一或 p 两种，常数时间即可；筛完把 g 原地改成合法前缀计数，节省内存。

超长的 f、L、R 用十亿进制大整数表示，仅需除小整数、乘小整数和减法，时间与输入位数成正比，不把十万位数字转换为固定整数。

### 复杂度

时间 O(n+输入总位数+log n)，空间 O(n+输入总位数)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct Big {
    static const int base = 1000000000;
    vector<int> d;
    Big(long long x = 0) {
        do {
            d.push_back(x % base);
            x /= base;
        } while (x);
    }
    explicit Big(string s) {
        for (int r = s.size(); r > 0; r -= 9)
            d.push_back(stoi(s.substr(max(0, r - 9), min(9, r))));
        trim();
    }
    void trim() {
        while (d.size() > 1 && d.back() == 0)
            d.pop_back();
    }
    void multiply(long long x) {
        long long carry = 0;
        for (int &v : d) {
            long long z = v * x + carry;
            v = z % base;
            carry = z / base;
        }
        while (carry) {
            d.push_back(carry % base);
            carry /= base;
        }
        trim();
    }
    long long divide(long long x) {
        long long rem = 0;
        for (int i = (int)d.size() - 1; i >= 0; i--) {
            long long z = rem * base + d[i];
            d[i] = z / x;
            rem = z % x;
        }
        trim();
        return rem;
    }
    void add(long long x) {
        long long carry = x;
        for (int i = 0; carry; i++) {
            if (i == (int)d.size())
                d.push_back(0);
            long long z = d[i] + carry;
            d[i] = z % base;
            carry = z / base;
        }
    }
    void addBig(const Big &b) {
        int n = max(d.size(), b.d.size());
        d.resize(n, 0);
        long long carry = 0;
        for (int i = 0; i < n; i++) {
            long long z = (long long)d[i] + (i < (int)b.d.size() ? b.d[i] : 0) + carry;
            d[i] = z % base;
            carry = z / base;
        }
        if (carry)
            d.push_back(carry);
    }
    void subtract(const Big &b) {
        int borrow = 0;
        for (int i = 0; i < (int)d.size(); i++) {
            long long z = (long long)d[i] - (i < (int)b.d.size() ? b.d[i] : 0) - borrow;
            borrow = z < 0;
            if (borrow)
                z += base;
            d[i] = z;
        }
        trim();
    }
    friend ostream &operator<<(ostream &out, const Big &b) {
        out << b.d.back();
        for (int i = (int)b.d.size() - 2; i >= 0; i--)
            out << setw(9) << setfill('0') << b.d[i];
        return out;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, c;
    string sf, sl, sr;
    cin >> n >> c >> sf >> sl >> sr;
    vector<int> least(n + 1), g(n + 1), primes;
    g[1] = 1;
    for (int i = 2; i <= n; i++) {
        if (!least[i]) {
            least[i] = i;
            primes.push_back(i);
            g[i] = (n % i == 0 ? i : 1);
        }
        for (int p : primes) {
            if (p > least[i] || 1LL * i * p > n)
                break;
            least[i * p] = p;
            g[i * p] = g[i] * ((n / g[i]) % p == 0 ? p : 1);
        }
    }
    for (int i = 1; i <= n; i++)
        g[i] = g[i - 1] + (g[i] <= c);
    int total = g[n];
    Big f(sf);
    f.subtract(Big(1));
    int rank = f.divide(total) + 1;
    int position = lower_bound(g.begin() + 1, g.end(), rank) - g.begin();
    f.multiply(n);
    f.add(position);
    cout << f << '\n';
    auto count = [&](Big value) {
        int rem = value.divide(n);
        value.multiply(total);
        value.add(g[rem]);
        return value;
    };
    Big left(sl);
    left.subtract(Big(1));
    Big answer = count(Big(sr));
    answer.subtract(count(left));
    cout << answer << '\n';

    return 0;
}
```

### 实现提醒

第 f 项先用 f−1 分周期；周期内二分第一个达到排名的位置；L−1 用高精度减法。
