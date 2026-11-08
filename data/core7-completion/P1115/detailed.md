## P1115 最大子段和

原题：[P1115](https://www.luogu.com.cn/problem/P1115)

### 从问题到算法

固定右端 i 后，合法子段只有两类：只选 a[i]，或者在某个以 i−1 结尾的子段后追加 a[i]。第二类中只有原来和最大的前缀值得保留，因为追加的数完全相同。

所以 ending[i]=max(a[i],ending[i−1]+a[i])。再对所有右端取最大值，就覆盖了全部连续子段。只依赖上一项，空间可以压成两个变量。

子段必须非空，不能把全局答案初始化成零，否则全为负数时会错误地选空段。

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
