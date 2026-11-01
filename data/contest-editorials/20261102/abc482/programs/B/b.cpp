#include <bits/stdc++.h>
using namespace std;
int main() {
    vector<string> s(5);
    for (auto &row : s) cin >> row;
    int answer = 5;
    for (int i = 0; i < 5; ++i) {
        int row = 0, column = 0;
        for (int j = 0; j < 5; ++j) { row += s[i][j] == '.'; column += s[j][i] == '.'; }
        answer = min(answer, min(row, column));
    }
    int main_diagonal = 0, other_diagonal = 0;
    for (int i = 0; i < 5; ++i) { main_diagonal += s[i][i] == '.'; other_diagonal += s[i][4 - i] == '.'; }
    cout << min(answer, min(main_diagonal, other_diagonal)) << '\n';
}
