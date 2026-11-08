## CF797E Array Queries

原题：[CF797E](https://www.luogu.com.cn/problem/CF797E)

### 从问题到算法

位置 i 的下一跳为 i+a[i]+k，严格向右，所以固定 k 后可以从 n 到一递推 dp[i]=1+dp[next]，越界位置为零。

取 B≈sqrt(n)。对出现过的 k≤B，各花 O(n) 计算全部起点；对 k>B，每步至少移动 B+1，直接模拟最多 O(n/B) 次。两部分总量平衡。

先读完询问，将相同小 k 聚在一起。处理一组后即可覆盖旧 dp，无须保存 n×B 的大表。大参数的答案直接存到原询问编号，最后按输入顺序输出。

### 复杂度

时间 O(n√n+q√n)，空间 O(n+q)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> a(n + 1);
    for (int i = 1; i <= n; i++)
        cin >> a[i];
    int q;
    cin >> q;
    int B = sqrt(n) + 1;
    vector<vector<pair<int, int>>> small(B + 1);
    vector<int> ans(q), dp(n + 1);
    for (int i = 0; i < q; i++) {
        int p, k;
        cin >> p >> k;
        if (k <= B)
            small[k].push_back({p, i});
        else {
            int count = 0;
            for (; p <= n; p += a[p] + k)
                count++;
            ans[i] = count;
        }
    }
    for (int k = 0; k <= B; k++)
        if (!small[k].empty()) {
            for (int i = n; i >= 1; i--) {
                long long next = 1LL * i + a[i] + k;
                dp[i] = 1 + (next <= n ? dp[next] : 0);
            }
            for (auto [p, id] : small[k])
                ans[id] = dp[p];
        }
    for (int x : ans)
        cout << x << '\n';

    return 0;
}
```

### 实现提醒

下一位置严格更大；倒序 DP；离线分组节省平方根倍内存。
