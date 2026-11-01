"""Actual tree states, coverage constraints and independent probability choices."""
import base64
import hashlib
import json
from editorial_figures import Figure,BLUE,RED,GREEN,GRAY
from core7_authoring import ROOT,OUT,roster_entries


def attach_figures(specs):
    pictures={};roster=roster_entries()
    previous={r['problem_id']:r.get('images',{}) for r in json.loads((ROOT/'data/library/solutions.json').read_text('utf-8'))}
    def save(pid,f,caption):
        p=f.save(pid,OUT/'figures');data='data:image/svg+xml;base64,'+base64.b64encode(p.read_bytes()).decode();key='assets/core7/'+pid+'.svg';old=previous.get(roster[pid]['id'],{})
        if key in old and old[key]!=data:key=key[:-4]+'-'+hashlib.sha256(data.encode()).hexdigest()[:10]+'.svg'
        pictures[pid]=(key,data,caption,old)
    def tree(f,points,edges,labels=None,selected=()):
        for u,v in edges:f.line(*points[u],*points[v],GREEN if u in selected and v in selected else GRAY,width=4)
        for u,p in enumerate(points):f.circle(*p,labels[u] if labels else u+1,GREEN if u in selected else BLUE)
    from core7_cases_tree_dp import morale_literal,dominating_sets,all_distances,paint_assignments,actual_dfs_orders,expectation_literal

    f=Figure('直径取不同孩子的两条链，长度按边数算',425)
    tree(f,[(150,150),(330,150),(330,280),(510,150),(650,280)],[(0,1),(1,2),(1,3),(3,4)],selected={1,2,3,4})
    f.text(70,350,'路径 3→2→4→5：共有 3 条边',GREEN,size=25)
    f.text(70,405,'以 2 为根，两条下行链分别长 1、2，合成 3',size=23)
    save('B4016',f,'五个圆是原树结点，绿色三条边组成一条最长简单路径；结点一是另一条同长直径的端点。')

    f=Figure('删去无宝叶子后，检查剩下的树是否分叉',455)
    for x,selected in [(205,{1,2,3}),(565,{1,2})]:
        points=[(x,185),(x-95,285),(x+95,285),(x,85)]
        for u,v in [(0,1),(0,2),(0,3)]:f.line(*points[u],*points[v],GRAY,dash=x==565 and v==3,width=4)
        for u,p in enumerate(points):f.circle(*p,u+1,GREEN if u in selected else GRAY)
    f.text(205,350,'三个分支有宝：No',RED,size=22,anchor='middle')
    f.text(565,350,'剪掉 4，走 2→1→3：Yes',GREEN,size=20,anchor='middle')
    f.text(45,420,'绿色有宝，灰色无宝；不能为了第三个分支重复经过边',size=22)
    save('P11249',f,'左右都是同一棵四点三叉树，仅四号点的宝藏状态不同。右边虚线为被剪去的无宝叶边。')

    f=Figure('完全二叉树的最后一层必须从左连续填',390)
    tree(f,[(220,115),(120,240)],[(0,1)])
    tree(f,[(520,115),(620,240)],[(0,1)])
    f.text(220,295,'只有左孩子：两棵子树都完全',GREEN,size=20,anchor='middle')
    f.text(540,335,'只有右孩子：只有叶子子树完全',RED,size=20,anchor='middle')
    f.text(60,375,'左右方向不能交换；空树可作高度零的满子树',size=22)
    save('P15801',f,'左图根有左孩子、右侧空，计二；右图根有右孩子、左侧空，根不是完全树，只计叶子。')

    f=Figure('增加短支入口，让所有叶子到根的时间相同',390)
    tree(f,[(380,105),(205,255),(555,255)],[(0,1),(0,2)])
    f.text(230,165,'原长 1',BLUE,size=23);f.text(465,165,'原长 3',BLUE,size=23)
    f.text(160,205,'补 2',GREEN,size=24);f.text(500,205,'补 0',GREEN,size=24)
    f.text(60,345,'根到两个叶子最后都为 3，最少总增量为 2',GREEN,size=24)
    save('P1131',f,'只有增加边长可选，不能缩短三的长支；在短支加二便同步两个叶子的到达时间。')

    assert dominating_sets(3,[(0,1),(1,2)],[1,100,1])==2
    f=Figure('低价的两个端点可以共同覆盖中间点',405)
    tree(f,[(150,170),(380,170),(610,170)],[(0,1),(1,2)],labels=['1','2','3'],selected={0,2})
    for x,cost in [(150,1),(380,100),(610,1)]:f.text(x,240,f'费用 {cost}',size=23,anchor='middle')
    f.text(60,320,'设岗 {1,3}：总费 2；只设中点：总费 100',GREEN,size=23)
    f.text(60,380,'未设岗点 2 被两个岗覆盖也合法，要求至少一次',size=22)
    save('P2458',f,'绿色端点设岗，二号同时相邻两个岗仍然合规；与客户恰好一个服务器的另一题要求不同。')

    f=Figure('沿一条边换根，边两侧的牛群距离一增一减',420)
    tree(f,[(140,180),(380,180),(620,180)],[(0,1),(1,2)])
    for x,count in [(140,0),(380,1),(620,2)]:f.text(x,110,f'{count} 头牛',size=23,anchor='middle')
    f.text(260,165,'长 2',BLUE,size=20,anchor='middle');f.text(500,165,'长 3',BLUE,size=20,anchor='middle')
    f.text(65,290,'牛棚从 2 移到 3：两头牛各近 3，一头牛远 3',size=22)
    f.text(65,350,'总费从 6 变成 3，变化为 3×(3−2×2)=−3',GREEN,size=22)
    save('P2986',f,'树边长度为二与三，点上的牛数为零一二；费用按每头牛到棚的路径长度逐头相加。')

    assert paint_assignments(4,[(0,1),(0,2),(0,3)],{1:0,2:1})==2
    f=Figure('固定两个不同颜色叶子，根只剩第三种颜色',420)
    tree(f,[(380,110),(170,260),(380,260),(590,260)],[(0,1),(0,2),(0,3)],labels=['色3','色1','色2','?'])
    f.text(60,345,'根只能色 3；右叶可色 1 或色 2，共 2 种',GREEN,size=23)
    f.text(60,400,'每个孩子先对不同于父色的状态求和，再在孩子间相乘',size=21)
    save('P4084',f,'一号为根，二三号分别预涂颜色一与二；四号未预涂，两个可选颜色分别形成一份完整涂色方案。')

    f=Figure('新增叶子只新增它与旧点的距离，查询彼此独立',420)
    tree(f,[(120,170),(330,170),(550,170),(330,300)],[(0,1),(1,2),(1,3)],labels=['1','2','3','新'],selected={3})
    f.text(225,150,'2',BLUE,size=23);f.text(440,150,'3',BLUE,size=23);f.text(355,245,'4',GREEN,size=23)
    f.text(60,365,'旧无序距离和 10；新叶距离为 6、4、7，总计 17',size=21)
    f.text(60,405,'有序总和 = 2×(10+17)=54；自身距离为零',GREEN,size=22)
    save('P9584',f,'旧树一二三号边长二与三，本次在二号接一条长度四的新边。下一次查询会重新使用旧三点树。')

    assert actual_dfs_orders(4,[(0,1),(1,2),(2,3)])==6
    f=Figure('四点链有六个不同 DFS 首次访问序列',425)
    tree(f,[(110,110),(290,110),(470,110),(650,110)],[(0,1),(1,2),(2,3)])
    for y,text in [(205,'根 1：1234；根 2：2134 或 2341'),(275,'根 3：3214 或 3421；根 4：4321')]:f.text(65,y,text,size=23)
    f.text(65,350,'固定根：根的孩子有 deg! 种排列，其它点为 (deg−1)!',size=21)
    f.text(65,405,'仅首次进入的结点写入序列；回退本身不再写一次',size=22)
    save('P13020',f,'列出这棵四点链的全部六份首次访问序列，相同根的每种邻居处理先后都能实际执行。')

    f=Figure('已知受害点只列一部分，比较到它们的最远距离',420)
    tree(f,[(130,170),(300,170),(470,170),(640,170)],[(0,1),(1,2),(2,3)],selected={0,3})
    f.text(60,285,'受害点为 1、4，半径 d=2；可能源头是 2 或 3',GREEN,size=23)
    f.text(60,350,'点 2 到两个标记距离为 1、2，最大值 2 合格',size=22)
    f.text(60,405,'“未列为受害点”不等于“未受影响”，不能排除 2、3',size=21)
    save('CF337D',f,'绿色一四号是已知标记，不是候选源头集合；中间两个结点都能在半径二覆盖全部已知标记。')

    f=Figure('只统计最高不同位，平局把 x 的低位留零',390)
    for y,label,values in [(85,'原值',[3,0]),(180,'异或 2 后',[1,2])]:f.text(55,y+32,label,size=22);f.row(values,y,x=300,width=160)
    f.text(65,295,'原来有 1 对逆序；选 x=2，变成 0 对',GREEN,size=24)
    f.text(65,355,'x=3 也能零逆序，但更大，所以答案取 x=2',size=22)
    save('CF1416C',f,'二进制十一与零零在高一位首次不同，翻转该位即可；低位不影响这对数的大小，保持零使x最小。')

    f=Figure('环边的两个端点不能同时选，断边后仍要保留约束',455)
    points=[(200,120),(420,120),(310,280),(640,250)]
    tree(f,points,[(1,2),(2,0),(1,3)],labels=['0','1','2','3'],selected={0,3})
    f.line(points[0][0]+25,points[0][1],points[1][0]-25,points[1][1],RED,dash=True,width=4)
    for x,y,w in [(165,85,1),(455,85,2),(310,335,1),(640,315,5)]:f.text(x,y,f'人流 {w}',size=21,anchor='middle')
    f.text(60,400,'删红边后，分别禁选 0 或 1；可选 {0,3} 得 6',GREEN,size=22)
    f.text(60,440,'倍率为 2 时利润 12.0；不能同时选 0、1',size=22)
    save('P1453',f,'沿用原样例的零起始编号、三角环及一号到三号尾边；绿色零三号合法，红虚线表示暂不加入树的环边。')

    f=Figure('可以提前给下一层准备，每轮三次已足够',450)
    tree(f,[(380,90),(380,190),(140,310),(300,310),(460,310),(620,310)],[(0,1),(1,2),(1,3),(1,4),(1,5)],selected={0,1,2,3})
    f.text(55,375,'初始仅 1 黑；首轮把 2、3、4 染黑，对手走到 2',size=22)
    f.text(55,430,'第二轮再染 5、6：不必按最大孩子数回答 4',GREEN,size=22)
    save('P3554',f,'绿色展示第一轮结束后的已黑点，一号原本黑，新增二三四号恰好三个；对手只能由一号到二号。')

    f=Figure('同一路线的两个比例都得满足，所以取较小者',470)
    tree(f,[(380,85),(220,195),(540,195),(130,320),(310,320),(540,320)],[(0,1),(0,2),(1,3),(1,4),(2,5)],labels=['u','v','6','4','5','7'])
    f.text(55,385,'v 子树有 3 人；u 共 5 名下属，向上传播比例 3/5',size=21)
    f.text(55,430,'v 内两个叶子只能提供 1/2，整条路线受 1/2 限制',GREEN,size=21)
    f.text(55,465,'初始一名叛徒不会直接命令它的下属全部加入',size=21)
    save('P5958',f,'图中v有两个叶子，内部先形成三人子树的临界比例为二分之一；再向u传播还需不高于五分之三，取较小的二分之一。')

    assert morale_literal([-1,0,0,1],[6,-2,4,-7])==5
    f=Figure('同色孩子触发其子树内同色点，负战力不能跳过',460)
    tree(f,[(380,100),(200,220),(560,220),(200,335)],[(0,1),(0,2),(1,3)],labels=['6','−2','4','−7'],selected={0,2,3})
    f.text(55,395,'绿色作黑、蓝色作白：根只增加右孩子的 4',size=22)
    f.text(55,445,'总士气为 10−2+4−7=5；不能越过白孩子直接加 −7',size=20)
    save('P8916',f,'原四点样例的一份最优染色，图上标的是原战力；根与负二异色，不通过该子边触发，负七仍计自己的负士气。')

    f=Figure('内部名次与全局实力不同，先求能赢的相对名次',440)
    tree(f,[(380,95),(205,210),(555,210),(100,315),(280,315),(480,315),(660,315)],[(0,1),(0,2),(1,3),(1,4),(2,5),(2,6)],labels=['min','max','max','?','?','?','?'])
    f.text(55,385,'四人先各取强，再在决赛取弱，冠军只能相对第 2 或 3',size=20)
    f.text(55,430,'进入第 2 轮只需赢一场；进入第 3 轮才是冠军',GREEN,size=21)
    save('P10767',f,'满二叉签表两场半决赛取强者，决赛取弱者；冠军不会是最弱或最强，而实力二和三都存在可行分组。')

    edges=[(0,2),(1,2),(2,3),(3,4),(3,5)]
    assert dominating_sets(6,edges,[1]*6,True)==2
    f=Figure('服务器可以相邻，客户必须恰好只有一个相邻服务器',445)
    tree(f,[(120,105),(120,300),(300,200),(460,200),(640,105),(640,300)],edges,selected={2,3})
    f.text(55,375,'选服务器 3、4：客户 1、2、5、6 各由一台服务',GREEN,size=22)
    f.text(55,425,'服务器自己不是客户；不能额外禁止绿色两点相邻',size=21)
    save('UVA1218',f,'原PDF六点例图的合法服务器集合三与四，两台相邻仍满足全部四名客户各恰好一个服务器邻居。')

    from fractions import Fraction
    assert expectation_literal([-1,0,0])==Fraction(7,6)
    f=Figure('随机前沿的候选等概率，合法完整序列未必等概率',465)
    tree(f,[(380,100),(210,250),(550,250)],[(0,1),(0,2)])
    f.text(55,330,'根为 1：顺序 123 或 132，逆序期望 1/2',size=22)
    f.text(55,385,'根为 2：213，逆序 1；根为 3：312，逆序 2',size=21)
    f.text(55,445,'三种初始根等概率：总期望 (1/2+1+2)/3=7/6',GREEN,size=22)
    save('CF1540B',f,'实际三点树对应原样例，根一时两叶各有二分之一机会先被选；根二或三时后续候选顺序唯一。')

    for spec in specs:
        if spec.pid not in pictures:continue
        key,data,caption,old=pictures[spec.pid];spec.images.update(old);spec.images[key]=data
        figure='\n\n!['+caption+']('+key+')\n\n';spec.brief=figure+spec.brief;spec.detail=figure+spec.detail
