"""Reviewed four palindrome tasks within the requested difficulty range."""
from nowcoder_editorials import CONTENT, add, read
from nowcoder_palindrome_support import EXPLANATION, MANACHER


def run():
    existing = read(CONTENT / 'reviewed.json')

    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)

    put(236544, 2100, ['Manacher', '计数', '快速幂'], '所有奇数长度回文子串按长度降序，求前 K 个长度的乘积。',
        '用 Manacher 得到每个中心的最长奇回文长度。若某中心最长为 L，它就恰好给 L、L-2、……、1 各贡献一次。因此先按最长长度计数，再沿奇数长度从大到小累加后缀，得到每个长度的实际出现次数。每个长度取 min(剩余K,出现次数) 项，用快速幂把这一长度的重复乘法一次完成。全部用尽仍不足 K 则输出 -1。\n\n' + EXPLANATION,
        r'''int n; long long k; string s; cin >> n >> k >> s; PalindromeRadii radius(s); vector<long long> count(n + 3); for (int r : radius.odd) count[2 * r - 1]++;
        const long long mod = 19930726; auto power = [&](long long a, long long exponent) { long long result = 1; while (exponent) { if (exponent & 1) result = result * a % mod; a = a * a % mod; exponent >>= 1; } return result; };
        long long answer = 1; for (int length = n % 2 ? n : n - 1; length >= 1 && k > 0; length -= 2) { count[length] += count[length + 2]; long long take = min(k, count[length]); answer = answer * power(length, take) % mod; k -= take; } cout << (k ? -1 : answer);''',
        '位置不同的相同回文也分别计数。只考虑奇数长度，K 最大万亿，不能逐项枚举。模数不必为素数，普通快速幂仍可用。',
        declarations=MANACHER, complexity=r'预处理 $O(n)$，选取阶段 $O(n\log(K+1))$ 的上界，空间 $O(n)$。',
        cases=[{'input': '2 3\naa', 'output': '-1'}])
    put(236545, 2100, ['Manacher', '前后缀最值'], '求可拆成两个相邻非空回文的最长连续子串。',
        '预处理 end[i] 为恰在 i 结束的最长回文长度，start[i] 为恰在 i 开始的最长回文长度。先把每个中心的最大奇、偶回文记到它的左右端点。一个长度 L 的回文去掉两端后，得到向内缩一格、长度 L-2 的回文，所以 end 从右向左按 end[i+1]-2 传播，start 从左向右按 start[i-1]-2 传播，就补齐所有较短半径。最后枚举分割缝 i|i+1，最大化 end[i]+start[i+1]。两段正好相邻且都非空。\n\n' + EXPLANATION,
        r'''string s; cin >> s; int n = s.size(); PalindromeRadii radius(s); vector<int> ending(n), starting(n);
        for (int i = 0; i < n; i++) { int r = radius.odd[i], length = 2 * r - 1; ending[i + r - 1] = max(ending[i + r - 1], length); starting[i - r + 1] = max(starting[i - r + 1], length);
            r = radius.even[i]; if (r) { length = 2 * r; ending[i + r - 1] = max(ending[i + r - 1], length); starting[i - r] = max(starting[i - r], length); } }
        for (int i = n - 2; i >= 0; i--) ending[i] = max(ending[i], ending[i + 1] - 2); for (int i = 1; i < n; i++) starting[i] = max(starting[i], starting[i - 1] - 2);
        int answer = 0; for (int i = 0; i + 1 < n; i++) answer = max(answer, ending[i] + starting[i + 1]); cout << answer;''',
        '这是两个相邻回文，不能拿两个可能相交的全局最长回文直接相加。较短回文也可能参与最优答案，端点传播不能省略。',
        declarations=MANACHER, complexity=r'时间、空间均为 $O(n)$。',
        cases=[{'input': 'ab', 'output': '2'}, {'input': 'aaaaa', 'output': '5'}])
    put(236735, 2100, ['Manacher', '等价变换', '计数'], '统计反转并零一取反后保持不变的非空子串。',
        '反对称串不可能为奇数长度，因为中心字符无法与自身取反后相同。对所有位置 i，把原二进制字符异或 i 的奇偶性，得到 t[i]。偶长度子串中任意一对镜像下标奇偶性相反，所以原字符不同，当且仅当变换后的字符相同。因此原串的反对称子串，恰好对应变换串的偶长度回文。求 Manacher 的偶半径并求和即可，每个半径的一到其最大值各对应一个不同位置的子串。\n\n' + EXPLANATION,
        r'''int n; string s; cin >> n >> s; for (int i = 0; i < n; i++) s[i] = char('0' + ((s[i] - '0') ^ (i & 1))); PalindromeRadii radius(s); cout << accumulate(radius.even.begin(), radius.even.end(), 0LL);''',
        '只累计偶回文半径，不能加入奇回文。即使内容相同，只要起止位置不同也分别计数，答案需要 long long。',
        declarations=MANACHER, complexity=r'时间、空间均为 $O(n)$。')
    count_range = r'''long long countPalindromes(const string &s, int begin, int end, vector<int> &radius) {
        long long answer = 0; int left = begin, right = begin - 1;
        for (int i = begin; i < end; i++) { int k = i > right ? 1 : min(radius[left + right - i], right - i + 1);
            while (i - k >= begin && i + k < end && s[i - k] == s[i + k]) k++; radius[i] = k; answer += k; if (i + k - 1 > right) { left = i - k + 1; right = i + k - 1; } }
        left = begin; right = begin - 1;
        for (int i = begin; i < end; i++) { int k = i > right ? 0 : min(radius[left + right - i + 1], right - i + 1);
            while (i - k - 1 >= begin && i + k < end && s[i - k - 1] == s[i + k]) k++; radius[i] = k; answer += k; if (i + k - 1 > right) { left = i - k; right = i + k - 1; } }
        return answer;
    }'''
    put(236738, 2200, ['Manacher', '贡献法'], '每个回文子串的价值为不同字母数，累计所有回文出现的价值。',
        '按字母分别计贡献。对某字母 c，所有包含 c 的回文各贡献一；其数量等于全部回文数，减去不含 c 的回文数。把字符串按 c 的出现位置切成若干个不含 c 的连续段，不含 c 的回文必完整落在其中某一段，在各段独立用 Manacher 计数即可。于是答案是 26*全部回文数，再减去二十六次所有无 c 段中的回文数。固定字母只有二十六种，每轮段长之和不超过 n，所以总共线性乘一个常数。\n\n计数函数分别求奇、偶回文半径，将半径求和；数组可在各段间复用。',
        r'''string s; cin >> s; int n = s.size(); vector<int> radius(n); long long total = countPalindromes(s, 0, n, radius), answer = 26 * total;
        for (char c = 'a'; c <= 'z'; c++) { int begin = 0; for (int i = 0; i <= n; i++) if (i == n || s[i] == c) { answer -= countPalindromes(s, begin, i, radius); begin = i + 1; } } cout << answer;''',
        '同一个字母在回文里出现多次仍只贡献一。不能把“回文长度”当价值；空段没有回文。总贡献可超过 32 位。',
        declarations=count_range, complexity=r'时间 $O(26n)$，额外空间 $O(n)$。',
        cases=[{'input': 'aaaa', 'output': '10'}, {'input': 'abc', 'output': '3'}])


if __name__ == '__main__':
    run()
    print('Registered four reviewed palindrome articles.')
