## P10031 Xor with Gcd

原题：[P10031](https://www.luogu.com.cn/problem/P10031)

### 从问题到算法

异或中相同的值出现两次就抵消，因此只需知道每个 gcd 值的出现次数是奇数还是偶数。固定 n 的因数 d，令 i=d·j，那么 gcd(i,n)=d 等价于 gcd(j,n/d)=1，满足条件的 j 恰有 φ(n/d) 个。

当整数 k>2 时，与 k 互质的剩余类可以按 j 与 k−j 两两配对，且不会是同一个数，所以 φ(k) 为偶数。只有 φ(1)=1、φ(2)=1 为奇数。

对应 n/d=1 得到 d=n，始终保留；当 n 为偶数时，n/d=2 对应 d=n/2，也保留。其它全部抵消。整个过程不需要分解 n，适用于十的十八次方。

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
