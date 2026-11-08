int main() {
    string raw((istreambuf_iterator<char>(cin)), {});
    for (char &c : raw)
        if (!isdigit((unsigned char)c))
            c = ' ';
    istringstream input(raw);
    int n, m;
    input >> n >> m;
    cout << Solution().solve(n, m);
}
