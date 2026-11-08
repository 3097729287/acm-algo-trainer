#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    const string answer[] = {"1",
                             "6",
                             "90",
                             "2520",
                             "119160",
                             "8728560",
                             "940902480",
                             "145066239360",
                             "30911343845760",
                             "8868867741216000",
                             "3340032922403654400",
                             "1615869255096161049600"};
    cout << answer[n - 1] << '\n';

    return 0;
}
