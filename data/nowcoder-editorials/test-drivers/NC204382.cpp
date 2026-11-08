int main() {
    string raw((istreambuf_iterator<char>(cin)), istreambuf_iterator<char>());
    vector<int> numbers;
    for (size_t i = 0; i < raw.size();) {
        if (raw[i] == '-' || isdigit(static_cast<unsigned char>(raw[i]))) {
            int sign = 1;
            if (raw[i] == '-') {
                sign = -1;
                i++;
            }
            int value = 0;
            while (i < raw.size() && isdigit(static_cast<unsigned char>(raw[i]))) {
                value = value * 10 + raw[i] - '0';
                i++;
            }
            numbers.push_back(sign * value);
        } else
            i++;
    }
    int n = numbers[0];
    vector<int> pre(numbers.begin() + 1, numbers.begin() + 1 + n),
        suf(numbers.begin() + 1 + n, numbers.end());
    auto result = Solution().solve(n, pre, suf);
    cout << '[';
    for (int i = 0; i < n; i++) {
        if (i)
            cout << ',';
        cout << result[i];
    }
    cout << ']';
}
