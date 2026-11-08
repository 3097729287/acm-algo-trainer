## P3467 PLA-Postering

原题：[P3467](https://www.luogu.com.cn/problem/P3467)

### 从问题到算法

一个矩形建筑在连续横向范围内提供固定高度。高度下降后，超过新轮廓的那些建筑已经结束，必须弹出；它们不能跨过低谷继续当作同一块建筑。

弹完后，若栈顶高度等于当前高度，说明这一层可以继续使用，无需新建筑。若更低，则必须新增一个以当前高度为顶的矩形层。零高度不对应建筑，不能压入并计数。

这种贪心每次只在确有新层不可避免时计数，并让同高度尽量连续，因此取得最少建筑数。横坐标决定顺序，但矩形数量不依赖每段宽度。

### 复杂度

时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> stack = {0};
    int answer = 0;
    while (n--) {
        int x, h;
        cin >> x >> h;
        while (stack.back() > h)
            stack.pop_back();
        if (stack.back() < h) {
            stack.push_back(h);
            answer++;
        }
    }
    cout << answer << '\n';

    return 0;
}
```

### 实现提醒

输入包含横坐标与高度；同高不重复压栈；零高度不计。
