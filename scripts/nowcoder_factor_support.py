FACTOR = r'''
using U64 = unsigned long long;
U64 multiplyMod(U64 a,U64 b,U64 mod) { return (unsigned __int128)a*b%mod; }
U64 powerMod(U64 a,U64 n,U64 mod) { U64 value = 1; while (n) { if (n&1) value = multiplyMod(value,a,mod); a = multiplyMod(a,a,mod); n >>= 1; } return value; }
bool isPrime(U64 n) {
    if (n < 2) return false;
    for (U64 p : {2ULL,3ULL,5ULL,7ULL,11ULL,13ULL,17ULL,19ULL,23ULL,29ULL,31ULL,37ULL}) if (n%p == 0) return n == p;
    U64 odd = n-1; int twos = 0; while (!(odd&1)) { odd >>= 1; twos++; }
    for (U64 base : {2ULL,325ULL,9375ULL,28178ULL,450775ULL,9780504ULL,1795265022ULL}) {
        if (base%n == 0) continue;
        U64 value = powerMod(base%n,odd,n); if (value == 1 || value == n-1) continue;
        bool reachesMinusOne = false;
        for (int j = 1; j < twos; j++) { value = multiplyMod(value,value,n); if (value == n-1) { reachesMinusOne = true; break; } }
        if (!reachesMinusOne) return false;
    }
    return true;
}
U64 rho(U64 n) {
    if (n%2 == 0) return 2; if (n%3 == 0) return 3;
    static mt19937_64 random(20261108);
    for (;;) {
        U64 constant = random()%(n-1)+1, x = random()%(n-2)+2, y = x, divisor = 1;
        auto step = [&](U64 value) { return (U64)(((unsigned __int128)multiplyMod(value,value,n)+constant)%n); };
        while (divisor == 1) { x = step(x); y = step(step(y)); divisor = gcd(x>y ? x-y : y-x,n); }
        if (divisor != n) return divisor;
    }
}
void factor(U64 n,vector<U64> &factors) { if (n == 1) return; if (isPrime(n)) { factors.push_back(n); return; } U64 d = rho(n); factor(d,factors); factor(n/d,factors); }
'''
