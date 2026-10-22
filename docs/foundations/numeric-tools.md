# 数值工具：连续编号、累加与最值

这些工具分别处理“填连续编号”“合并数值”“比较候选”，使用前要看返回类型和范围。`iota`、`accumulate` 在 `<numeric>`，`min`、`max` 在 `<algorithm>`。

```cpp
vector<int> id(4);
iota(id.begin(), id.end(), 0); // 0、1、2、3，容器本来就要有 4 项
vector<int> a{1000000000, 1000000000, 1000000000};
long long sum = accumulate(a.begin(), a.end(), 0LL); // 3000000000
int best = max(3, 7); // 返回 7，不会修改原参数
```

`accumulate` 的初始值决定累加器类型；写零会先按 `int` 累加，即使最终接收变量是 `long long` 也来不及修复溢出。`min`、`max` 的候选通常应为同一类型；更新变量须写 `best=max(best,candidate)`，只调用 `max` 不会自动赋值。

`fill(a.begin(),a.end(),value)` 给每个已有元素赋值，时间 $O(n)$。`memset` 逐字节填充，不适合填任意整数一或大哨兵；用 `fill` 更能直接表达意图。初始化一个长为 $n$ 的数组也需要 $O(n)$，把它放进每轮循环可能成为主要耗时。

极大或极小哨兵要与合法答案范围区分，并给后续加法留下余地。若不可达值为 `INF`，不能不检查就算 `INF+weight`；计数题、最短路和最大值问题的初值含义不同，应从“尚未选任何东西”或“尚未到达”的状态推出来。
