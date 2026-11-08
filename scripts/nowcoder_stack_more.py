"""Remaining elementary stack/ordered set/queue applications."""
from nowcoder_editorials import add, CONTENT, read, register


def run():
    existing = read(CONTENT / 'reviewed.json')
    def put(n, *args, **kwargs):
        if 'nowcoder-global::' + str(n) not in existing:
            add(n, *args, **kwargs)

    put(13822, 1400, ['队列', '惰性删除'], '已知每人进出队时刻且从队首出队，统计从未插队的人。',
        '按进队次序给每人一个递增编号。某人出队时，若还有比他更早进队的人尚未出队，他必然曾插到别人前面；反之他没有越过仍在队里的早到者，就是正常排队。维护最早尚未离开的编号 front，出队时标记删除，再让 front 跳过所有已离开的编号。每个编号只被跳过一次。',
        r'''int t; cin >> t; while (t--) { int n; cin >> n; unordered_map<string,int> id; vector<bool> removed(n + 2); int total = 0, front = 1, answer = 0;
            for (int i = 0; i < n; i++) { string op, name; cin >> op >> name;
                if (op == "in") id[name] = ++total; else { int current = id[name]; if (current == front) answer++; removed[current] = true;
                    while (front <= total && removed[front]) front++; } }
            cout << answer << '\n';
        }''', '新入队者不一定站在队尾，不能把实际队伍简单当普通 FIFO 队列重放；这里保存的是到达顺序，并用实际出队信息惰性删除。',
        complexity='哈希查名期望 $O(n)$，编号扫描总计 $O(n)$，空间 $O(n)$。')
    put(14615, 1400, ['筛法', '枚举', '去重'], '统计不超过 n 的数中，有多少个可以表示为素数平方、素数立方与素数四次方之和。',
        '先筛出不超过 √n 的素数，并分别保存不超过 n 的平方、立方、四次方列表。枚举三个列表的组合，和不超过 n 就给对应数打标记；首次标记时增加答案，避免多种表示重复计数。列表递增，部分和已超界就可以结束该层枚举。',
        r'''int n; cin >> n; int limit = sqrt(n); vector<bool> prime(limit + 1, true); if (limit >= 0) prime[0] = false; if (limit >= 1) prime[1] = false;
        for (int p = 2; p <= limit / p; p++) if (prime[p]) for (int x = p * p; x <= limit; x += p) prime[x] = false;
        vector<long long> square, cube, fourth;
        for (long long p = 2; p <= limit; p++) if (prime[p]) { if (p * p <= n) square.push_back(p * p); if (p * p * p <= n) cube.push_back(p * p * p); if (p * p * p * p <= n) fourth.push_back(p * p * p * p); }
        vector<bool> seen(n + 1); int answer = 0;
        for (long long a : fourth) for (long long b : cube) { if (a + b > n) break; for (long long c : square) { long long sum = a + b + c; if (sum > n) break; if (!seen[sum]) { seen[sum] = true; answer++; } } }
        cout << answer;''', '同一个和可能来自不同素数组合，必须按数值去重。使用 vector<bool> 的位存储，不分配五千万个普通整数。',
        complexity=r'筛法 $O(\sqrt n\log\log n)$；枚举最多 $O(\pi(n^{1/4})\pi(n^{1/3})\pi(\sqrt n))$ 次。标记空间 $O(n)$ 位。', cases=[{'input': '27', 'output': '0'}])
    put(17508, 1500, ['有序集合', '区间查询'], '维护指纹集合：与已有值差不超过 k 时忽略新增，区间删除，区间存在性查询。',
        '用 set 按数值存储指纹。任一操作只关心 [x-k,x+k]：lower_bound(x-k) 找到可能的第一个元素，若它不大于右端点就说明存在匹配。添加时按此条件决定是否插入；删除时从这个迭代器开始逐个删除直到越过右端点。每个被删除元素都源自此前一次成功插入，所有删除的总量不超过操作数。',
        r'''int m, k; cin >> m >> k; set<int> values;
        for (int i = 0; i < m; i++) { string op; int x; cin >> op >> x; cin.ignore(numeric_limits<streamsize>::max(), '\n');
            auto it = values.lower_bound(x - k); bool exists = it != values.end() && *it <= x + k;
            if (op == "add") { if (!exists) values.insert(x); }
            else if (op == "query") cout << (exists ? "Yes" : "No") << '\n';
            else { while (it != values.end() && *it <= x + k) it = values.erase(it); }
        }''', '删除会移除区间里全部指纹，不要求集合里恰好存在 x。样例行末有解释性注释，读取指令和值后忽略该行余下内容。',
        complexity=r'总时间 $O(m\log m)$，集合空间 $O(m)$。删除的元素总数受成功添加次数限制。')
    put(210768, 900, ['集合', '去重'], '忽略重复叫号，求第一次叫到 younik 时她是第几位不同的人。',
        '逐个名字插入集合，集合大小就是到目前为止叫过的不同人数。首次遇到 younik 时记录当时大小，后面的名字不再影响她的序号。',
        r'''int n; cin >> n; set<string> people; int answer = 0; for (int i = 0; i < n; i++) { string name; cin >> name; people.insert(name); if (name == "younik" && answer == 0) answer = people.size(); } cout << answer;''',
        '重复名字不能重复增加人数，题目求的不是输入行号。', complexity=r'时间 $O(n\log n)$，名字长度视为输入成本，存储空间 $O(n)$。')
    put(216012, 1600, ['排序', '区间', '贪心'], '选择任意实数中心，最大化严格比所有蓝石更近的红石数量。',
        '能得分的红石必须处于同一段相邻蓝石之间，或最左、最右的外侧区间。因为距中心小于最近蓝石距离的所有位置构成一个不含蓝石的开区间，不可能跨过蓝石。反过来，有限蓝石间隙的中点能让间隙内全部红石得分；外侧间隙也可把中心移得足够远以覆盖所有红石。因此排序后统计每个蓝石间隙内红石的数量，取最大值，坐标等于蓝石的红石永不得分。',
        r'''int t; cin >> t; while (t--) { int n, m; cin >> n >> m; vector<int> red(n), blue(m); for (int &x : red) cin >> x; for (int &x : blue) cin >> x;
            sort(red.begin(), red.end()); sort(blue.begin(), blue.end()); vector<int> count(m + 1); int p = 0, answer = 0;
            for (int x : red) { while (p < m && blue[p] < x) p++; if (p < m && blue[p] == x) continue; answer = max(answer, ++count[p]); }
            if (answer == 0) cout << "Impossible\n"; else cout << answer << '\n';
        }''', '输出最大得分而不是中心坐标。多个蓝石同坐标不改变间隙，红蓝同坐标时严格不等式永远失败。',
        complexity=r'每组时间 $O(n\log n+m\log m)$，数组空间 $O(n+m)$。')

    if 'nowcoder-global::212914' not in existing:
        code = r'''#include <bits/stdc++.h>
        using namespace std;
        class Solution {
        public:
            long long legalExp(string str) {
                vector<long long> values;
                for (size_t i = 0; i < str.size();) {
                    if (isdigit(static_cast<unsigned char>(str[i]))) {
                        long long value = 0;
                        while (i < str.size() && isdigit(static_cast<unsigned char>(str[i]))) { value = value * 10 + str[i] - '0'; i++; }
                        values.push_back(value); i++;
                    } else {
                        char op = str[i++]; long long b = values.back(); values.pop_back(); long long a = values.back(); values.pop_back();
                        values.push_back(op == '+' ? a + b : op == '-' ? a - b : a * b);
                    }
                }
                return values.back();
            }
        };'''
        markdown = ('## 牛牛与后缀表达式\n\n### 题意\n\n计算由数字、结束符 # 及加减乘构成的合法后缀表达式。原站要求实现 `Solution::legalExp(string str)` 并返回 long long。\n\n'
                    '### 思路\n\n从左到右扫描，数字持续读到 # 为止，把完整数值压栈。遇到运算符，就依次弹出右操作数 b、左操作数 a，计算 a op b 后重新压栈。每个栈元素始终代表一个已经算好的完整子表达式；合法后缀串结束后，栈内只剩整个表达式的值。\n\n'
                    '### 参考代码\n\n```cpp\n' + code + '\n```\n\n### 复杂度\n\n每个字符与栈元素均只处理常数次，时间与栈空间上界均为 $O(|str|)$。\n\n'
                    '### 易错点\n\n先弹出的是右操作数，减法必须写 a-b。参数可能有多位，不能把每个数字字符都单独压栈。样例外层引号表示字符串参数，不属于传入函数的内容。所有数值使用 long long，原题保证中间结果绝对值不超过十的十八次方。\n')
        register(212914, 1300, ['栈', '表达式'], '完整原题核验为 legalExp(string) 函数式接口。按后缀式维护数值栈，O(|str|)，正确区分多位参数与减法左右操作数。',
                 {'default': markdown}, driver=r'''int main() { string s; cin >> s; if (s.size() >= 2 && s.front() == '"' && s.back() == '"') s = s.substr(1, s.size() - 2); cout << Solution().legalExp(s); }''',
                 cases=[{'input': '"1#5#-"', 'output': '-4'}, {'input': '"1000000000#1000000000#*"', 'output': '1000000000000000000'}])


if __name__ == '__main__':
    run()
    print('Registered ordered-set and remaining stack applications.')
