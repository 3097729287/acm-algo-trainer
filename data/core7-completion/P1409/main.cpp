#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<double> previous(n + 1), current(n + 1), constant(n + 1);
    previous[1] = 1;
    for (int size = 2; size <= n; size++) {
        constant[1] = 0;
        double coefficient = 1;
        for (int position = 2; position <= size; position++) {
            coefficient *= 0.5;
            constant[position] = constant[position - 1] * 0.5 + previous[position - 1] / 3.0;
        }
        current[1] = (1.0 / 6 + constant[size] * 0.5) / (1 - coefficient * 0.5);
        for (int position = 2; position <= size; position++)
            current[position] = current[position - 1] * 0.5 + previous[position - 1] / 3.0;
        previous.swap(current);
    }
    cout << fixed << setprecision(9) << previous[m] << '\n';

    return 0;
}
