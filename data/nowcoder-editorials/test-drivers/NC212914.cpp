int main() {
    string s;
    cin >> s;
    if (s.size() >= 2 && s.front() == '"' && s.back() == '"')
        s = s.substr(1, s.size() - 2);
    cout << Solution().legalExp(s);
}
