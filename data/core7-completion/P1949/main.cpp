#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string s, t;
    cin >> s >> t;
    int start = stoi(s), goal = stoi(t);
    if (start == goal) {
        cout << 0 << '\n';
        return 0;
    }
    int power[6] = {100000, 10000, 1000, 100, 10, 1};
    vector<unsigned char> distance(6000000, 255);
    vector<int> queue;
    queue.reserve(6000000);
    queue.push_back(start * 6);
    distance[start * 6] = 0;
    for (size_t front = 0; front < queue.size(); front++) {
        int state = queue[front], code = state / 6, p = state % 6, depth = distance[state];
        if (code == goal) {
            cout << depth << '\n';
            return 0;
        }
        auto push = [&](int next) {
            if (distance[next] == 255) {
                distance[next] = depth + 1;
                queue.push_back(next);
            }
        };
        if (p)
            push(code * 6 + p - 1);
        if (p < 5)
            push(code * 6 + p + 1);
        int digit = code / power[p] % 10;
        if (digit < 9)
            push((code + power[p]) * 6 + p);
        if (digit > 0)
            push((code - power[p]) * 6 + p);
        for (int q : {0, 5}) {
            int other = code / power[q] % 10;
            int next = code + (other - digit) * power[p] + (digit - other) * power[q];
            push(next * 6 + p);
        }
    }

    return 0;
}
