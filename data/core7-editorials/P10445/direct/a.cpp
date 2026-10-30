#include <bits/stdc++.h>
using namespace std;
struct Location{long long x;int id;};
bool by_position(const Location&a,const Location&b){return a.x!=b.x?a.x<b.x:a.id<b.id;}
struct RangeMin{
    int base=1;vector<int>tree;
    RangeMin(const vector<Location>&points,int original){
        while(base<(int)points.size())base*=2;tree.assign(2*base,INT_MAX);
        for(int i=0;i<(int)points.size();++i)if(points[i].id<=original)tree[base+i]=points[i].id;
        for(int i=base-1;i>0;--i)tree[i]=min(tree[2*i],tree[2*i+1]);
    }
    int query(int l,int r)const{
        if(l>r)return INT_MAX;int answer=INT_MAX;l+=base;r+=base;
        while(l<=r){if(l&1)answer=min(answer,tree[l++]);if(!(r&1))answer=min(answer,tree[r--]);l/=2;r/=2;}
        return answer;
    }
};
bool lex_better(int l,int r,int old_l,int old_r,const RangeMin&minimum){
    int added=min(minimum.query(l,min(r,old_l-1)),minimum.query(max(l,old_r+1),r));
    int removed=min(minimum.query(old_l,min(old_r,l-1)),minimum.query(max(old_l,r+1),old_r));
    return added<removed;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,p;long long budget;cin>>n>>budget>>p;vector<Location>points;points.reserve(n+1);
for(int id=1;id<=n;++id){long long x;cin>>x;points.push_back({x,id});}points.push_back({0,n+1});sort(points.begin(),points.end(),by_position);
int origin=0,gift=0;for(int i=0;i<=n;++i){if(points[i].id==n+1)origin=i;if(points[i].id==p)gift=i;}
RangeMin minimum(points,n);int best_left=origin,best_right=origin,best_count=0;
for(int pass=0;pass<2;++pass){long long width=(budget+(pass?5:0))/2;int left=0;
    for(int right=0;right<=n;++right){while(points[right].x-points[left].x>width)++left;
        if(!(left<=origin&&origin<=right))continue;
        if(pass&&!(left<=gift&&gift<=right))continue;
        int count=right-left; // 窗口内含一个不计数的虚拟原点
        if(count>best_count||(count==best_count&&lex_better(left,right,best_left,best_right,minimum))){best_count=count;best_left=left;best_right=right;}
    }
}
cout<<best_count<<'\n';bool first=true;
for(int i=best_left;i<=best_right;++i)if(points[i].id<=n){if(!first)cout<<' ';first=false;cout<<points[i].id;}cout<<'\n';
    return 0;
}
