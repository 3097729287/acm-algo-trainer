#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    while (n--) {
        string name;
        int age, score;
        cin >> name >> age >> score;
        cout << name << ' ' << age + 1 << ' ' << min(600, score * 12 / 10) << '\n';
    }

    return 0;
}
