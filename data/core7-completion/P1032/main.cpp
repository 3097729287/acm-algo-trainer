#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string start, goal;
    cin >> start >> goal;
    vector<pair<string, string>> rules;
    string a, b;
    while (cin >> a >> b)
        rules.push_back({a, b});
    auto search = [&](string initial, bool reverseRule) {
        unordered_map<string, int> distance;
        queue<string> q;
        distance[initial] = 0;
        q.push(initial);
        while (!q.empty()) {
            string s = q.front();
            q.pop();
            int depth = distance[s];
            if (depth == 5)
                continue;
            for (auto rule : rules) {
                string from = reverseRule ? rule.second : rule.first,
                       to = reverseRule ? rule.first : rule.second;
                for (size_t pos = s.find(from); pos != string::npos; pos = s.find(from, pos + 1)) {
                    string next = s.substr(0, pos) + to + s.substr(pos + from.size());
                    if (distance.emplace(next, depth + 1).second)
                        q.push(next);
                }
            }
        }
        return distance;
    };
    auto forward = search(start, false), backward = search(goal, true);
    int ans = 11;
    for (auto &[s, d] : forward) {
        auto it = backward.find(s);
        if (it != backward.end())
            ans = min(ans, d + it->second);
    }
    if (ans <= 10)
        cout << ans << '\n';
    else
        cout << "NO ANSWER!\n";

    return 0;
}
