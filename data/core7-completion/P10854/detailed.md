## P10854 Ninelie

原题：[P10854](https://www.luogu.com.cn/problem/P10854)

### 从问题到算法

全串相同等价于所有相邻差异 d_i 都为零。翻转内部位置 p 会同时翻转 d_(p−1)、d_p，而允许操作的条件 a_(p−1)!=a_(p+1) 正好表示这两个差异位一个零、一个一。于是操作只是在差异数组中交换相邻 01 或 10，让一个边界移动一步。

翻转位置一可以消除最左边界 d_1，翻转位置 n 可以消除最右边界 d_(n−1)。原边界在位置 i 时，移到左端并删除需 i 次，移到右端需 n−i 次。

把 i<=n/2 的边界按 i 递增处理，依次翻转位置 i,i−1,…,1，先前边界已消除，不会挡路；把右半边界按 i 递减处理，依次翻转 i+1,…,n。两侧处理范围不冲突，每一步都满足合法条件。

总次数为 Σ(边界位置i)min(i,n−i)，最大不超过所有位置都出现边界时的 floor(n²/4)。n<=2000，所以不超过一百万，所有合法输入都有方案。

### 复杂度

时间和输出量 O(n²)，空间 O(n²)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, r;
    cin >> n >> r;
    vector<int> a(n);
    for (int &x : a)
        cin >> x;
    vector<int> boundary, operations;
    for (int i = 1; i < n; i++)
        if (a[i - 1] != a[i])
            boundary.push_back(i);
    for (int i : boundary)
        if (i <= n / 2)
            for (int p = i; p >= 1; p--)
                operations.push_back(p);
    for (int j = (int)boundary.size() - 1; j >= 0; j--) {
        int i = boundary[j];
        if (i > n / 2)
            for (int p = i + 1; p <= n; p++)
                operations.push_back(p);
    }
    cout << operations.size() << '\n';
    for (int p : operations)
        cout << p << ' ';
    cout << '\n';

    return 0;
}
```

### 实现提醒

保存原始边界位置；左侧从左往右处理，右侧从右往左；输出实际字符位置。
