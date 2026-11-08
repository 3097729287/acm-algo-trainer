## P10031 Xor with Gcd

原题：[P10031](https://www.luogu.com.cn/problem/P10031)

### 思路

gcd(i,n)=d 的次数为 φ(n/d)。欧拉函数只有在参数为 1 或 2 时为奇数，因此 n 为奇数时答案为 n，n 为偶数时答案为 n 异或 n/2。

### 复杂度

每组时间 O(1)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int t;
    cin >> t;
    while (t--) {
        long long n;
        cin >> n;
        cout << (n % 2 ? n : n ^ (n / 2)) << '\n';
    }

    return 0;
}
```

### 实现提醒

偶数分支使用按位异或 ^，不是幂；n=1 输出 1。
