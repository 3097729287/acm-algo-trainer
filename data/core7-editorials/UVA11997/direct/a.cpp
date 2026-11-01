#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int k;while(cin>>k){vector<long long>a(k);for(auto &v:a)cin>>v;sort(a.begin(),a.end());
    for(int row=1;row<k;++row){vector<long long>b(k),next;for(auto &v:b)cin>>v;sort(b.begin(),b.end());next.reserve(k);
        using State=tuple<long long,int,int>;priority_queue<State,vector<State>,greater<State>>pq;
        for(int i=0;i<k;++i)pq.push({a[i]+b[0],i,0});
        // 相同数值保留出现次数，只取出当前最小的 k 个方案。
        for(int take=0;take<k;++take){auto [sum,i,j]=pq.top();pq.pop();next.push_back(sum);if(j+1<k)pq.push({a[i]+b[j+1],i,j+1});}
        a.swap(next);
    }
    for(int i=0;i<k;++i)cout<<a[i]<<(i+1==k?'\n':' ');
}
    return 0;
}
