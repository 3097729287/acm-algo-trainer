"""Draw actual rooted trees, budgets, point sets and endpoint relations."""
import base64
import hashlib
import json
from html import escape
from editorial_figures import Figure,BLUE,RED,GREEN,GRAY
from core7_authoring import ROOT,OUT,roster_entries


def attach_figures(specs):
    pictures={};roster=roster_entries()
    previous={r['problem_id']:r.get('images',{}) for r in json.loads((ROOT/'data/library/solutions.json').read_text('utf-8'))}
    def save(pid,f,caption):
        p=f.save(pid,OUT/'figures');data='data:image/svg+xml;base64,'+base64.b64encode(p.read_bytes()).decode();key='assets/core7/'+pid+'.svg'
        old=previous.get(roster[pid]['id'],{})
        if key in old and old[key]!=data:key=key[:-4]+'-'+hashlib.sha256(data.encode()).hexdigest()[:10]+'.svg'
        pictures[pid]=(key,data,caption,old)
    def tree(f,points,edges,marked=(),red=()):
        for u,v in edges:f.line(*points[u],*points[v],GREEN if u in marked and v in marked else GRAY,width=4)
        for u,(x,y) in points.items():f.circle(x,y,u,GREEN if u in marked else RED if u in red else BLUE)

    f=Figure('后序末尾的 A 定根，中序在 A 处分开',420)
    p={'A':(230,100),'B':(110,220),'C':(350,220),'D':(280,330)}
    tree(f,p,[('A','B'),('A','C'),('C','D')])
    for y,text in [(125,'中序：B A D C'),(200,'后序：B D C A'),(275,'先序：A B C D')]:f.text(440,y,text,size=23)
    f.text(65,395,'A 左边只有 B；右子树根为 C，D 是 C 的左孩子',size=21)
    save('P1030',f,'根、左右子树以及三种访问顺序来自同一棵树；不能把中序右半部分误当成先序。')

    f=Figure('决赛先由两半区各选最强者，亚军是较弱的一位',430)
    f.row([4,2,3,1],100,x=35,width=82);f.row([10,5,9,7],100,x=405,width=82)
    f.text(70,185,'队号 1、2、3、4',size=21);f.text(440,185,'队号 5、6、7、8',size=21)
    f.line(200,198,200,245,GREEN);f.line(570,198,570,245,GREEN)
    f.box(95,245,210,52,'第一队：能力 4',RED);f.box(465,245,210,52,'第五队：能力 10',GREEN)
    f.line(200,298,385,350,RED);f.line(570,298,385,350,GREEN)
    f.text(385,380,'冠军 5；亚军 1',GREEN,size=25,anchor='middle')
    f.text(95,417,'全体次大能力 9 在第五队同半区，进不了决赛',size=21)
    save('P4715',f,'八支队的完整能力值与原样例一致；左右半区分别产生决赛队伍，而不是取全体第二大。')

    f=Figure('中点相同，三组无序配对对应六个有序点对',360)
    p={'c':(240,160),'2':(85,280),'5':(240,280),'10':(395,280)}
    tree(f,p,[('c','2'),('c','5'),('c','10')])
    f.text(455,140,'圆内数字为叶权',size=21);f.text(455,200,'最大：5×10=50',GREEN,size=22)
    f.text(455,260,'有序和：160',GREEN,size=23);f.text(50,340,'先累加 2×新权值×此前邻居权和，再更新邻居权和',size=21)
    save('P1351',f,'三个叶子距离两两为二，中点唯一；不把中心自身和叶子配成距离二的点对。')

    f=Figure('同点、祖先关系与跨分支 LCA 都保留',385)
    p={4:(350,100),2:(160,200),1:(530,200),3:(450,300),5:(650,300)}
    tree(f,p,[(4,2),(4,1),(1,3),(1,5)])
    f.text(55,350,'LCA(2,4)=4；LCA(3,2)=4；LCA(3,5)=1',size=22)
    save('P3379',f,'根为四号，输入边不决定根；一次向上对齐后如果两点相同，应立即返回。')

    f=Figure('最近共同领导是 2，但最大编号的共同领导是 5',440)
    p={0:(100,90),5:(260,180),2:(390,270),3:(295,365),4:(520,365),1:(100,270)}
    tree(f,p,[(0,5),(5,2),(2,3),(2,4),(0,1)],marked={0,5,2})
    f.text(435,115,'参与者：3、4',size=22);f.text(435,175,'共同领导：2、5、0',size=21)
    f.text(435,225,'取最大编号 5',GREEN,size=24);f.text(60,422,'输入领导编号不必小于下属；不能直接输出 LCA',size=21)
    save('P10113',f,'完整六人合法树，五号是二号的领导；这是直接输出最近公共祖先会错的具体情形。')

    from core7_cases_trees import picture
    f=Figure('删除右孩子及子树后，左子树仍在原来的字符列',400)
    rows=picture(3,{(1,1)}).splitlines()
    for i,row in enumerate(rows):
        f.parts.append(f'<text x="70" y="{100+i*42}" xml:space="preserve" font-family="Consolas,monospace" font-size="32">{escape(row)}</text>')
    f.text(415,130,'三层树，删除第 2 层',size=22);f.text(415,180,'从左数第 2 个结点',size=22)
    f.text(415,245,'整片右侧保留空格',GREEN,size=23);f.text(415,295,'不重新居中，不改尺寸',size=21)
    f.text(60,380,'画布仍是 6 行、11 列，所有空白都是普通空格',size=22)
    save('P1185',f,'字符画直接由叶子坐标独立生成器绘制；未出现的右子树不是缩进被裁剪，而是按要求留空。')

    f=Figure('五点链以中心为根，三个核心保留最高的三个点',410)
    p={3:(380,95),2:(235,205),4:(530,205),1:(85,310),5:(680,310)}
    tree(f,p,[(3,2),(3,4),(2,1),(4,5)],marked={2,3,4})
    for u,h in [(3,2),(2,1),(4,1),(1,0),(5,0)]:f.text(p[u][0],p[u][1]+48,'h='+str(h),GREEN if h else GRAY,size=21,anchor='middle')
    f.text(65,398,'高度降序 2、1、1、0、0；k=3，答案 0+1=1',size=22)
    save('P5536',f,'绿色核心保持连通，两端非核心城市到集合均为一；高度是向下的最大路长，不是离根深度。')

    f=Figure('移动元素 4 时换一个代表结点，旧的存储结点仍保留',440)
    p={1:(180,130),2:(90,255),7:(260,255),4:(550,130),6:(460,255),5:(650,255)}
    tree(f,p,[(1,2),(1,7),(4,6),(4,5)],marked={1,7})
    f.text(160,335,'pos[4]=7',GREEN,size=23);f.text(455,335,'pos[3]=6；pos[5]=5',size=21)
    f.text(65,390,'左集合 {1,2,4}：3、7',size=22);f.text(410,390,'右集合 {3,5}：2、8',size=22)
    f.text(65,428,'圆内是存储结点编号；旧结点 4 不再由 pos[4] 指向',size=21)
    save('UVA11987',f,'图只画原样例最后一次移动后的两个非空集合，空旧结点三未画；旧根四仍连着代表元素三、五的结点，不能把旧根直接移走。')

    f=Figure('起点不吃：两次往返一共吃四只',390)
    p={'s':(210,135),'v':(560,135)};tree(f,p,[('s','v')])
    f.text(210,195,'原有 2 只',size=22,anchor='middle');f.text(560,195,'原有 3 只',size=22,anchor='middle')
    f.row(['s','v','s','v','s'],240,x=145,width=92,colors={1:GREEN,2:GREEN,3:GREEN,4:GREEN})
    f.text(55,330,'只在到达时吃：s 吃 2 只，v 吃 2 只；最终回 s',size=22)
    f.text(55,375,'两个边对×2=4；不能在原地吃掉 v 剩余的一只',size=21)
    save('CF77C',f,'五格为连续位置，第一格只是出发位置；两端消耗均不超过容量，最多两次返回s。')

    f=Figure('长度四与长度二的链，连接中心后直径仍为四',400)
    p={1:(150,130),2:(250,130),3:(350,130),4:(450,130),5:(550,130),6:(250,270),7:(350,270),8:(450,270)}
    tree(f,p,[(1,2),(2,3),(3,4),(4,5),(6,7),(7,8),(3,7)],marked={3,7})
    f.text(430,205,'新路：中心 3 至中心 7',GREEN,size=21)
    f.text(55,350,'max(4,2,2+1+1)=4',GREEN,size=24)
    f.text(55,390,'询问中的城市只指定两块，允许另选连接端点',size=22)
    save('CF455C',f,'绿色道路连接两树的中心；若误按询问给定端点连接，两条链可变成长度七，违背最优合并。')

    f=Figure('只交换第一与第三位，未触及的第二位仍参与逆序',360)
    f.text(60,120,'原序列',size=22);f.row([1,2,3],85,x=235,width=120,colors={1:GRAY})
    f.text(60,220,'交换后',size=22);f.row([3,2,1],185,x=235,width=120,colors={0:GREEN,1:GRAY,2:GREEN})
    f.text(65,285,'触及端点之间：1 对；与中间未触及位置：2 对',size=22)
    f.text(65,335,'共 3 对；两端的坐标距离 2，排名距离 1',GREEN,size=23)
    save('CF540E',f,'灰格不曾被交换，数值仍为二；只给触及点离散化计逆序会少算两对。')

    f=Figure('核是一整段，支路只走到接入点就到达核',390)
    p={'A':(100,170),'C':(380,170),'B':(660,170),'v':(380,300)}
    tree(f,p,[('A','C'),('C','B'),('C','v')],marked={'A','C','B'})
    f.text(230,145,'4',size=23);f.text(520,145,'4',GREEN,size=23);f.text(405,245,'3',size=23)
    f.text(50,350,'核 A—B 长 8；v 到核为 (7+7-8)/2=3',size=22)
    f.text(50,385,'到最近端点为 7，到整段路径却只有 3',GREEN,size=23)
    save('P1099',f,'A至B是一条直径，允许长度八时选择完整A至B为核，偏心距为三。v接入核的内部C处，到两端都是七，到整段核只有三。')

    f=Figure('全部关键点的主干长八，支路只补两端接入路',390)
    p={2:(150,155),1:(385,155),3:(640,155),6:(150,295)}
    tree(f,p,[(2,1),(1,3),(2,6)],marked={2,1,3})
    for x,y,text in [(265,130,'3'),(510,130,'5'),(175,235,'1')]:f.text(x,y,text,size=23)
    f.text(360,235,'关键点：2、3；主干 W=8',GREEN,size=22)
    f.text(360,295,'s=t=6，接入点都为 2',size=22)
    f.text(55,365,'答案 2×8+1+1-0=18',GREEN,size=24)
    save('P9433',f,'取自原样例的必要局部结构，六号不是关键点；起终点相同也必须走完主干收集全部关键点。')

    f=Figure('连续极角块对应互不重叠的几何扇区',480)
    coords={1:(0,0),2:(2,3),4:(4,5),3:(-2,2),5:(-3,5)}
    p={u:(310+55*x,410-55*y) for u,(x,y) in coords.items()}
    for group,color in [([1,2,4],'#e1f3eb'),([1,3,5],'#e4eef9')]:
        f.parts.append('<polygon points="'+' '.join(f'{p[u][0]},{p[u][1]}' for u in group)+f'" fill="{color}"/>')
    tree(f,p,[(1,2),(2,4),(1,3),(3,5)],marked={1,2,4})
    point_id={1:1,3:2,5:3,2:4,4:5}
    for u,(x,y) in p.items():f.text(x+30,y+8,'点'+str(point_id[u]),GRAY,size=19)
    f.text(435,335,'圆内是树编号',size=21);f.text(435,375,'小字是平面点编号',size=21)
    f.text(50,465,'每个孩子获得与子树大小相同的连续角度点块',size=22)
    save('CF196C',f,'点坐标按同一比例绘制，无三点共线。答案按平面点顺序是一、三、五、二、四，不能输出其逆映射。')

    f=Figure('同一棵博弈树，分别安排叶子使结果最大与最小',430)
    for offset,leaf,caption in [(0,[3,1,2],'最大结果 3'),(380,[1,2,3],'最小结果 2')]:
        p={'root':(190+offset,100),'a':(80+offset,245),'b':(270+offset,205),'c':(215+offset,315),'d':(325+offset,315)}
        for u,v in [('root','a'),('root','b'),('b','c'),('b','d')]:f.line(*p[u],*p[v],GRAY)
        f.box(150+offset,80,80,40,'MAX',BLUE);f.box(230+offset,185,80,40,'MIN',RED)
        for u,value in zip(['a','c','d'],leaf):f.circle(*p[u],value,GREEN)
        f.text(190+offset,390,caption,GREEN,size=25,anchor='middle')
    save('CF538E',f,'左侧为max(3,min(1,2))，右侧为max(1,min(2,3))；两幅是不同排列，不把一次固定赋值当作全部优化。')

    f=Figure('长度一、二、二：折去一条二，剩三边路径',420)
    p={'c':(220,270),'a':(130,270),'b':(220,190),'d':(220,110),'e':(310,270),'f':(400,270)}
    f.line(*p['c'],*p['e'],RED,dash=True,width=4);f.line(*p['e'],*p['f'],RED,dash=True,width=4)
    tree(f,p,[('c','a'),('c','b'),('b','d')],marked={'a','c','b','d'})
    for u in ['e','f']:f.circle(*p[u],u,RED)
    f.text(470,145,'两条长 2 的叶端臂',size=22);f.text(470,210,'可以合并一条',RED,size=22)
    f.text(470,285,'保留路径长 1+2=3',GREEN,size=22)
    f.text(55,390,'三为奇数，没有结点能分成两条等长臂，不能再折',size=21)
    save('CF765E',f,'红虚线是被合并掉的整条两边叶端路径；绿色三边路径已经达到本例最短长度。')

    f=Figure('保留六、五以后，只剩一个名额，四号需要两个',435)
    p={6:(380,90),2:(235,205),5:(565,205),1:(90,335),3:(245,335),4:(400,335)}
    tree(f,p,[(6,2),(6,5),(2,1),(2,3),(2,4)],marked={6,5})
    f.text(485,280,'四号需要补 4、2 两点',size=20);f.text(485,330,'剩一格，跳过四号',RED,size=20)
    f.text(485,380,'之后可补二号',GREEN,size=22)
    f.text(55,425,'再补 2：保留 {2,5,6}；删除 {1,3,4}',size=22)
    save('CF980E',f,'该图是原样例，以最大编号六为根。不能只拿最大的三个编号，因为它们的连通路径还需要二号。')

    f=Figure('父子端点交错，兄弟区间包含而不交错',395)
    xs={i:100+(i-1)*80 for i in range(1,7)}
    for i,x in xs.items():f.text(x,85,i,GRAY,size=21,anchor='middle')
    for u,l,r,y,color in [(1,1,4,140,BLUE),(2,2,6,220,GREEN),(3,3,5,300,RED)]:
        f.text(30,y+7,'点'+str(u),size=21);f.line(xs[l],y,xs[r],y,color,width=5)
        for end in [l,r]:f.circle(xs[end],y,'',color,radius=8)
    for y,text in [(145,'1—2 严格交错'),(220,'1—3 严格交错'),(295,'2 包含 3，无边')]:f.text(550,y,text,size=21)
    f.text(55,375,'左端点 1、2、3 先分配；右端点依次为 4、5、6',size=22)
    save('CF1278E',f,'根区间[1,4]，两个孩子为[2,6]与[3,5]；两个孩子的右端点按左端点的逆序产生。')

    for spec in specs:
        if spec.pid not in pictures:continue
        key,data,caption,old=pictures[spec.pid];spec.images.update(old);spec.images[key]=data
        figure='\n\n!['+caption+']('+key+')\n\n'
        spec.brief=figure+spec.brief;spec.detail=figure+spec.detail
