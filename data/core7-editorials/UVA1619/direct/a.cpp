#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;bool first=true;
while(cin>>n){vector<long long>a(n),prefix(n+1);for(int i=0;i<n;++i){cin>>a[i];prefix[i+1]=prefix[i]+a[i];}
    vector<int>left(n),right(n),stack;
    for(int i=0;i<n;++i){while(!stack.empty()&&a[stack.back()]>=a[i]) stack.pop_back();left[i]=stack.empty()?0:stack.back()+1;stack.push_back(i);}
    stack.clear();for(int i=n-1;i>=0;--i){while(!stack.empty()&&a[stack.back()]>=a[i]) stack.pop_back();right[i]=stack.empty()?n-1:stack.back()-1;stack.push_back(i);}
    long long best=0;int bestLeft=0,bestRight=0;
    for(int i=0;i<n;++i){int l=left[i],r=right[i];long long value=a[i]*(prefix[r+1]-prefix[l]);if(value>best||(value==best&&make_pair(r-l,l)<make_pair(bestRight-bestLeft,bestLeft))){best=value;bestLeft=l;bestRight=r;}}
    if(!first) cout<<'\n';first=false;cout<<best<<'\n'<<bestLeft+1<<' '<<bestRight+1<<'\n';
}
    return 0;
}
