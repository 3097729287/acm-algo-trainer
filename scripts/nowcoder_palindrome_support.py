"""Linear odd/even palindrome radii, inlined in the actual references."""
MANACHER = r'''
struct PalindromeRadii {
    vector<int> odd, even;
    explicit PalindromeRadii(const string &s) {
        int n = s.size(); odd.resize(n); even.resize(n);
        int left = 0, right = -1;
        for (int i = 0; i < n; i++) {
            int k = i > right ? 1 : min(odd[left + right - i], right - i + 1);
            while (i - k >= 0 && i + k < n && s[i - k] == s[i + k]) k++;
            odd[i] = k;
            if (i + k - 1 > right) { left = i - k + 1; right = i + k - 1; }
        }
        left = 0; right = -1;
        for (int i = 0; i < n; i++) {
            int k = i > right ? 0 : min(even[left + right - i + 1], right - i + 1);
            while (i - k - 1 >= 0 && i + k < n && s[i - k - 1] == s[i + k]) k++;
            even[i] = k;
            if (i + k - 1 > right) { left = i - k; right = i + k - 1; }
        }
    }
};
'''
EXPLANATION = 'Manacher 的 odd[i] 表示以 i 为中心、包含中心的最大奇回文半径，长度为 2odd[i]-1；even[i] 表示中心在 i-1 与 i 之间的最大偶回文半径，长度为 2even[i]。维护已知最靠右的回文区间，利用镜像位置的半径初始化，再只向未知部分扩展。右边界只会前进，全部扩展次数为线性。'
