#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> a(n);
    int maximum = 0;
    for (int &x : a) {
        cin >> x;
        maximum = max(maximum, x);
    }
    vector<int> frequency(maximum + 1);
    for (int x : a)
        frequency[x]++;
    vector<int> all, removable;
    for (int x = 1; x <= maximum; x++)
        if (frequency[x]) {
            all.push_back(frequency[x]);
            bool hasMultiple = false;
            for (int y = x + x; y <= maximum; y += x)
                if (frequency[y]) {
                    hasMultiple = true;
                    break;
                }
            if (hasMultiple)
                removable.push_back(frequency[x]);
        }
    sort(all.begin(), all.end());
    sort(removable.begin(), removable.end());
    vector<int> prefix(all.size() + 1), cheap(removable.size() + 1);
    for (int i = 0; i < (int)all.size(); i++)
        prefix[i + 1] = prefix[i] + all[i];
    for (int i = 0; i < (int)removable.size(); i++)
        cheap[i + 1] = cheap[i] + removable[i];
    int distinct = all.size();
    vector<int> answer(n + 1, distinct);
    for (int reduction = 1; reduction < distinct; reduction++) {
        int cost = prefix[reduction + 1];
        if (reduction < (int)cheap.size())
            cost = min(cost, cheap[reduction]);
        answer[cost] = min(answer[cost], distinct - reduction);
    }
    for (int k = 1; k <= n; k++)
        answer[k] = min(answer[k], answer[k - 1]);
    for (int k = 0; k <= n; k++)
        cout << answer[k] << (k == n ? '\n' : ' ');

    return 0;
}
