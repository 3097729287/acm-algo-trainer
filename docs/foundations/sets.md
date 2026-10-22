# set、multiset 与有序邻居

`set<T>` 保留互不相同的元素并按比较器排序，适合动态判断存在、查前驱后继；`multiset<T>` 允许重复值。插入、按键查找和成员二分通常为 $O(\log n)$，空间为 $O(n)$。`unordered_set` 是哈希集合，平均查询快，但没有大小顺序。

```cpp
set<int> s{2, 5, 9};
auto it = s.lower_bound(6); // 指向 9，第一个 >=6 的数
if (it != s.end()) cout << *it;
if (it != s.begin()) cout << *prev(it); // 前驱是 5
```

`lower_bound` 等于 `end()` 表示没有更大的候选；它仍可能有前驱。等于 `begin()` 表示没有前驱，不能再向前移动。空集合尤其要先检查。

`multiset` 中 `erase(value)` 删除所有等于该值的项；只删一个应先 `find`，确认找到后 `erase(it)`。`set` 会自动去重，若多个相同记录必须各算一次，就不能直接把它们塞进普通集合后拿集合长度作答案。

关联容器的迭代器不支持相减。查询边界位置快，不等于“边界前有几个元素”也能快；对 `set` 调 `distance(begin,it)` 可能走过线性多个节点。大量秩查询可考虑离散化加树状数组或支持秩的数据结构。
