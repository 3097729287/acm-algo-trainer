RANGE_MIN = r'''
struct RangeMinimum {
    int n; const long long inf = 1LL << 60;
    vector<long long> value,lazy;
    explicit RangeMinimum(int n) : n(n), value(4*n,1LL << 60), lazy(4*n) {}
    void apply(int p,long long delta) { value[p] += delta; lazy[p] += delta; }
    void push(int p) { if (lazy[p]) { apply(p*2,lazy[p]); apply(p*2+1,lazy[p]); lazy[p] = 0; } }
    void assign(int p,int l,int r,int position,long long x) {
        if (l == r) { value[p] = x; lazy[p] = 0; return; }
        push(p); int mid = (l+r)/2;
        if (position <= mid) assign(p*2,l,mid,position,x); else assign(p*2+1,mid+1,r,position,x);
        value[p] = min(value[p*2],value[p*2+1]);
    }
    void add(int p,int l,int r,int ql,int qr,long long delta) {
        if (ql <= l && r <= qr) { apply(p,delta); return; }
        push(p); int mid = (l+r)/2;
        if (ql <= mid) add(p*2,l,mid,ql,qr,delta);
        if (qr > mid) add(p*2+1,mid+1,r,ql,qr,delta);
        value[p] = min(value[p*2],value[p*2+1]);
    }
    long long query(int p,int l,int r,int ql,int qr) {
        if (ql <= l && r <= qr) return value[p];
        push(p); int mid = (l+r)/2; long long answer = inf;
        if (ql <= mid) answer = min(answer,query(p*2,l,mid,ql,qr));
        if (qr > mid) answer = min(answer,query(p*2+1,mid+1,r,ql,qr));
        return answer;
    }
};
'''
