#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<long long>a(3*n);for(int i=0;i<n;++i){cin>>a[i];a[i+n]=a[i+2*n]=a[i];}
long long low=*min_element(a.begin(),a.begin()+n),high=*max_element(a.begin(),a.begin()+n);
if(2*low>=high){for(int i=0;i<n;++i) cout<<(i?" ":"")<<-1;cout<<'\n';return 0;}
deque<int>queue;int right=0;
for(int left=0;left<n;++left){
    while(right<3*n&&(queue.empty()||2*a[right]>=a[queue.front()])){while(!queue.empty()&&a[queue.back()]<=a[right]) queue.pop_back();queue.push_back(right);++right;}
    cout<<(left?" ":"")<<right-left;if(!queue.empty()&&queue.front()==left) queue.pop_front();
}
cout<<'\n';
    return 0;
}
