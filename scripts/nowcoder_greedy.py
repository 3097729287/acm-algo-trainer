"""Reviewed greedy proofs; misleading titles do not determine algorithms."""
from nowcoder_editorials import CONTENT, add, read


def run():
    existing = read(CONTENT / 'reviewed.json')

    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)

    put(14670, 1200, ['贪心', '排序'], '每 k 块木板组成一个桶，容量是最短板乘底面积，最大化总容量。',
        '把木板从高到低排序，每连续 k 块组成一个桶；不足 k 块的最矮木板不用。第 j 个桶的最短板取排序后的第 jk 块。证明可把任意方案的桶按最短板从高到低编号：前 j 桶共有 jk 块板都不短于第 j 桶的最短板，所以该最短板不能超过全体第 jk 高的板。连续分组恰好逐项达到这个上界。',
        r'''int t; cin >> t; while (t--) { int n, k, s; cin >> n >> k >> s; vector<int> h(n); for (int &x : h) cin >> x;
            sort(h.begin(), h.end(), greater<int>()); long long answer = 0; for (int i = k - 1; i < n; i += k) answer += 1LL * h[i] * s; cout << answer << '\n'; }''',
        '最矮的余数块应丢弃，不能先按升序从第一块开始组。k 大于 n 时造不出桶，答案为零。',
        complexity=r'每组时间 $O(n\log n)$，空间 $O(n)$。')
    put(13228, 1900, ['数学', '贪心'], '把水缸中的部分水加入各杯，使各杯最终温度相同，求能达到的最高温度。',
        '记各杯总水量为 V、总的温度乘体积为 H，初始最低和最高温度为 low、high。混水只能让每杯温度向水缸温度 T 靠近，不能有限次越过或恰好到达 T（除非原来就是 T）。若 T>high，最高共同温度是用完 C 升后的 (H+TC)/(V+C)，且它必须至少为 high；这也充分，因为每杯所需加入量 c[i](X-t[i])/(T-X) 都非负，合计恰为 C。若 T<low，共同温度不能高于 low；取 X=low 最省冷水，所需总量为 (H-low V)/(low-T)，不超过 C 就可行。若 T 夹在温度范围内，只有所有杯原来都等于 T 才可行。用整数交叉相乘判断可行性，最后才做除法输出。',
        r'''int n; long long t, capacity; cin >> n >> t >> capacity; long long volume = 0, heat = 0, low = 10001, high = 0;
        for (int i = 0; i < n; i++) { long long temperature, c; cin >> temperature >> c; volume += c; heat += temperature * c; low = min(low, temperature); high = max(high, temperature); }
        bool possible = false; long double answer = 0;
        if (t > high) { possible = heat + t * capacity >= high * (volume + capacity); answer = (heat + (long double)t * capacity) / (volume + capacity); }
        else if (t < low) { possible = heat - low * volume <= capacity * (low - t); answer = low; }
        else if (low == high) { possible = true; answer = low; }
        if (!possible) cout << "Impossible\n"; else cout << "Possible\n" << fixed << setprecision(4) << answer << '\n';''',
        '不要求倒光水缸。降温时多倒水反而降低共同温度，样例也只用了 1.5 升而非全部两升。杯间不能互相倒水。',
        complexity=r'时间 $O(n)$，只保存汇总量，额外空间 $O(1)$。',
        cases=[{'input': '2\n100 2\n10 1\n20 1', 'output': 'Possible\n57.5000'}, {'input': '2\n20 100\n10 1\n20 1', 'output': 'Impossible'}, {'input': '1\n10 0\n20 1', 'output': 'Possible\n20.0000'}])
    put(14291, 1600, ['贪心', '排序'], '允许先重排序列，随后逐次切开，最大化每次被切序列的总和之和。',
        '逆向看，切分就是把所有单元素合并，每次代价为新合并的总和，目标是最大化总代价。最优合并树中，越大的数应放在越深的位置，因为它参与的合并次数更多；最深处必有一对兄弟叶子，可以把最大的两个数交换到这里而不减答案。合并这两个最大数后，问题缩小。各数非负，合并结果仍最大，所以后续总是把当前大块与下一个较大数合并。正向就是升序排列，每次单独切掉最左的最小数。累加长度 n、n-1、……、2 的后缀和。',
        r'''int n; cin >> n; vector<long long> a(n); long long sum = 0, answer = 0; for (auto &x : a) { cin >> x; sum += x; } sort(a.begin(), a.end());
        for (int i = 0; i + 1 < n; i++) { answer += sum; sum -= a[i]; } cout << answer;''',
        '求最大代价，应让大数被反复计入。长度一不再切分，不能再加最后一个数。总和与答案都用 long long。',
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。',
        cases=[{'input': '2\n0 10000', 'output': '10000'}])
    put(15322, 1300, ['数学', '贪心'], '每步给恰好 n-1 个元素加一，用最少步数使所有值相等，并求最终值。',
        '每步相当于所有元素一起加一，再把未选中的那一个减一。忽略公共平移，就成了每步把一个元素减一，至少需要 sum(a[i]-minimum) 步才能都降到原最小值。依次降低各元素可实现此下界。还原公共平移后，最终值为 minimum+steps。',
        r'''int t; cin >> t; while (t--) { int n; cin >> n; long long sum = 0, minimum = LLONG_MAX; for (int i = 0; i < n; i++) { long long x; cin >> x; sum += x; minimum = min(minimum, x); }
            long long steps = sum - minimum * n; cout << steps << ' ' << minimum + steps << '\n'; }''',
        '求操作次数时基准是原数组最小值。n=1 时每步改变零个元素，本来已相等，答案零步。',
        complexity=r'每组时间 $O(n)$，额外空间 $O(1)$。')
    put(15805, 1300, ['贪心', '字符串'], '从字符串中选出字典序最大的子序列。',
        '从右向左维护已见最大字符。当前字符若不小于右侧所有字符，就选它；若更小，就应舍弃，因为右侧更大的字符能使答案在这一位更大。相等时也保留：先选当前这一个，后面的同字符仍可继续选，公共前缀后的较长串字典序更大。最后反转答案，恢复原下标顺序。',
        r'''string s, answer; cin >> s; char maximum = 0; for (int i = (int)s.size() - 1; i >= 0; i--) if (s[i] >= maximum) { maximum = s[i]; answer += s[i]; }
        reverse(answer.begin(), answer.end()); cout << answer;''',
        '相等必须保留，不能写成严格大于。子序列只可删除字符，不能把所有字符直接降序排序。',
        complexity=r'时间 $O(|s|)$，结果空间 $O(|s|)$。',
        cases=[{'input': 'aaaa', 'output': 'aaaa'}, {'input': 'azb', 'output': 'zb'}])
    put(16301, 1600, ['贪心', '构造', '集合'], '每步用两数之和替换其中一个，使 n 个正整数最终互不相同。',
        '若原来有 D 个不同值，一步至多让不同值数量增加一，故至少 n-D 步。这个下界可达到：每次挑一个重复值 x，把它与当前最大值 M 相加，替换这个重复项。x>0，所以新数 M+x 比所有旧数大；原值 x 还有另一份，不会失去旧的不同值，恰好增加一种。重复做 n-D 次即可，因此只需数不同值。',
        r'''int n; cin >> n; set<long long> values; for (int i = 0; i < n; i++) { long long x; cin >> x; values.insert(x); } cout << n - values.size();''',
        '构造仅用于证明，不需要真的累加这些可能越来越大的数。所有输入为正数是新值严格大于当前最大值的关键。',
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(16640, 1200, ['贪心', '排序', '双指针'], '每组最多两件且总价格不超过 w，最小化组数。',
        '排序后维护最便宜和最贵的剩余物品。最贵的总要放入一组：若它与最便宜的都放不下，就只能单独一组；否则把这两件配在一起。证明后一选择安全：若某最优方案把最贵的配给另一件，交换成最便宜的仍可行，被替换的那件放到最便宜原来的位置，也不会更贵于该位置原本搭配最贵物品时的上界；若其中一件原来单独成组，同样不会增加组数。每次确定一组，直到取完。',
        r'''int w, n; cin >> w >> n; vector<int> a(n); for (int &x : a) cin >> x; sort(a.begin(), a.end());
        int left = 0, right = n - 1, answer = 0; while (left <= right) { if (left < right && a[left] + a[right] <= w) left++; right--; answer++; } cout << answer;''',
        '只剩一件时直接成组，不能用同一个物品与自身配对。题目保证每件单独都能放下。',
        complexity=r'时间 $O(n\log n)$，排序之外额外空间 $O(1)$。')
    put(19487, 1400, ['贪心', '排序', '连通性'], '领导人属性差不超过 m 的两势力可合并，并保留两位领导人之一。',
        '把属性升序排序。相邻差不超过 m 的一段可全部合并：从左到右合并，每次保留右侧较大的领导人，它就能继续与下一个相邻领导人连接。相邻差大于 m 的地方两边任何属性差都大于 m，领导人又始终来自原集合，因此永远无法跨过。答案就是这些段的数量。',
        r'''int n; long long m; cin >> n >> m; vector<long long> a(n); for (auto &x : a) cin >> x; sort(a.begin(), a.end()); int answer = 1;
        for (int i = 1; i < n; i++) if (a[i] - a[i - 1] > m) answer++; cout << answer;''',
        '合并后可以主动保留新的领导人，所以一段的最大值减最小值可以远大于 m。不能直接按整段极差分组。',
        complexity=r'时间 $O(n\log n)$，保存输入的空间 $O(n)$。')
    put(19784, 1600, ['贪心', '排序'], '最多 m 辆购物车，每辆含凳子的车可将最贵的一件商品半价。',
        '设凳子有 s 件，最多可得到 k=min(m,s) 次折扣。任意方案省下的钱不超过全体最贵 k 件价格之和的一半。这个上界可达：给这 k 件商品各放一辆车，若某件本身是凳子就已有资格，否则从剩余凳子中给它配一件。因为总凳子数至少 k，必能配齐；剩余商品都不比这 k 件贵，放进其中任一车不会降低折扣。没有凳子时原价购买。',
        r'''int t; cin >> t; while (t--) { int n, m, stools = 0; cin >> n >> m; vector<long long> prices(n); long long total = 0;
            for (auto &price : prices) { int isStool; cin >> price >> isStool; total += price; stools += isStool; }
            sort(prices.begin(), prices.end(), greater<long long>()); long long twice = 2 * total; for (int i = 0; i < min(m, stools); i++) twice -= prices[i];
            cout << twice / 2 << (twice % 2 ? ".5\n" : ".0\n"); }''',
        '凳子本身也可成为半价商品。用金额的两倍做整数运算，避免浮点格式误差；购物车不要求全都使用。',
        complexity=r'每组时间 $O(n\log n)$，空间 $O(n)$。',
        cases=[{'input': '1\n3 2\n9 0\n2 0\n3 0', 'output': '14.0'}])
    put(19812, 1500, ['贪心', '数学'], '借助等高滑索穿过一列山，最小化海拔累计上升与下降量。',
        '设最高山高 H。必然至少到达 H：不能在低于 H 的高度直接越过这座更高的山。起终点都为零，因此累计变化至少 2H。上界也可实现：向最高山前进时，每次从当前山顶滑到右边第一座不低于它的山，途中山都不高于滑索，符合条件；这样海拔只升不降。越过最高山后，按反方向同样构造单调下降路线。故答案恰为 2H。',
        r'''int n, highest = 0; cin >> n; for (int i = 0; i < n; i++) { int x; cin >> x; highest = max(highest, x); } cout << highest * 2;''',
        '幅度在这里按题目所求的累计海拔变化理解，单座高 H 的山需要上升 H 再下降 H。无需真的计算滑索端点。',
        complexity=r'时间 $O(n)$，额外空间 $O(1)$。')
    put(19838, 1700, ['贪心', '数学'], '删除当前位置 i 的元素付出 a[i]i，后面的下标减一，求总费用最小值。',
        '原来第 i 个元素删除时的位置一定在一到 i 之间。正数的最小贡献不小于 a[i]，负数的最小贡献不小于 i*a[i]。这组逐项下界能同时实现：先从右往左删所有负数，它们前面的原元素全都还在，下标正好是原 i；再从左往右删非负数，每次下标都是一。因此把负数乘原下标、非负数原值直接求和即可。',
        r'''int n; cin >> n; long long answer = 0; for (long long i = 1; i <= n; i++) { long long x; cin >> x; answer += x < 0 ? x * i : x; } cout << answer;''',
        '负数希望在更大的下标删除，不能把所有元素都从左到右删。标题中列出的数据结构并非解题所需。',
        complexity=r'时间 $O(n)$，额外空间 $O(1)$。',
        cases=[{'input': '4\n5 -2 3 -4', 'output': '-12'}, {'input': '3\n-1 -1 -1', 'output': '-6'}])
    put(201628, 1600, ['贪心', '排序'], '对方出牌顺序已知，可重排自己的牌，使所有 max(自己的牌-对方的牌,0) 之和最大。',
        '把对方牌升序排，自己的牌降序排，逐项累加正差。可从获胜的 k 轮看出上界：总分至多为自己的最大 k 张之和，减对方最小 k 张之和。这两个序列一降一升，逐项差单调不增，取所有正差正好最大化该上界；把其余牌任意配给剩下的轮次即可达到。只求分数，原出牌顺序可以通过重新安排自己的牌还原，不影响最优值。',
        r'''int n; cin >> n; vector<long long> a(n), b(n); for (auto &x : a) cin >> x; for (auto &x : b) cin >> x;
        sort(a.begin(), a.end()); sort(b.begin(), b.end(), greater<long long>()); __int128 answer = 0;
        for (int i = 0; i < n; i++) if (b[i] > a[i]) answer += b[i] - a[i];
        if (!answer) cout << 0; else { string s; while (answer) { s += char('0' + answer % 10); answer /= 10; } reverse(s.begin(), s.end()); cout << s; }''',
        '单张牌可达 10^18，总分可能超过 64 位；用 __int128 累加并按十进制输出。目标不是获胜轮数。',
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。',
        cases=[{'input': '2\n1 100\n2 101', 'output': '100'}, {'input': '10\n1 1 1 1 1 1 1 1 1 1\n1000000000000000000 1000000000000000000 1000000000000000000 1000000000000000000 1000000000000000000 1000000000000000000 1000000000000000000 1000000000000000000 1000000000000000000 1000000000000000000', 'output': '9999999999999999990'}])
    put(204859, 1300, ['排序', '双指针', '滑动窗口'], '选尽量多的人，使任意两人的能力差不超过 k。',
        '排序后，一个团队合法等价于最大值减最小值不超过 k。若选了两个端点，中间的人也可全部加入而不破坏条件，所以只需找最长合法连续段。枚举右端点，不断右移左端点直到极差不超过 k，再更新长度；左端点只会向右移动。',
        r'''int t; cin >> t; while (t--) { int n; long long k; cin >> n >> k; vector<long long> a(n); for (auto &x : a) cin >> x; sort(a.begin(), a.end());
            int left = 0, answer = 0; for (int right = 0; right < n; right++) { while (a[right] - a[left] > k) left++; answer = max(answer, right - left + 1); } cout << answer << '\n'; }''',
        '限制是任意两人，不能仅检查排序后相邻两人的差；链式相近不保证首尾相近。',
        complexity=r'排序 $O(n\log n)$，双指针 $O(n)$，空间 $O(n)$。')
    put(21841, 1300, ['数学', '前缀和'], '任意合并两个图形 x、y，得到 x+y 并获分 xy，求最大总分。',
        '一个图形合并后大小是其包含的原始大小之和，合并两组时 xy 正好等于两组之间所有原始元素乘积的和。每对原始元素只在它们第一次进入同组时计分一次，因此无论合并顺序如何，总分始终是所有 i<j 的 a[i]a[j] 之和。读入 x 时，令它与前面所有元素的和 prefix 相乘加入答案，再把 x 加入 prefix。',
        r'''int n; cin >> n; long long prefix = 0, answer = 0; for (int i = 0; i < n; i++) { long long x; cin >> x; answer += prefix * x; prefix += x; } cout << answer;''',
        '不需要枚举合并顺序，也不需要优先队列。最后的总大小不是总分，需累加每对元素的乘积。',
        complexity=r'时间 $O(n)$，额外空间 $O(1)$。')


if __name__ == '__main__':
    run()
    print('Registered fourteen individually proved greedy solutions.')
