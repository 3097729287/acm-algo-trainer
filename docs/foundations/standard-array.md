# array：长度在编译时固定的标准库数组

`array<T,N>`保存N个T类型元素，长度写在类型中，运行时不会伸长。它需要头文件`<array>`，支持下标访问、整体复制、范围for以及begin、end，因此长度已知的四科题数适合用array保存。[C++标准草案中的array定义](https://eel.is/c++draft/array.overview)规定它连续存放固定数量的元素。

下标从零开始，四个元素的下标为零到三，访问第四号下标已经越界。方括号访问不自动检查范围；at会检查，但不能因此忽略合法边界。

```cpp
array<int,4> counts{}; // 四个整数全部初始化为零
counts[0] = 2;
counts[1] = 3;
auto saved = counts; // 整体复制，后续各自修改
counts.fill(1);
int sum = 0;
for (int x : saved) sum += x;
cout << saved.size() << ' ' << sum << ' ' << counts[0] << '\n';
```

这段程序输出四、五、一，依次是固定长度、复制前数组的元素和，以及fill后当前数组的首项。空花括号使整数初始为零；如果只声明局部的array而不初始化，不能在赋值前读其中的整数。题解中的counts没有花括号，但它的每一项都先被输入写入，随后才会读取。

范围for中的`int x`是副本，改变x不会改变数组；需要逐项写入时使用`int &x`。例如输入循环中的引用让cin直接修改对应元素。长度由输入n决定时改用vector；不要把运行时变量n直接当作array类型参数。

一次下标访问为常数时间，复制或fill需要遍历N项。array本身不会像vector一样提供push_back来增加元素。
