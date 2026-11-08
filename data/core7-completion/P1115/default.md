## P1115 最大子段和

原题：[P1115](https://www.luogu.com.cn/problem/P1115)

### 思路

当前最优非空子段要么从本项重新开始，要么延长上一位置结尾的最优子段。维护 ending=max(a[i],ending+a[i])，全局答案取所有 ending 的最大值。

### 复杂度

时间 O(n)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    long long ending = 0, answer = LLONG_MIN;
    while (n--) {
        long long x;
        cin >> x;
        ending = max(x, ending + x);
        answer = max(answer, ending);
    }
    cout << answer << '\n';

    return 0;
}
```

### 实现提醒

子段非空；全负数组返回最大负数；和使用六十四位。
