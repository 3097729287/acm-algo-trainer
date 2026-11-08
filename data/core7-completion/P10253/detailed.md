## P10253 说唱

原题：[P10253](https://www.luogu.com.cn/problem/P10253)

### 从问题到算法

把 x 的每位贡献展开，数字 d 在十的 j 次方位贡献 d(10^(j+1)−1)/9，因此 9f(x)=10x−S(x)。若 f(x)=y，就有 10x−9y=S(x)。

因为零≤S(x)≤9·digits(y)，候选 x 位于 ceil(9y/10) 到 (9y+9digits(y))/10 之间，只有线性多个。先以十进制数组计算 9y，去掉末位得到除十商，并按余数向上取整；同时维护 delta=10x−9y 与数位和。

每次 x 加一，delta 加十。数位和通过进位更新：每个被清零的九减九，最后进位位置加一。连续加一时所有进位总次数为候选数的常数倍，加上最初可能的一次长进位，总时间线性。若数位和等于 delta 即找到答案。

f(x) 严格递增，因为 x 本身递增且各个向下整除项都不减，所以找到的解必唯一；超过数位和上界仍无解则输出 −1。

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
