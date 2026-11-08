int main() {
    string raw((istreambuf_iterator<char>(cin)), {});
    for (char &c : raw)
        if (!isdigit((unsigned char)c))
            c = ' ';
    istringstream input(raw);
    int n, m;
    input >> n >> m;
    vector<Point> limit;
    for (int i = 0; i < m; i++) {
        int x, y;
        input >> x >> y;
        limit.emplace_back(x, y);
    }
    cout << Solution().solve(n, m, limit);
}
