#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;cin>>tests;while(tests--){int n,l;cin>>n>>l;l=max(l,2);vector<int>course(n),frequency(n+1),touched;for(int &x:course)cin>>x;
    int next_left=0,eligible=0;long long answer=0;
    for(int right=0;right<n;++right){
        if(right>0&&course[right]==course[right-1]){for(int x:touched)frequency[x]=0;touched.clear();next_left=right;eligible=0;}
        // 加入刚达到最小长度的左端，再排除首尾同值者。
        while(next_left<=right-l+1){int x=course[next_left++];if(frequency[x]==0)touched.push_back(x);++frequency[x];++eligible;}
        answer+=eligible-frequency[course[right]];
    }
    cout<<answer<<'\n';
}
    return 0;
}
