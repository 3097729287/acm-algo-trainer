COVER = r'''
struct CoverTree {
    vector<long long> coordinate,length; vector<int> count;
    CoverTree(vector<long long> x): coordinate(move(x)),length(coordinate.size()*4+4),count(length.size()) {}
    void change(int u,int l,int r,int ql,int qr,int delta) {
        if (ql<=l && r<=qr) count[u]+=delta;
        else { int mid=(l+r)/2; if (ql<=mid) change(u*2,l,mid,ql,qr,delta); if (qr>mid) change(u*2+1,mid+1,r,ql,qr,delta); }
        if (count[u]) length[u]=coordinate[r+1]-coordinate[l];
        else length[u]=l==r?0:length[u*2]+length[u*2+1];
    }
};
'''
AREA = r'''
int n; cin >> n;
struct Event { long long x,low,high; int delta; };
vector<Event> event; vector<long long> y;
for (int i=0;i<n;i++) {
    long long x1,y1,x2,y2; cin >> x1 >> y1 >> x2 >> y2;
    if (x1>x2) swap(x1,x2); if (y1>y2) swap(y1,y2);
    if (x1==x2 || y1==y2) continue;
    event.push_back({x1,y1,y2,1}); event.push_back({x2,y1,y2,-1});
    y.push_back(y1); y.push_back(y2);
}
if (event.empty()) { cout << 0; return 0; }
sort(y.begin(),y.end()); y.erase(unique(y.begin(),y.end()),y.end());
sort(event.begin(),event.end(),[](auto a,auto b) { return a.x<b.x; });
CoverTree tree(y); long long area=0,previous=event[0].x;
for (auto e : event) {
    area+=(e.x-previous)*tree.length[1]; previous=e.x;
    int l=lower_bound(y.begin(),y.end(),e.low)-y.begin();
    int r=lower_bound(y.begin(),y.end(),e.high)-y.begin()-1;
    tree.change(1,0,(int)y.size()-2,l,r,e.delta);
}
cout << area;
'''
