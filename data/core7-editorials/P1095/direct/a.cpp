#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int mana;long long target;int seconds;cin>>mana>>target>>seconds;if(target==0){cout<<"Yes\n0\n";return 0;}
long long magic=0,best=0;for(int t=1;t<=seconds;++t){if(mana>=10){mana-=10;magic+=60;}else mana+=4;
    best=max(best+17,magic);if(best>=target){cout<<"Yes\n"<<t<<'\n';return 0;}
}cout<<"No\n"<<best<<'\n';
    return 0;
}
