#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int t;cin>>t;while(t--){int n,target;cin>>n>>target;vector<int>digits(1,1);
    for(int factor=2;factor<=n;++factor){int carry=0;
        for(int &digit:digits){int value=digit*factor+carry;digit=value%10;carry=value/10;}
        while(carry){digits.push_back(carry%10);carry/=10;}
    }
    int answer=0;for(int digit:digits)answer+=digit==target;cout<<answer<<'\n';
}
    return 0;
}
