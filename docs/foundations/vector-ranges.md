# vector 的区间插入与内容复制

当一个新数组需要由几个已有片段拼成，可以用 `insert` 的区间形式。它复制的是源区间里的元素，不会把源数组中的元素拿走。

接口 `destination.insert(position,first,last)` 把左闭右开源区间 [first,last) 的元素，按原顺序插入到目标 position 之前。position 必须是目标数组的有效迭代器，可以为 end；first、last 则来自同一个源范围，且不能倒置。以下使用两个不同容器，避免把目标自身的失效迭代器当作插入来源：

```cpp
vector<int> source = {1, 2, 3, 4, 5};
vector<int> result = {9};
auto first_added = result.insert(result.end(), source.begin()+1, source.begin()+4);
// result 变成 9、2、3、4；source 仍是 1、2、3、4、5。
int first_value = *first_added;
vector<int> snapshot = result;
snapshot[0] = 0; // 副本有独立的元素，不会改变 result[0]。
result = source; // 赋值替换整个内容，不是在末尾追加。
```

返回值指向第一个插入元素；若源区间为空，则返回对应插入位置。上例 first_value 为二。在目标中间插入会把后面的元素向后搬，插入 k 项、后面原有 t 项时，成本为 O(k+t)；末尾插入仍需复制 k 项。若扩容，还要搬移旧存储的内容。

扩容会使目标全部旧迭代器、引用、指针失效；即使未扩容，插入位置及之后的旧迭代器也会失效。不要先保存目标 end，再多次插入时反复用它，应在每次调用时重新取得 end。源数组独立且没有修改时，源迭代器仍有效。

`vector<int> snapshot = result` 创建独立副本；`result = source` 将已有数组内容替换为源内容，复制成本与源长度成正比。改副本不会改原数组。若只保存引用，则引用仍指向原对象，语义不同。复制可用于搜索分支备份，是否合适要结合数组大小与分支数量判断。
