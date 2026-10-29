#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<long long>cnt(5001);int maximum=0;while(n--){int x;cin>>x;++cnt[x];maximum=max(maximum,x);}
const long long mod=1000000007;long long answer=0;
for(int s=2;s<=maximum;++s){long long full=cnt[s]*(cnt[s]-1)/2%mod;if(full==0)continue;
    for(int a=1;a*2<=s;++a){int b=s-a;long long split=a==b?cnt[a]*(cnt[a]-1)/2:cnt[a]*cnt[b];
        answer=(answer+full*(split%mod))%mod;
    }
}cout<<answer<<'\n';
    return 0;
}
