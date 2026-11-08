#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> stack = {0};
    int answer = 0;
    while (n--) {
        int x, h;
        cin >> x >> h;
        while (stack.back() > h)
            stack.pop_back();
        if (stack.back() < h) {
            stack.push_back(h);
            answer++;
        }
    }
    cout << answer << '\n';

    return 0;
}
