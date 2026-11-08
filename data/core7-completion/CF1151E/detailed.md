## CF1151E Number of Components

原题：[CF1151E](https://www.luogu.com.cn/problem/CF1151E)

### 从问题到算法

固定值域区间 [l,r]，只保留值落在其中的位置，原下标相邻且都保留的位置之间连边。这是路径图的一个森林，每个连通块恰好是一段，块数等于顶点数减边数。

对所有 [l,r] 求和时，固定一个值为 x 的位置。要保留它，l 可以从 1 到 x 选择，r 可以从 x 到 n 选择，贡献 x(n−x+1)。

固定两个相邻位置，值为 u、v。要同时保留，左界不超过较小值，右界不小于较大值，因此这条边被计入 min(u,v)(n−max(u,v)+1) 个区间。把所有点贡献加上、边贡献减去，就是答案。重复值与同一值出现多段都自然处理。

### 复杂度

时间 O(n)，空间 O(n)，也可只保存前一个值降为空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long long> a(n);
    long long ans = 0;
    for (auto &x : a) {
        cin >> x;
        ans += x * (n - x + 1);
    }
    for (int i = 1; i < n; i++)
        ans -= min(a[i - 1], a[i]) * (n - max(a[i - 1], a[i]) + 1);
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

相邻关系来自原下标；点减边；乘积与总答案用 long long。
