#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;string s;cin>>n>>s;int answer=0;
for(int cut=0;cut<n;++cut){int total=0;char color='w';
    for(int step=0;step<n;++step){char c=s[(cut+step)%n];if(c!='w'&&color!='w'&&c!=color)break;if(c!='w')color=c;++total;}
    color='w';for(int step=0;total<n;++step){char c=s[(cut-1-step+n)%n];if(c!='w'&&color!='w'&&c!=color)break;if(c!='w')color=c;++total;}
    answer=max(answer,total);
}cout<<answer<<'\n';
    return 0;
}
