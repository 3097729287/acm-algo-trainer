#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int a,b;cin>>a>>b;int difference=b-a,answer=abs(difference);
for(int ten=-40;ten<=40;++ten)for(int five=-40;five<=40;++five){
    // 一度按钮的净次数由总温差决定，不必成为第三重循环。
    int one=difference-10*ten-5*five;
    answer=min(answer,abs(ten)+abs(five)+abs(one));
}
cout<<answer<<'\n';
    return 0;
}
