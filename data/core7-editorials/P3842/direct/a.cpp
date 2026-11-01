#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;long long bestL=0,bestR=0;int prevL=1,prevR=1;
for(int row=1;row<=n;++row){int l,r;cin>>l>>r;long long length=r-l,down=row>1;
    long long nextL=min(bestL+llabs(prevL-r),bestR+llabs(prevR-r))+length+down;
    long long nextR=min(bestL+llabs(prevL-l),bestR+llabs(prevR-l))+length+down;
    bestL=nextL;bestR=nextR;prevL=l;prevR=r;
}cout<<min(bestL+n-prevL,bestR+n-prevR)<<'\n';
    return 0;
}
