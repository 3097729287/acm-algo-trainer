#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long long> stack;
    long long answer = 0;
    while (n--) {
        long long x;
        cin >> x;
        while (!stack.empty() && stack.back() <= x)
            stack.pop_back();
        answer += stack.size();
        stack.push_back(x);
    }
    cout << answer << '\n';

    return 0;
}
