## P1255 数楼梯

原题：[P1255](https://www.luogu.com.cn/problem/P1255)

### 从问题到算法

每次走一级或两级。按最后一步分组，走一级的方案与到 i−1 级的方案一一对应，走两级则与到 i−2 级对应，两类不重不漏。

设 ways[0]=1，表示尚未上楼的唯一空方案；ways[1]=1。按楼梯级数递增计算。只需要前两项，用十亿进制的高精度数组做竖式加法，逐块相加并进位。

输出时先打印最高块，其余每块补满九位，不能直接把整个大数转回固定整数。

### 复杂度

O(n) 次高精度加法，空间 O(答案位数)。

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
    Big a(1), b(1);
    for (int i = 2; i <= n; i++) {
        Big next = a;
        next.addBig(b);
        a = b;
        b = next;
    }
    cout << b << '\n';

    return 0;
}
```

### 实现提醒

ways[0]=1；相邻两项需保存旧值；答案不对模数取余。
