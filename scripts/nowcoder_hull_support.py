HULL = r'''
using Wide = __int128;
struct MonotoneHull {
    struct Line { Wide slope, intercept; Wide at(Wide x) const { return slope*x+intercept; } };
    deque<Line> lines;
    void add(Wide slope, Wide intercept) {
        Line line{slope,intercept};
        while (!lines.empty() && lines.back().slope == slope) {
            if (lines.back().intercept <= intercept) return;
            lines.pop_back();
        }
        while (lines.size() >= 2) {
            auto a = lines[lines.size()-2], b = lines.back();
            if ((b.intercept-a.intercept)*(b.slope-line.slope) <
                (line.intercept-b.intercept)*(a.slope-b.slope)) break;
            lines.pop_back();
        }
        lines.push_back(line);
    }
    Wide minimum(Wide x) {
        while (lines.size() >= 2 && lines[1].at(x) <= lines[0].at(x)) lines.pop_front();
        return lines.front().at(x);
    }
};
void printWide(Wide value) {
    if (value < 0) { cout << '-'; value = -value; }
    string digits;
    do { digits += char('0'+value%10); value /= 10; } while (value);
    reverse(digits.begin(),digits.end()); cout << digits;
}
'''
HULL_EXPLANATION = '直线斜率按非增顺序加入，查询横坐标非减。维护下凸壳：新线使末尾两线的交点顺序逆转时，删除中间线，交点顺序用交叉乘积精确比较。斜率相同时只保留截距更小者。查询时若第二条线不劣于第一条，就弹掉第一条；随着横坐标变大，它也不会重新更优。每条线至多进出队一次。代码用128位处理中间乘积，避免平方及交点比较溢出。'
