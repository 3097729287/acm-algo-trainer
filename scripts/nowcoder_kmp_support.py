"""Generic prefix function and overlapping occurrence count, inlined as needed."""
PREFIX_FUNCTION = r'''
template<class Sequence> vector<int> prefixFunction(const Sequence &s) {
    int n = s.size(); vector<int> pi(n);
    for (int i = 1; i < n; i++) { int j = pi[i - 1]; while (j > 0 && s[i] != s[j]) j = pi[j - 1]; if (s[i] == s[j]) j++; pi[i] = j; }
    return pi;
}
'''
MATCH_OCCURRENCES = r'''
template<class Sequence> long long occurrences(const Sequence &text, const Sequence &pattern, const vector<int> &pi) {
    if (pattern.empty()) return text.size() + 1;
    int matched = 0; long long answer = 0;
    for (const auto &value : text) { while (matched > 0 && value != pattern[matched]) matched = pi[matched - 1]; if (value == pattern[matched]) matched++; if (matched == (int)pattern.size()) { answer++; matched = pi[matched - 1]; } }
    return answer;
}
'''
EXPLANATION = '前缀函数 pi[i] 记录前缀 s[0..i] 的最长相同真前后缀长度。失配时令已匹配长度 j=pi[j-1]，保留仍可能匹配的后缀；成功时 j 增一。每次回退都会减少 j，增长总数只与串长成正比，因此预处理和扫描均为线性。'
