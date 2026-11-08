"""Deterministic suffix-array solutions for the two eligible LCS problems."""
from nowcoder_editorials import CONTENT, add, read
from nowcoder_suffix_support import EXPLANATION, SUFFIX_ARRAY


def run():
    existing = read(CONTENT / 'reviewed.json')
    if 'nowcoder-global::237306' not in existing:
        add(237306, 2200, ['后缀数组', '最长公共子串'], '求两个长度各不超过五十万的小写字符串的最长公共子串长度。',
            '将两个串中间放一个未出现在字母表中的分隔符，拼成一个整数序列。建立后缀数组与相邻 LCP，扫描来源不同的相邻后缀，取其 LCP 最大值。若某个公共子串长度为 L，那么所有以它开头的后缀在后缀数组中连续，里面同时有两个源串的后缀，必存在一对来源不同的相邻后缀，LCP 至少为 L；所以只看相邻项已足够。分隔符后缀不参与答案。\n\n' + EXPLANATION,
            r'''string s, t; cin >> s >> t; vector<int> data; data.reserve(s.size() + t.size() + 1); for (char c : s) data.push_back(c - 'a' + 2); int separator = data.size(); data.push_back(1); for (char c : t) data.push_back(c - 'a' + 2);
            SuffixArray index(data); auto owner = [&](int p) { return p < separator ? 0 : p == separator ? -1 : 1; }; int answer = 0;
            for (int i = 1; i < (int)index.sa.size(); i++) { int a = owner(index.sa[i - 1]), b = owner(index.sa[i]); if (a >= 0 && b >= 0 && a != b) answer = max(answer, index.height[i]); } cout << answer;''',
            '求的是连续子串，不是最长公共子序列。分隔符必须不同于所有字符，防止公共前缀跨越两个源串。',
            declarations=SUFFIX_ARRAY, complexity=r'总长 $N=|s|+|t|+1$，时间 $O(N\log N)$，空间 $O(N)$。',
            cases=[{'input': 'aaaa\naa', 'output': '2'}, {'input': 'abc\nxyz', 'output': '0'}])
    if 'nowcoder-global::237667' not in existing:
        add(237667, 2300, ['后缀数组', '滑动窗口', '单调队列'], '求同时是所有给定字符串子串的最长字符串长度。',
            '给每个源串分配不同的分隔符，将它们拼接后建立后缀数组与相邻 LCP。每个后缀标记其起点所属源串，分隔符位置记为无来源。在后缀数组上滑动窗口，维护每种来源出现次数；窗口包含全部源串时，这些后缀的公共前缀长度是 height[left+1..right] 的最小值，用递增单调队列求它。记录答案后移出左端继续缩短，直到缺少一种来源。\n\n正确性来自字典序的连续性：任何公共子串都对应一整段以它为前缀的后缀，其中包含所有来源；反过来，某窗口里全部后缀的公共前缀也出现在所有来源中。对固定右端，缩短窗口不会降低 LCP 最小值，因此把可行窗口逐一缩短不会漏掉最优值。\n\n' + EXPLANATION,
            r'''int sources; cin >> sources; vector<int> data, owner; data.reserve(1100000); owner.reserve(1100000);
            for (int id = 0; id < sources; id++) { string s; cin >> s; for (char c : s) { data.push_back(sources + 1 + c - 'a'); owner.push_back(id); } data.push_back(id + 1); owner.push_back(-1); }
            SuffixArray index(data); vector<int> count(sources); deque<int> minimum; int left = 0, kinds = 0, answer = 0;
            for (int right = 0; right < (int)index.sa.size(); right++) { int id = owner[index.sa[right]]; if (id >= 0 && count[id]++ == 0) kinds++;
                while (!minimum.empty() && index.height[minimum.back()] >= index.height[right]) minimum.pop_back(); minimum.push_back(right);
                while (kinds == sources) { while (!minimum.empty() && minimum.front() <= left) minimum.pop_front(); if (!minimum.empty()) answer = max(answer, index.height[minimum.front()]);
                    int removed = owner[index.sa[left++]]; if (removed >= 0 && --count[removed] == 0) kinds--; } }
            cout << answer;''',
            '多个分隔符也必须彼此不同，避免公共前缀穿过串尾。队列保存的是 LCP 下标，窗口左端对应的 height[left] 在窗口之外，要删去。',
            declarations=SUFFIX_ARRAY, complexity=r'拼接总长 $N$，时间 $O(N\log N)$，空间 $O(N)$。',
            cases=[{'input': '3\na\na\na', 'output': '1'}, {'input': '2\nabc\nxyz', 'output': '0'}])


if __name__ == '__main__':
    run()
    print('Registered two deterministic longest-common-substring articles.')
