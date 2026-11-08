"""Reference aggregate tree over either Z/(2^64) or a specified small modulus."""
AFFINE_TREE = r'''
struct AffineTree {
    using U = unsigned long long;
    struct Node { U sum = 0, squares = 0, multiply = 1, add = 0; };
    int n; U modulus; vector<Node> tree;
    AffineTree(const vector<U> &a, U mod) : n((int)a.size() - 1), modulus(mod), tree(4 * n + 4) { build(1, 1, n, a); }
    U plus(U a, U b) const { return modulus ? (a + b) % modulus : a + b; }
    U times(U a, U b) const { return modulus ? a * b % modulus : a * b; }
    U length(int len) const { return modulus ? (U)len % modulus : (U)len; }
    void pull(int p) { tree[p].sum = plus(tree[p * 2].sum, tree[p * 2 + 1].sum); tree[p].squares = plus(tree[p * 2].squares, tree[p * 2 + 1].squares); }
    void build(int p, int l, int r, const vector<U> &a) {
        if (l == r) { tree[p].sum = a[l]; tree[p].squares = times(a[l], a[l]); return; }
        int mid = (l + r) / 2; build(p * 2, l, mid, a); build(p * 2 + 1, mid + 1, r, a); pull(p);
    }
    void apply(int p, int len, U a, U b) {
        U old = tree[p].sum;
        tree[p].squares = plus(plus(times(times(a, a), tree[p].squares), times(times(times(2, a), b), old)), times(times(b, b), length(len)));
        tree[p].sum = plus(times(a, old), times(b, length(len)));
        tree[p].multiply = times(tree[p].multiply, a);
        tree[p].add = plus(times(tree[p].add, a), b);
    }
    void push(int p, int l, int r) {
        if (tree[p].multiply == 1 && tree[p].add == 0) return;
        int mid = (l + r) / 2; apply(p * 2, mid - l + 1, tree[p].multiply, tree[p].add); apply(p * 2 + 1, r - mid, tree[p].multiply, tree[p].add);
        tree[p].multiply = 1; tree[p].add = 0;
    }
    void change(int p, int l, int r, int ql, int qr, U a, U b) {
        if (ql <= l && r <= qr) { apply(p, r - l + 1, a, b); return; }
        push(p, l, r); int mid = (l + r) / 2; if (ql <= mid) change(p * 2, l, mid, ql, qr, a, b); if (qr > mid) change(p * 2 + 1, mid + 1, r, ql, qr, a, b); pull(p);
    }
    pair<U,U> query(int p, int l, int r, int ql, int qr) {
        if (ql <= l && r <= qr) return {tree[p].sum, tree[p].squares};
        push(p, l, r); int mid = (l + r) / 2; pair<U,U> result{0, 0};
        if (ql <= mid) result = query(p * 2, l, mid, ql, qr);
        if (qr > mid) { auto other = query(p * 2 + 1, mid + 1, r, ql, qr); result.first = plus(result.first, other.first); result.second = plus(result.second, other.second); }
        return result;
    }
};
'''
