#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<pair<long long, long long>> stack;
    long long sum = 0;
    for (int i = 0; i < n; i++) {
        long long h;
        cin >> h;
        long long count = 1;
        while (!stack.empty() && stack.back().first <= h) {
            auto [value, number] = stack.back();
            stack.pop_back();
            sum -= value * number;
            count += number;
        }
        stack.push_back({h, count});
        sum += h * count;
        cout << sum + 1 << (i + 1 == n ? '\n' : ' ');
    }

    return 0;
}
