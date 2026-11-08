"""Reviewed two-dimensional periodic tile and minimum window maximum."""
from nowcoder_editorials import CONTENT, add, read
from nowcoder_kmp_support import PREFIX_FUNCTION


def run():
    if 'nowcoder-global::16638' in read(CONTENT / 'reviewed.json'):
        return
    add(16638, 2300, ['KMP', '二维单调队列', '周期'], '选一个能无限平铺出整个颜色矩阵的子块，最小化子块最大费用乘两边长加一。',
        '先确定最小的纵向周期 p 与横向周期 q。把每一行看成一个整体符号，用前缀函数得到 p=n-pi[n-1]；横向则把整列看成符号比较，得到 q=m-pi[m-1]。原矩阵只需是无限平铺矩阵的一部分，因此周期不必整除 n 或 m。逐行比较、逐列比较的每次代价分别为 m、n，而 KMP 比较次数线性，两项总计仍为 O(nm)。\n\n任何合法块的高、宽都分别是矩阵周期，不会小于 p、q。更大的候选块内部必含一个 p×q 子块，后者最大费用不更高，边长因子也不更大；又因颜色已经分别具有 p、q 周期，任意相位的 p×q 子块都能还原整个矩阵。所以最优一定可以取最小周期尺寸，只需在费用矩阵里找最大值最小的 p×q 窗口。\n\n先对每行用递减队列求宽 q 的窗口最大值，再对结果各列求高 p 的窗口最大值，最后取所有窗口最大值的最小值，乘 (p+1)(q+1)。',
        r'''int n, m; cin >> n >> m; vector<string> colors(n); for (auto &row : colors) cin >> row; auto vertical = prefixFunction(colors); int height = n - vertical.back();
        auto equalColumns = [&](int a, int b) { for (const auto &row : colors) if (row[a] != row[b]) return false; return true; }; vector<int> pi(m);
        for (int i = 1; i < m; i++) { int j = pi[i - 1]; while (j > 0 && !equalColumns(i, j)) j = pi[j - 1]; if (equalColumns(i, j)) j++; pi[i] = j; } int width = m - pi.back(), columns = m - width + 1;
        vector<int> horizontal(n * columns), row(m), queue(max(n, m)); for (int r = 0; r < n; r++) { for (int &x : row) cin >> x; int head = 0, tail = 0;
            for (int c = 0; c < m; c++) { while (head < tail && queue[head] <= c - width) head++; while (head < tail && row[queue[tail - 1]] <= row[c]) tail--; queue[tail++] = c; if (c + 1 >= width) horizontal[r * columns + c - width + 1] = row[queue[head]]; } }
        int best = INT_MAX; for (int c = 0; c < columns; c++) { int head = 0, tail = 0; for (int r = 0; r < n; r++) { while (head < tail && queue[head] <= r - height) head++; while (head < tail && horizontal[queue[tail - 1] * columns + c] <= horizontal[r * columns + c]) tail--; queue[tail++] = r; if (r + 1 >= height) best = min(best, horizontal[queue[head] * columns + c]); } }
        cout << 1LL * best * (height + 1) * (width + 1);''',
        '例如 acaca 的最小周期为二，长度五不能整除二也允许。子块可从矩阵任何位置选，不能只看左上角周期块。费用乘积使用 long long。',
        declarations=PREFIX_FUNCTION, complexity=r'时间、空间均为 $O(nm)$。',
        cases=[{'input': '1 3\naba\n9 2 1', 'output': '12'}, {'input': '2 2\naa\naa\n0 8\n7 9', 'output': '0'}])


if __name__ == '__main__':
    run()
    print('Registered the reviewed two-dimensional carpet solution.')
