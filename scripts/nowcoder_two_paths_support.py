TWO_PATHS = r'''
long long twoPaths(const vector<vector<int>> &a, bool disjoint) {
    int rows = a.size(), cols = a[0].size();
    if (disjoint && (rows == 1 || cols == 1)) return 0;
    const long long neg = -(1LL << 60);
    vector<vector<long long>> dp(rows,vector<long long>(rows,neg)), next = dp;
    dp[0][0] = a[0][0];
    for (int step = 1; step <= rows + cols - 2; step++) {
        for (auto &row : next) fill(row.begin(),row.end(),neg);
        int low = max(0,step-cols+1), high = min(rows-1,step);
        for (int r1 = low; r1 <= high; r1++) for (int r2 = low; r2 <= high; r2++) {
            if (disjoint && r1 == r2 && step != rows+cols-2) continue;
            long long previous = neg;
            for (int d1 = 0; d1 <= 1; d1++) for (int d2 = 0; d2 <= 1; d2++)
                if (r1 >= d1 && r2 >= d2) previous = max(previous,dp[r1-d1][r2-d2]);
            if (previous == neg) continue;
            long long gain = a[r1][step-r1];
            if (r1 != r2) gain += a[r2][step-r2];
            next[r1][r2] = previous + gain;
        }
        dp.swap(next);
    }
    return dp[rows-1][rows-1];
}
'''
