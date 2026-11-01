"""Real merge histories, tree visits, directions and operation identities."""
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
    from core7_cases_interval import merge_orders,game_tree,deletion_orders,expression_trees,choir_permutations,cave_colorings,ice_plays

    f=Figure('两端不同，给另一端补一个镜像字符',335)
    f.row(['a','b'],90,x=210,width=160)
    f.row(['a','b','a'],205,x=130,width=160,colors={2:GREEN})
    f.text(65,315,'新补右端 a，得到 aba；也可在左边补 b 得到 bab',size=22)
    save('P1435',f,'上排原串ab，下排绿色a为唯一插入字符，原来的a和b先后顺序没有改变。')

    assert merge_orders([2,5,3,1])[0]==22
    f=Figure('最后两堆的质量和固定，前面费用还要累计',465)
    for y,values,cost in [(85,[2,5,3,1],''),(180,[2,5,4],'本次费用 4'),(275,[7,4],'本次费用 7'),(370,[11],'本次费用 11')]:
        f.row(values,y,x=85,width=115);f.text(570,y+32,cost,GREEN,size=22,anchor='middle')
    f.text(65,450,'总费用 4+7+11=22；最终质量 11 不是答案',size=23)
    save('P1775',f,'先合并相邻的三与一，再合并二与五，最后合并七与四，所有中间堆仍保持原次序。')

    assert game_tree([8,15,3,7])==(22,11)
    f=Figure('眼前选八会输，先取七能拿二十二分',365)
    f.row([8,15,3,7],100,x=75,width=150,colors={1:GREEN,3:GREEN})
    f.text(65,235,'先取 7：最终先手 22，后手 11',GREEN,size=24)
    f.text(65,295,'先取 8：最佳也只有 15，对手得到 18',RED,size=24)
    f.text(65,345,'两条路线的总分都为 33，比较的是各自最终所得',size=21)
    save('P2734',f,'首轮可以取八或七；绿色的七与十五最终归先手，对手无论怎样回应都能保证二十二分。')

    assert deletion_orders([1,2,3])==7
    f=Figure('删中间得到两侧之和，新的邻居随后改变',440)
    for y,values,note in [(90,[1,2,3],'删 2，得 1+3=4'),(200,[1,3],'删 1，得 0+3=3'),(310,[3],'删 3，得 0')]:
        f.row(values,y,x=105,width=125);f.text(510,y+32,note,GREEN,size=20)
    f.text(65,420,'总分 7；不加被删元素自身，边界不存在时为零',size=23)
    save('P17015',f,'每一排都是删除发生前的真实剩余数组，第二步的一与三已经相邻。')

    f=Figure('四颗珠对应五个边界，接缝决定额外能量',410)
    for i in range(4):f.line(100+i*140,130,240+i*140,130,GREEN,width=4)
    for i,value in enumerate([10,2,3,5,10]):f.circle(100+i*140,130,value,BLUE)
    f.text(65,230,'先合 10→2 与 2→3：10×2×3=60',size=23)
    f.text(65,290,'再接 3→5：150；最后接 5→10：500',size=23)
    f.text(65,365,'以第 4 颗珠为断口起点，总能量 60+150+500=710',GREEN,size=22)
    save('P1063',f,'对应原样例头标记二三五十，窗口从第四颗开始，圆是头尾边界，四条边才是四颗珠。')

    assert expression_trees([1,2,3,4,5],2)==120
    f=Figure('括号把前三项先相加，恰好再用两个乘号',375)
    f.row([1,2,3,4,5],95,x=65,width=125,colors={3:GREEN,4:GREEN})
    f.line(80,195,425,195,BLUE,width=4)
    f.text(250,245,'先加成 6',BLUE,size=24,anchor='middle')
    f.text(65,325,'(1+2+3) × 4 × 5 = 120',GREEN,size=28)
    f.text(65,365,'所有相邻间隔都有运算，原数字顺序不变',size=22)
    save('P1388',f,'前三个数字用两个加号，后面两个间隔用乘号，满足五数字、两个乘号的原样例。')

    assert merge_orders([4,5,9,4],True)==(43,54)
    f=Figure('末尾四与开头四相邻，合并不能固定断口',525)
    positions=[(380,100),(555,225),(380,350),(205,225)]
    for i in range(4):f.line(*positions[i],*positions[(i+1)%4],GREEN if i==3 else BLUE,width=4)
    for p,value in zip(positions,[4,5,9,4]):f.circle(*p,value,BLUE)
    f.text(65,420,'最小：先跨首尾合成 8，再成 13、22，总费 43',GREEN,size=22)
    f.text(65,485,'最大：依次合成 14、18、22，总费 54',size=23)
    save('P1880',f,'四个圆依原顺时针顺序为四五九四，绿色边明确连起原序列首尾，两条费用历史都能实际执行。')

    assert choir_permutations(3)[(0,1,2)]==4
    f=Figure('用一二三代表相对身高，这四种初始排列都可行',455)
    for i,values in enumerate([[1,2,3],[2,1,3],[2,3,1],[3,2,1]]):
        f.row(values,75+85*i,x=95,width=120);f.text(590,105+85*i,'→ 1、2、3',GREEN,size=24,anchor='middle')
    f.text(65,435,'每步与刚入队者比较：更矮放左，更高放右',size=22)
    save('P3205',f,'展示三人的全部四种可行初始排列，相对身高一二三可以对应任意三个严格递增的合法身高值。')

    f=Figure('同一对子字母可有多个父来源，都要保留',420)
    points=[(380,90),(220,210),(540,210),(140,315),(300,315),(460,315),(620,315)]
    for u,v in [(0,1),(0,2),(1,3),(1,4),(2,5),(2,6)]:f.line(*points[u],*points[v],BLUE,width=3)
    f.text(380,80,'I 或 N',GREEN,size=25,anchor='middle')
    for p in points[1:3]:f.circle(*p,'W',BLUE)
    for p in points[3:]:f.circle(*p,'I',GRAY)
    f.text(65,395,'W→II；I→WW、N→WW，所以 IIII 的来源为 IN',size=22)
    save('P4290',f,'根有I或N两种选择，两个W分别生成两个I；字母的左右先后和原串完全一致。')

    f=Figure('两数相邻得分有方向，零的零次方另作规定',350)
    f.row([2,3],90,x=180,width=190)
    f.text(65,235,'先取左端：2 的 3 次方 = 8',size=24)
    f.text(65,295,'先取右端：3 的 2 次方 = 9，更优',GREEN,size=24)
    f.text(65,340,'第一项本身没有得分；0 的 0 次方按题意为 0',size=21)
    save('P10236',f,'两个数只有两种不同的取数结果，交换前后会改变指数和底数，不能把得分表当无向关系。')

    f=Figure('释放者不用付，当前同段其余七人都要贿赂',355)
    f.row(list(range(1,9)),100,x=55,width=80,colors={i:GREEN if i==2 else RED for i in range(8)})
    f.text(65,240,'共 8 间牢房，先释放第 3 人；其它 7 人都听到',size=23)
    f.text(65,305,'边界为 0、9：本次费用 9−0−2=7',GREEN,size=25)
    save('P13439',f,'格子数字是牢房编号，绿色三号释放后为空；被贿赂的七人不要求也在释放名单中。')

    assert cave_colorings('AAAAA')==2
    f=Figure('五次进入均记 A，可以来自两种三节点有序树',440)
    for u,v in [((180,90),(180,205)),((180,205),(180,320)),((540,90),(450,205)),((540,90),(630,205))]:f.line(*u,*v,BLUE,width=4)
    for p in [(180,90),(180,205),(180,320),(540,90),(450,205),(630,205)]:f.circle(*p,'A',BLUE)
    f.text(180,385,'链：下、下、回、回',size=22,anchor='middle')
    f.text(540,385,'两孩子：下回、下回',size=22,anchor='middle')
    f.text(65,430,'两种记录都为 AAAAA；每次回到父洞也会记颜色',size=22)
    save('UVA1362',f,'外部入口在最上方根处，链与两孩子星形各有三个洞穴、五次颜色记录，说明回访颜色不可丢掉。')

    f=Figure('第一刀切四，左右两段再各切一次',385)
    f.line(65,140,695,140,BLUE,width=7)
    for value in [0,2,4,7,10]:
        x=65+63*value;f.line(x,112,x,167,GREEN if value==4 else GRAY,width=4);f.text(x,215,value,GRAY,size=23,anchor='middle')
    f.text(65,290,'先切 4：10 + 4 + 6 = 20',GREEN,size=25)
    f.text(65,350,'若先切 2：10 + 8 + 6 = 24',RED,size=25)
    save('UVA10003',f,'线段按零到十真实比例绘制，切口为二、四、七，绿色四为第一刀，之后左段长四、右段长六。')

    f=Figure('两台机器人连续工作三秒，收八枚、花三枚',480)
    for y,label,values in [(85,'秒数',[1,2,3]),(180,'经过道路',[1,2,2]),(275,'收集金币',[1,3,4]),(370,'本秒购价',[1,0,2])]:
        f.text(35,y+32,label,size=22);f.row(values,y,x=220,width=155,colors={0:BLUE,1:BLUE,2:GREEN})
    f.text(65,460,'前两秒第一台，末秒新买第二台；净收益 1+3+4−1−2=5',size=21)
    save('P1070',f,'对应原样例两厂、三秒、寿命最多二秒；第一台从一厂走一二号路，末秒在二厂新买，不能把第三秒闲置。')

    f=Figure('四个零有四种下标三元组，两端固定后中间有两选',390)
    f.row([0,0,0,0],95,x=95,width=140,colors={0:GREEN,1:BLUE,2:BLUE,3:GREEN})
    for i in range(4):f.text(165+i*140,220,'下标 '+str(i+1),GRAY,size=22,anchor='middle')
    f.text(65,290,'固定两端 1、4：中间可选 2 或 3，新增 2 组',size=23)
    f.text(65,355,'整段计数 = 左三格 1 + 右三格 1 − 交集 0 + 两端 2 = 4',size=20)
    save('P6006',f,'四个数值相同但下标不同；包含首尾下标的一二四与一三四，另加一二三、二三四，共四组。')

    assert ice_plays([3,2,4,1],1)==25
    f=Figure('先吃指定的第二个，再沿已吃区间两侧扩展',475)
    f.text(55,85,'初始美味度',size=22);f.row([3,2,4,1],105,x=95,width=140,colors={1:GREEN})
    f.text(55,235,'可行吃法的原下标',size=22);f.row([2,3,4,1],255,x=95,width=140)
    f.text(65,385,'得分：1×2 + 2×4 + 3×1 + 4×3 = 25',GREEN,size=24)
    f.text(65,450,'首口后已吃段从 [2,2] 扩为 [2,3]、[2,4]、[1,4]',size=21)
    save('P7129',f,'对应原样例第一关的四个冰淇淋，次序二三四一满足每次只能吃已吃区间两侧的要求，乘数按时间增长。')

    f=Figure('插入两个闭括号，保留原字符的先后次序',365)
    f.row(['(',')','[','(',')',']'],100,x=65,width=105,colors={0:BLUE,1:GREEN,2:BLUE,3:BLUE,4:GREEN,5:BLUE})
    f.text(65,245,'原串是 ( [ ( ]；蓝色是原字符，绿色为新插入',size=23)
    f.text(65,310,'得到 ()[()]，总长 6，圆括号与方括号各自正确配对',size=22)
    save('UVA1626',f,'六格中新增的是第二与第五格闭圆括号，原四字符按顺序完整出现，结果是一个圆括号对拼接一组方括号。')

    f=Figure('第一次放首与放尾不同，即使结果同为一个 a',355)
    f.line(380,90,200,225,BLUE,width=4);f.line(380,90,560,225,GREEN,width=4)
    f.circle(380,90,'空',GRAY);f.circle(200,225,'a',BLUE);f.circle(560,225,'a',GREEN)
    f.text(175,145,'放首',BLUE,size=23,anchor='middle');f.text(585,145,'放尾',GREEN,size=23,anchor='middle')
    f.text(65,325,'S=a、T=a，答案为 2，不能按不同结果字符串去重',size=22)
    save('CF1336C',f,'两条边表示两种不同的第一次操作，结果都满足前缀a，因此单字符状态初始化为二。')

    for spec in specs:
        if spec.pid not in pictures:continue
        key,data,caption,old=pictures[spec.pid];spec.images.update(old);spec.images[key]=data
        figure='\n\n!['+caption+']('+key+')\n\n';spec.brief=figure+spec.brief;spec.detail=figure+spec.detail
