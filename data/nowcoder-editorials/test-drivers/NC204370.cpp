int main() {
    string input((istreambuf_iterator<char>(cin)), istreambuf_iterator<char>());
    for (char &c : input)
        if (!isdigit((unsigned char)c))
            c = ' ';
    stringstream stream(input);
    int n, m;
    stream >> n >> m;
    vector<int> a(n);
    for (int &x : a)
        stream >> x;
    cout << Solution().solve(n, m, a);
}
