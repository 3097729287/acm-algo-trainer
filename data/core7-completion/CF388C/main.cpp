#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    long long first = 0, second = 0;
    vector<int> middle;
    while (n--) {
        int size;
        cin >> size;
        vector<int> a(size);
        for (int &x : a)
            cin >> x;
        for (int i = 0; i < size / 2; i++) {
            first += a[i];
            second += a[size - 1 - i];
        }
        if (size % 2)
            middle.push_back(a[size / 2]);
    }
    sort(middle.rbegin(), middle.rend());
    for (int i = 0; i < (int)middle.size(); i++)
        if (i % 2)
            second += middle[i];
        else
            first += middle[i];
    cout << first << ' ' << second << '\n';

    return 0;
}
