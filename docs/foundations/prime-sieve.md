# 埃氏筛：一次求出整个上界内的所有素数

若只判断一个小整数是否为素数，可以试除到平方根；若需要上界 n 内的完整素数表，对每个数重复试除会做很多重复工作。埃氏筛反过来，从一个素数出发排除它的倍数。

先把二到 n 都当作候选，零和一明确排除。从二开始扫描，尚未被排除的 p 就是素数；把 p²、p²+p、p²+2p……标成合数。小于 p² 的 p 的倍数已经含有小于 p 的因子，早先被处理，不必再从二倍 p 开始。

例如上界三十：二排除 4、6、8……；三从九开始排除 9、12、15……；四已被排除，跳过；五从二十五开始排除。最终留下 2、3、5、7、11、13、17、19、23、29。

```cpp
int limit = 30;
vector<bool> is_prime(limit+1, true);
is_prime[0] = false;
if (limit >= 1) is_prime[1] = false;
for (int p = 2; p <= limit/p; ++p) {
    if (!is_prime[p]) continue;
    for (long long multiple = 1LL*p*p; multiple <= limit; multiple += p)
        is_prime[multiple] = false;
}
vector<int> primes;
for (int x = 2; x <= limit; ++x)
    if (is_prime[x]) primes.push_back(x);
```

输入约定上界为非负整数，输出是布尔判定表与有序素数数组。外层只需到平方根，因为每个合数都有不超过平方根的素因子；最后收集仍须扫到 n，不能漏掉大于平方根的素数。

`p<=limit/p` 避免外层平方判定溢出，倍数循环用 long long 使乘法和步长也有足够范围。`vector<bool>` 是按位存储的标准库特化，适合这里的下标读写；不要假设其元素是普通 bool 引用，也不需要用引用遍历修改它。

标记次数约为 n 乘各素数倒数之和，埃氏筛时间 O(n log log n)，保存标记与结果空间 O(n)。它适合按数值上界开表的场景；上界太大时，不应仅因输入项很少就开同样大的数组。这里不是线性筛，同一个合数可以被多个素数标记。
