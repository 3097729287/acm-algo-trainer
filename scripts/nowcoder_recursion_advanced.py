"""Explicit interfaces, bounded expression grammars and recursive state output."""
from nowcoder_editorials import add, CONTENT, read, register


def run():
    existing = read(CONTENT / 'reviewed.json')
    def put(n, *args, **kwargs):
        if 'nowcoder-global::' + str(n) not in existing:
            add(n, *args, **kwargs)

    put(16811, 1400, ['高精度', '模拟'], '在指定进制中不断把数与自身反转相加，求三十步以内首次出现回文数的步数。',
        '用低位在前的数位数组保存原数，不转换为机器整数。每轮先比较首尾判断回文；若不是，就把当前数位与反向数位逐位相加，按输入进制进位。每次相加最多增加一位，三十轮足以直接模拟。检查第零步到第三十步，第三十次相加后的结果也必须检查。',
        r'''int base; string s; cin >> base >> s; vector<int> a;
        for (int i = (int)s.size() - 1; i >= 0; i--) { char c = toupper(static_cast<unsigned char>(s[i])); a.push_back(c <= '9' ? c - '0' : c - 'A' + 10); }
        for (int step = 0; step <= 30; step++) {
            if (equal(a.begin(), a.end(), a.rbegin())) { cout << "STEP=" << step; return 0; }
            if (step == 30) break; vector<int> next; int carry = 0, n = a.size();
            for (int i = 0; i < n; i++) { int value = a[i] + a[n - 1 - i] + carry; next.push_back(value % base); carry = value / base; }
            if (carry) next.push_back(carry); a.swap(next);
        }
        cout << "Impossible!";''',
        '进位基数是输入的 N，不能始终按十进制处理。原题失败输出采用半角叹号的 Impossible!；回文初值需要零步。',
        complexity='若初始位数为 $L$，时间 $O(30(L+30))$，数位空间 $O(L+30)$。',
        cases=[{'input': '10\n56', 'output': 'STEP=1'}, {'input': '16\nAB', 'output': 'STEP=2'}, {'input': '10\n196', 'output': 'Impossible!'}, {'input': '2\n11', 'output': 'STEP=0'}])
    put(16680, 1800, ['枚举', '逻辑推理'], '恰有 N 人始终说谎，枚举谁有罪以及今天星期几，判断能否唯一确定罪犯。',
        '罪犯最多二十种，星期只有七种，可以全部枚举。固定这两项后，每句可识别证词的真假都确定了。同一个人的所有有效证词必须同真或同假，否则当前假设矛盾。设被确定说谎的人数为 liar，完全没有有效证词的人数为 unknown，只要 liar≤N≤liar+unknown，就能分配未知人的身份使假设成立。最后按罪犯身份去重：零人可能则 Impossible，一人则姓名，多人则 Cannot Determine。',
        r'''int m, n, p; cin >> m >> n >> p; vector<string> names(m); map<string,int> index;
        for (int i = 0; i < m; i++) { cin >> names[i]; index[names[i]] = i; }
        struct Statement { int speaker, kind, value; }; vector<Statement> statements;
        vector<string> days = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}; string line; getline(cin, line);
        for (int i = 0; i < p; i++) { getline(cin, line); auto colon = line.find(':'); int speaker = index[line.substr(0, colon)]; string message = line.substr(colon + 2);
            if (message == "I am guilty.") statements.push_back({speaker, 0, speaker});
            else if (message == "I am not guilty.") statements.push_back({speaker, 1, speaker});
            else { bool recognized = false;
                for (int d = 0; d < 7; d++) if (message == "Today is " + days[d] + ".") { statements.push_back({speaker, 2, d}); recognized = true; break; }
                if (recognized) continue;
                for (int who = 0; who < m; who++) {
                    if (message == names[who] + " is guilty.") { statements.push_back({speaker, 0, who}); break; }
                    if (message == names[who] + " is not guilty.") { statements.push_back({speaker, 1, who}); break; }
                }
            }
        }
        vector<int> possible;
        for (int guilty = 0; guilty < m; guilty++) { bool feasible = false;
            for (int day = 0; day < 7 && !feasible; day++) { vector<int> type(m, -1); bool valid = true;
                for (auto statement : statements) { bool truth = statement.kind == 2 ? day == statement.value : statement.kind == 0 ? guilty == statement.value : guilty != statement.value;
                    int who = statement.speaker; if (type[who] != -1 && type[who] != truth) { valid = false; break; } type[who] = truth; }
                int liar = count(type.begin(), type.end(), 0), unknown = count(type.begin(), type.end(), -1);
                if (valid && liar <= n && n <= liar + unknown) feasible = true;
            }
            if (feasible) possible.push_back(guilty);
        }
        if (possible.empty()) cout << "Impossible"; else if (possible.size() > 1) cout << "Cannot Determine"; else cout << names[possible[0]];''',
        '不符合五类格式的话完全忽略，不能当成假话。说谎者可以是罪犯也可以不是罪犯，没有额外约束。不同星期下同一罪犯只算一个候选。',
        complexity='枚举判断时间 $O(7M(P+M))$，识别证词预处理 $O(PM)$，空间 $O(P+M)$。',
        cases=[{'input': '2 1 2\nA\nB\nA: I am guilty.\nA: I am not guilty.', 'output': 'Impossible'},
               {'input': '2 1 1\nA\nB\nA: Hello!', 'output': 'Cannot Determine'}])
    put(201605, 1600, ['汉诺塔', '递归', '模拟'], '按盘数奇偶确定目标柱，逐帧输出普通汉诺塔从初态到终态的完整过程。',
        '用三个栈保存各柱盘子，从底到顶记录。递归搬 n 个盘：先搬上面 n-1 个到辅助柱，再搬最大盘到目标，最后把 n-1 个搬到目标。初始状态和每一次实际移动后各输出一幅图，得到 2^n 幅。绘图按固定柱中心对齐，直径为 2d+1 的星号段表示 d 号盘，所有盘均从底部堆起。',
        r'''int n; cin >> n; vector<vector<int>> pole(3); for (int d = n; d >= 1; d--) pole[0].push_back(d);
        int width = 3 * (2 * n + 1) + 4; bool first = true;
        auto draw = [&]() { if (!first) cout << string(width, '-') << '\n'; first = false;
            for (int row = 0; row < n + 2; row++) { string line(width, '.');
                if (row > 0) for (int p = 0; p < 3; p++) { int center = n + 1 + p * (2 * n + 2), index = n + 1 - row;
                    if (index < (int)pole[p].size()) { int disk = pole[p][index]; for (int x = center - disk; x <= center + disk; x++) line[x] = '*'; }
                    else line[center] = '|';
                }
                cout << line << '\n';
            }
        };
        function<void(int,int,int)> move = [&](int count, int from, int to) { if (count == 0) return; int auxiliary = 3 - from - to;
            move(count - 1, from, auxiliary); int disk = pole[from].back(); pole[from].pop_back(); pole[to].push_back(disk); draw(); move(count - 1, auxiliary, to); };
        draw(); move(n, 0, n % 2 == 0 ? 2 : 1);''',
        '这里允许左右柱直接搬盘，与只准相邻移动的题不同。分隔线只在两幅图之间，最后不再输出一条分隔线。空白必须是句点。',
        complexity='图幅数为 $2^n$，每幅输出 $O(n^2)$ 个字符，时间 $O(n^2 2^n)$，栈与递归空间 $O(n)$。')
    put(21181, 1800, ['表达式', '栈', '取模与同余'], '按指定优先级与同级从左到右规则，计算带阶乘和乘方的表达式，每一步采用 C++ 的模六万五千五百三十六余数。',
        '把后缀阶乘在读到数字时立刻计算，再用数值栈与运算符栈处理二元运算。读到新运算符时，先弹出所有优先级不低于它的旧运算符，保证乘方在本题也左结合。每次运算立即取模；除数为零则本组输出 ArithmeticException。阶乘的参数达到十八时，结果含至少十六个因子二，模 65536 为零，可直接返回零，避免重复阶乘产生长循环。',
        r'''const long long mod = 65536; int t; cin >> t;
        auto precedence = [](char op) { if (op == '+' || op == '-') return 1; if (op == '*' || op == '/') return 2; return 3; };
        auto power = [&](long long a, long long b) { long long result = 1; while (b > 0) { if (b & 1) result = result * a % mod; a = a * a % mod; b >>= 1; } return result; };
        auto factorial = [&](long long x) { if (x >= 18) return 0LL; long long result = 1; for (long long i = 2; i <= x; i++) result = result * i % mod; return result; };
        while (t--) { string s; cin >> s; vector<long long> values; vector<char> operators; bool bad = false;
            auto apply = [&]() { long long b = values.back(); values.pop_back(); long long a = values.back(); values.pop_back(); char op = operators.back(); operators.pop_back(); long long result = 0;
                if (!bad) { if (op == '+') result = a + b; else if (op == '-') result = a - b; else if (op == '*') result = a * b;
                    else if (op == '/') { if (b == 0) bad = true; else result = a / b; } else result = power(a, b); }
                values.push_back(result % mod);
            };
            for (size_t i = 0; i < s.size();) { if (isdigit(static_cast<unsigned char>(s[i]))) { long long value = s[i++] - '0';
                    while (i < s.size() && s[i] == '!') { value = factorial(value); i++; } values.push_back(value);
                } else { char op = s[i++]; while (!operators.empty() && precedence(operators.back()) >= precedence(op)) apply(); operators.push_back(op); } }
            while (!operators.empty()) apply(); if (bad) cout << "ArithmeticException\n"; else cout << values.back() << '\n';
        }''', '本题明确规定乘方同级从左往右，与某些语言的幂运算规则不同。负余数保留 C++ 语义，不要擅自加模数转正；零的零次方为一。',
        complexity='表达式长为 $L$，栈操作总量 $O(L)$；每次乘方最多十六次位循环，故固定模数下总时间 $O(L)$，空间 $O(L)$。',
        cases=[{'input': '4\n2^3^2\n0^0\n0-9!\n3/0', 'output': '64\n1\n-35200\nArithmeticException'}])

    if 'nowcoder-global::204382' not in existing:
        code = r'''#include <bits/stdc++.h>
        using namespace std;
        class Solution {
        public:
            vector<int> solve(int n, vector<int>& pre, vector<int>& suf) {
                if (n == 0) return {};
                vector<int> left(n, -1), right(n, -1), path; int finished = 0;
                for (int i = 0; i < n; i++) {
                    while (!path.empty() && finished < n && pre[path.back()] == suf[finished]) { path.pop_back(); finished++; }
                    if (!path.empty()) { int parent = path.back(); if (left[parent] == -1) left[parent] = i; else right[parent] = i; }
                    path.push_back(i);
                }
                vector<int> result, stack; int current = 0;
                while (current != -1 || !stack.empty()) {
                    while (current != -1) { stack.push_back(current); current = left[current]; }
                    current = stack.back(); stack.pop_back(); result.push_back(pre[current]); current = right[current];
                }
                return result;
            }
        };'''
        markdown = ('## 中序序列\n\n### 题意\n\n由互异结点的先序与后序恢复中序，单个孩子固定视为左孩子。原站使用 `Solution::solve` 函数接口，返回数组，无需自行读取输入或输出。\n\n'
                    '### 思路\n\n先序顺序决定新结点的出现顺序，后序顺序决定哪些子树已经结束。用栈保存尚未完成的祖先路径；准备放入下一个先序结点前，只要栈顶已等于后序中下一个待结束的结点，就将它弹出。剩余栈顶就是新结点父亲：还没有左孩子就挂左边，否则挂右边。这样唯一的一个孩子自然成为左孩子。建完树后，用显式栈完成中序遍历，避免十万层链上的递归栈溢出。\n\n'
                    '### 参考代码\n\n```cpp\n' + code + '\n```\n\n### 复杂度\n\n每个结点进出两次栈各一次，时间与数组空间均为 $O(n)$。\n\n'
                    '### 易错点\n\n先序与后序本来不能唯一确定只有一个孩子时的左右关系，本题额外规定单孩子为左。原站给出的是参数与返回值样例，提交时保留指定类名、方法名和引用参数。\n')
        driver = r'''int main() {
            string raw((istreambuf_iterator<char>(cin)), istreambuf_iterator<char>()); vector<int> numbers;
            for (size_t i = 0; i < raw.size();) { if (raw[i] == '-' || isdigit(static_cast<unsigned char>(raw[i]))) { int sign = 1; if (raw[i] == '-') { sign = -1; i++; } int value = 0;
                    while (i < raw.size() && isdigit(static_cast<unsigned char>(raw[i]))) { value = value * 10 + raw[i] - '0'; i++; } numbers.push_back(sign * value);
                } else i++; }
            int n = numbers[0]; vector<int> pre(numbers.begin() + 1, numbers.begin() + 1 + n), suf(numbers.begin() + 1 + n, numbers.end());
            auto result = Solution().solve(n, pre, suf); cout << '['; for (int i = 0; i < n; i++) { if (i) cout << ','; cout << result[i]; } cout << ']';
        }'''
        register(204382, 1700, ['二叉树', '栈'], '完整原题核验为函数式接口。先序加入路径栈、后序闭合子树、迭代中序，时间 O(n)，处理十万结点。',
                 {'default': markdown}, driver=driver, cases=[{'input': '3,[1,2,3],[3,2,1]', 'output': '[3,2,1]'}, {'input': '1,[7],[7]', 'output': '[7]'}])


if __name__ == '__main__':
    run()
    print('Registered advanced recursion and native-function editorials.')
