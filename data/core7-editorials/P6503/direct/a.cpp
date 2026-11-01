#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<long long>a(n);for(auto &x:a) cin>>x;long long answer=0;
for(int maximum=0;maximum<2;++maximum){vector<int>stack;long long sum=0;
    for(int i=0;i<=n;++i){while(!stack.empty()&&(i==n||(maximum?a[stack.back()]<=a[i]:a[stack.back()]>=a[i]))){int j=stack.back();stack.pop_back();int left=stack.empty()?-1:stack.back();sum+=a[j]*(j-left)*(i-j);}if(i<n) stack.push_back(i);}
    if(maximum) answer+=sum;else answer-=sum;
}
cout<<answer<<'\n';
    return 0;
}
