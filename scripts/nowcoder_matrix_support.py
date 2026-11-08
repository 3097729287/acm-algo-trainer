MATRIX = r'''
using Matrix = vector<vector<long long>>;
constexpr long long MOD = 1000000007;
Matrix multiply(const Matrix &a,const Matrix &b) {
    int n = a.size(); Matrix result(n,vector<long long>(n));
    for (int i = 0; i < n; i++) for (int k = 0; k < n; k++) if (a[i][k])
        for (int j = 0; j < n; j++) result[i][j] = (result[i][j] + a[i][k] * b[k][j]) % MOD;
    return result;
}
vector<long long> applyMatrix(const Matrix &a,const vector<long long> &v) {
    int n = a.size(); vector<long long> result(n);
    for (int i = 0; i < n; i++) for (int j = 0; j < n; j++)
        result[i] = (result[i] + a[i][j] * v[j]) % MOD;
    return result;
}
'''
FIB = r'''
pair<long long,long long> fibonacci(unsigned long long n,long long mod) {
    if (!n) return {0,1};
    auto [a,b] = fibonacci(n / 2,mod);
    long long c = a * ((2*b-a+mod)%mod) % mod;
    long long d = (a*a%mod+b*b%mod)%mod;
    if (n & 1) return {d,(c+d)%mod};
    return {c,d};
}
'''
