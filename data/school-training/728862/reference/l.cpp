#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    long long t;
    cin >> n >> t;
    vector<int> a(n);
    for (int &v : a) cin >> v;
    long long sum = 0;
    int left = 0, answer = 0;
    for (int right = 0; right < n; ++right) {
        sum += a[right];
        while (sum > t) {
            sum -= a[left];
            ++left;
        }
        // 对这个右端点，left 已是最靠左的合法起点。
        answer = max(answer, right - left + 1);
    }
    cout << answer << '\n';
}
