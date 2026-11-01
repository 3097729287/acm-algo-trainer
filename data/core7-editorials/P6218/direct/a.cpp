#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
long long l,r;cin>>l>>r;if(l>r) swap(l,r);
auto prefix=[&](long long x){
    if(x<=0) return 0LL;vector<int>digits;for(;x;x>>=1) digits.push_back(x&1);reverse(digits.begin(),digits.end());
    long long memo[32][65][2];memset(memo,-1,sizeof(memo));
    function<long long(int,int,bool,bool)> dfs=[&](int pos,int balance,bool started,bool tight)->long long{
        if(pos==int(digits.size())) return started&&balance>=0;
        long long &saved=memo[pos][balance+32][started];if(!tight&&saved>=0) return saved;
        long long result=0;int limit=tight?digits[pos]:1;
        for(int d=0;d<=limit;++d){bool ns=started||d;int next=ns?balance+(d==0?1:-1):0;result+=dfs(pos+1,next,ns,tight&&d==limit);}
        if(!tight) saved=result;return result;
    };
    return dfs(0,0,false,true);
};
cout<<prefix(r)-prefix(l-1)<<'\n';
    return 0;
}
