int main() {
    string raw((istreambuf_iterator<char>(cin)), {});
    for (char &c : raw)
        if (!isdigit((unsigned char)c))
            c = ' ';
    istringstream input(raw);
    int n;
    input >> n;
    vector<int> a(n);
    for (int &x : a)
        input >> x;
    cout << Solution().oddNumber(n, a);
}
