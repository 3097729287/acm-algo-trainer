## P2532 树屋阶梯

原题：[P2532](https://www.luogu.com.cn/problem/P2532)

### 从问题到算法

总高为 n 的阶梯中，考察与对角阶梯边界接触并分隔两侧的那块钢材，它的位置把其余结构分成规模 i 与 n−1−i 的两个更小阶梯。选定分界后，两侧可以独立搭建，贡献 C_i·C_(n−1−i)，所有分界互不重复。

因此 C_0=1，C_n=Σ(i=0..n−1)C_iC_(n−1−i)，是 Catalan 递推。闭式 C_n=C(2n,n)/(n+1) 进一步给出 C_i=C_(i−1)·(4i−2)/(i+1)。

n 可到五百，固定六十四位整数不够。程序用十亿进制大整数，只需乘小整数和除小整数；先乘后除，每一步都精确整除。样例 n=3 对应 5 种。

### 复杂度

O(n) 次高精度小整数乘除，空间 O(答案位数)。

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

    int n;
    cin >> n;
    Big answer(1);
    for (int i = 1; i <= n; i++) {
        answer.multiply(4 * i - 2);
        answer.divide(i + 1);
    }
    cout << answer << '\n';

    return 0;
}
```

### 实现提醒

初始 C_0=1；不能用浮点近似；除法必须在乘法之后。
