SUDOKU = r'''
struct Sudoku {
    int board[81] = {}, row[9] = {}, column[9] = {}, block[9] = {}, best = -1;
    bool first = false, consistent = true;
    int weight(int p) { int r = p / 9, c = p % 9; return 6 + min({r,c,8-r,8-c}); }
    int box(int p) { return p / 27 * 3 + p % 9 / 3; }
    int choices(int p) { return 511 & ~(row[p/9] | column[p%9] | block[box(p)]); }
    void toggle(int p, int digit) { int bit = 1 << (digit - 1); row[p/9] ^= bit; column[p%9] ^= bit; block[box(p)] ^= bit; }
    bool search(int score) {
        int selected = -1, mask = 0, fewest = 10, upper = score;
        for (int p = 0; p < 81; p++) if (!board[p]) {
            int options = choices(p), count = __builtin_popcount((unsigned)options);
            if (!count) return false;
            upper += (32 - __builtin_clz((unsigned)options)) * weight(p);
            if (count < fewest) { fewest = count; selected = p; mask = options; }
        }
        if (selected == -1) { best = max(best,score); return first; }
        if (!first && upper <= best) return false;
        for (int digit = 9; digit >= 1; digit--) if (mask >> (digit - 1) & 1) {
            board[selected] = digit; toggle(selected,digit);
            if (search(score + digit * weight(selected))) return true;
            toggle(selected,digit); board[selected] = 0;
        }
        return false;
    }
    void solve() {
        int score = 0;
        for (int p = 0; p < 81; p++) if (board[p]) {
            if (!(choices(p) >> (board[p] - 1) & 1)) { consistent = false; return; }
            toggle(p,board[p]); score += board[p] * weight(p);
        }
        search(score);
    }
};
'''
