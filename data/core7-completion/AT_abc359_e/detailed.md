## AT_abc359_e Water Tank

原题：[AT_abc359_e](https://www.luogu.com.cn/problem/AT_abc359_e)

### 从问题到算法

水向左填满时，第 i 次需要经过的容量可按左端点分解，每个区间 [j,i] 的贡献是其中最高挡板高度，因此需要维护 Σ(j<=i)max(h[j..i])，再加一使水第一次越过当前目标。

栈中一组 (height,count) 表示 count 个连续后缀拥有相同最大值。新高度 h 会把所有旧最大值不超过 h 的后缀统一抬高到 h，所以把这些栈顶组弹掉，从总和中减旧贡献，并累计它们的 count。

再把只含当前项的后缀计入，形成新组 (h,合计count)，加入 h×count 到总和。剩余更高组不变。每组最多入栈和出栈一次，线性维护全部答案。

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
    vector<pair<long long, long long>> stack;
    long long sum = 0;
    for (int i = 0; i < n; i++) {
        long long h;
        cin >> h;
        long long count = 1;
        while (!stack.empty() && stack.back().first <= h) {
            auto [value, number] = stack.back();
            stack.pop_back();
            sum -= value * number;
            count += number;
        }
        stack.push_back({h, count});
        sum += h * count;
        cout << sum + 1 << (i + 1 == n ? '\n' : ' ');
    }

    return 0;
}
```

### 实现提醒

每个新项本身增加一个后缀；相等高度也合并；最后答案加一。
