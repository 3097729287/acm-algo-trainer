#include <bits/stdc++.h>
using namespace std;
struct Interval{int left,right,id;};
bool by_right(const Interval&a,const Interval&b){return a.right<b.right;}
bool assign_positions(vector<Interval>intervals,int n,vector<int>&answer){
    sort(intervals.begin(),intervals.end(),by_right);set<int>available;for(int i=1;i<=n;++i)available.insert(i);
    for(auto interval:intervals){auto at=available.lower_bound(interval.left);
        if(at==available.end()||*at>interval.right)return false;
        answer[interval.id]=*at;available.erase(at);
    }
    return true;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;while(cin>>n&&n){vector<Interval>x(n),y(n);for(int i=0;i<n;++i){cin>>x[i].left>>y[i].left>>x[i].right>>y[i].right;x[i].id=y[i].id=i;}
    // 两个方向各做一次独立匹配，结果仍按原车编号保存。
    vector<int>row(n),column(n);
    if(!assign_positions(x,n,row)||!assign_positions(y,n,column)){cout<<"IMPOSSIBLE\n";continue;}
    for(int i=0;i<n;++i)cout<<row[i]<<' '<<column[i]<<'\n';
}
    return 0;
}
