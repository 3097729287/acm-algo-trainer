AC = r'''
struct Aho {
    struct Node { array<int,26> next={}; int fail=0,parent=0,letter=0,longest=0; };
    vector<Node> node; vector<int> order;
    int alphabet; char base;
    Aho(int alphabet,char base,size_t capacity):alphabet(alphabet),base(base) { node.reserve(capacity); node.emplace_back(); }
    int insert(const string &s) {
        int u=0;
        for (char ch:s) {
            int c=ch-base;
            if (!node[u].next[c]) {
                int v=node.size(); node[u].next[c]=v; node.emplace_back();
                node[v].parent=u; node[v].letter=c;
            }
            u=node[u].next[c];
        }
        node[u].longest=max(node[u].longest,(int)s.size()); return u;
    }
    void build() {
        order={0};
        for (int c=0;c<alphabet;c++) if (node[0].next[c]) order.push_back(node[0].next[c]);
        for (size_t i=1;i<order.size();i++) {
            int u=order[i],f=node[u].fail;
            node[u].longest=max(node[u].longest,node[f].longest);
            for (int c=0;c<alphabet;c++) {
                int v=node[u].next[c];
                if (v) { node[v].fail=node[f].next[c]; order.push_back(v); }
                else node[u].next[c]=node[f].next[c];
            }
        }
    }
};
'''
