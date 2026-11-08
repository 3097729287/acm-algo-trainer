## P10253 说唱

原题：[P10253](https://www.luogu.com.cn/problem/P10253)

### 思路

设 S(x) 为十进制数位和，则 10x−S(x)=9y。x 从 ceil(9y/10) 起只需尝试 O(位数) 个值；大整数加一时顺便维护数位和，得到总线性时间。

### 复杂度

设输入十进制位数 d，时间 O(d)，空间 O(d)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        string y;
        cin >> y;
        vector<int> d;
        int carry = 0;
        for (int i = (int)y.size() - 1; i >= 0; i--) {
            int z = (y[i] - '0') * 9 + carry;
            d.push_back(z % 10);
            carry = z / 10;
        }
        if (carry)
            d.push_back(carry);
        int rem = d[0];
        d.erase(d.begin());
        if (d.empty())
            d.push_back(0);
        int sum = accumulate(d.begin(), d.end(), 0);
        auto increment = [&]() {
            int i = 0;
            while (i < (int)d.size() && d[i] == 9) {
                d[i] = 0;
                sum -= 9;
                i++;
            }
            if (i == (int)d.size())
                d.push_back(0);
            d[i]++;
            sum++;
        };
        int delta = 0;
        if (rem) {
            increment();
            delta = 10 - rem;
        }
        bool found = false;
        int bound = 9 * y.size();
        for (; delta <= bound; delta += 10) {
            if (sum == delta) {
                found = true;
                break;
            }
            increment();
        }
        if (!found) {
            cout << -1 << '\n';
            continue;
        }
        while (d.size() > 1 && !d.back())
            d.pop_back();
        for (int i = (int)d.size() - 1; i >= 0; i--)
            cout << d[i];
        cout << '\n';
    }

    return 0;
}
```

### 实现提醒

输入可以有五十万位；不能转固定整数；零的答案为零；维护的是 x 的数位和。
