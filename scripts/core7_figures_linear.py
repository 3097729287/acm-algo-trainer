"""Concrete choices, time lines, board cuts and resource-state examples."""
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
    def bubbles(f,values,y,x=180,step=110,color=BLUE):
        for i,v in enumerate(values):f.circle(x+i*step,y,v,color)
    from core7_cases_linear import flower_counts,necklace,coin_combinations,coin_bfs,escape_states,board_peel_plans

    assert flower_counts([3,2],4)==2
    f=Figure('花种顺序已固定，选定每种数量就唯一确定摆法',325)
    f.row(['A','A','B','B'],100,x=190,width=110,colors={2:GREEN,3:GREEN})
    f.row(['A','A','A','B'],200,x=190,width=110,colors={3:GREEN})
    f.text(50,135,'2 盆 A',size=22);f.text(50,235,'3 盆 A',size=22)
    f.text(65,305,'A 至多 3 盆，B 至多 2 盆，共 4 盆：只有这 2 种',size=22)
    save('P1077',f,'两排分别表示数量二加二、三加一；不再把同种花交换位置当作新方案。')

    assert necklace('rrwwbbrb')==6
    f=Figure('白珠等遇到真颜色后再定色，两端不能重复拿',345)
    f.text(55,95,'原圈顺序：r r w w b b r b；剪在第 4 与第 5 颗之间',size=21)
    f.row(list('bbrbrrww'),145,x=55,width=82,colors={0:BLUE,1:BLUE,2:GRAY,3:GRAY,4:RED,5:RED,6:RED,7:RED})
    f.text(65,245,'左端取 2 颗蓝',BLUE,size=22);f.text(390,245,'右端取 4 颗红，白珠当红',RED,size=22)
    f.text(65,315,'共 6 颗；中间 r、b 两颗未取，整圈总数仍为 8',GREEN,size=22)
    save('P1203',f,'剪开后八颗珠的原次序完整保留，两端从外向内收集；白珠归入右端红色，未被两次计入。')

    assert coin_combinations([1,2],3)==2
    f=Figure('一元与二元凑三元，按数量组合只计两种',335)
    bubbles(f,[1,1,1],125,color=BLUE);bubbles(f,[1,2],230,color=GREEN)
    f.text(555,135,'3 张一元',size=22);f.text(445,240,'1 张一元、1 张二元',size=22)
    f.text(65,310,'1+2 与 2+1 是同一组；面额应在外层处理',size=22)
    save('P2834',f,'每个圆是一张纸币，两行是两种真正不同的数量组合，不按取出先后区分。')

    assert coin_bfs([1,3,4],6)==2
    f=Figure('一、三、四元凑六元，先拿大面额会多用一张',345)
    bubbles(f,[4,1,1],120,color=RED);bubbles(f,[3,3],230,color=GREEN)
    f.text(530,130,'三张',RED,size=23);f.text(420,240,'两张，最优',GREEN,size=23)
    f.text(65,315,'比较最后一张后的剩余金额，不按面额贪心',size=22)
    save('P2842',f,'两种方案金额都是六，目标是张数而非金额之和；完整枚举所有面额才得到两个三的方案。')

    assert escape_states(39,200,4)=='No\n197\n'
    f=Figure('纯法术与完整最优分开记，不能混用其魔法值',515)
    for y,label,values in [(90,'秒数',[1,2,3,4]),(175,'纯法术动作',['闪','闪','闪','休']),
                           (260,'纯法术魔法',[29,19,9,13]),(345,'纯法术路程',[60,120,180,180]),(430,'完整最优路程',[60,120,180,197])]:
        f.text(35,y+31,label,size=21);f.row(values,y,x=225,width=115,colors={3:GREEN} if y==430 else None)
    f.text(55,505,'197 的方案末秒跑步，末尾魔法是 9；纯法术末尾才是 13',size=21)
    save('P1095',f,'初始魔法三十九。纯法术第四秒休息，完整最优第四秒跑步，两条状态对应不同的实际方案。')

    f=Figure('短任务结束后可能被迫接新任务，局部短不等于空闲多',380)
    for i in range(8):f.text(155+i*66,90,i+1,GRAY,size=21,anchor='middle')
    f.text(35,160,'先接 3',size=21);f.row(['忙']*7+['闲'],125,x=125,width=66,colors={0:BLUE,1:BLUE,2:BLUE,3:RED,4:RED,5:RED,6:RED,7:GREEN})
    f.text(35,260,'先接 6',size=21);f.row(['忙']*6+['闲','闲'],225,x=125,width=66,colors={6:GREEN,7:GREEN})
    f.text(55,325,'任务：(1,3)、(1,6)、(4,4)；工作日共 8 分钟',size=21)
    f.text(55,365,'选 6 分钟任务错过第 4 分钟的新任务，最后空闲 2 分钟',GREEN,size=21)
    save('P1280',f,'第一排三分钟任务后必须接四分钟任务，只有最后一分钟闲；第二排忙时错过的任务由同事做。')

    f=Figure('最多一次三倍：不放大负根，把右下四分变十二分',355)
    p={'-2':(350,105),'-3':(170,245),'4':(540,245)}
    f.line(*p['-2'],*p['-3'],GRAY);f.line(*p['-2'],*p['4'],GREEN,width=5)
    for label,(x,y) in p.items():f.circle(x,y,label,GREEN if label=='4' else BLUE)
    f.text(585,250,'×3 → 12',GREEN,size=22);f.text(55,325,'沿右路：-2+12=10；三倍次数不是必须用满',size=22)
    save('P1544',f,'两层三角形根为负二、叶为负三和四，k为一；负数不能靠零初始化跳过，必须先经过根。')

    f=Figure('前导零可保留：303 拆成 3 与 03 只要一个加号',345)
    f.row([3,0,3],100,x=170,width=130);f.line(300,82,300,164,RED,width=4)
    f.text(300,210,'只在这个间隙插入 +',RED,size=22,anchor='middle')
    f.text(100,275,'3+03=6：1 个加号',GREEN,size=24);f.text(415,275,'3+0+3=6：2 个',size=22)
    f.text(65,325,'状态先记数字段数，最后减一才是加号数',size=22)
    save('P1874',f,'保留原三个字符，零属于后一段03，不单独切开；目标是六，最少两段、一个加号。')

    f=Figure('一秒只走一步，对角两格相距两步，不能连续打中',360)
    for x in [120,240,360]:f.line(x,90,x,330,GRAY)
    for y in [90,210,330]:f.line(120,y,360,y,GRAY)
    f.line(180,150,300,150,GREEN,width=4);f.line(300,150,300,270,GREEN,width=4)
    f.circle(180,150,'1',BLUE);f.circle(300,270,'2',RED)
    f.text(420,135,'圆内是出现时刻',size=21);f.text(420,205,'时间差 1 < 距离 2',RED,size=22)
    f.text(420,275,'初始位置任选，只打 1 只',GREEN,size=21)
    save('P2285',f,'蓝事件在一时刻的(1,1)，红事件在二时刻的(2,2)。绿色最短网格路线仍需两步。')

    f=Figure('ab 变成 ac，末字修改比删除后再插入便宜',390)
    values=[[0,1,2],[1,0,1],[2,1,1]]
    for j,label in enumerate(['空','a','ac']):f.text(240+j*115,90,label,size=22,anchor='middle')
    for i,label in enumerate(['空','a','ab']):
        f.text(100,150+i*75,label,size=22)
        f.row(values[i],120+i*75,x=185,width=115,colors={2:GREEN} if i==2 else None)
    f.text(570,165,'删：1+1=2',size=22);f.text(570,235,'插：1+1=2',size=22);f.text(570,305,'改：0+1=1',GREEN,size=22)
    f.text(55,375,'每格是两个前缀之间的最小编辑次数，空前缀也是状态',size=21)
    save('P2758',f,'表的行分别是空串、a、ab，列是空串、a、ac，三个最后操作的候选值完整显示。')

    f=Figure('每行的蓝段必须覆盖，绿色路线允许先走到另一端',470)
    p={(r,c):(140+120*c,115+120*r) for r in range(3) for c in range(3)}
    for r in range(3):
        for c in range(2):f.line(*p[r,c],*p[r,c+1],GRAY,width=1)
    for c in range(3):
        for r in range(2):f.line(*p[r,c],*p[r+1,c],GRAY,width=1)
    for r,l,h in [(0,0,2),(1,0,1),(2,1,2)]:f.line(*p[r,l],*p[r,h],BLUE,width=12)
    route=[(0,0),(0,1),(0,2),(1,2),(1,1),(1,0),(2,0),(2,1),(2,2)]
    for a,b in zip(route,route[1:]):f.line(*p[a],*p[b],GREEN,width=4)
    f.circle(*p[0,0],'S',GREEN);f.circle(*p[2,2],'T',GREEN)
    f.text(525,160,'三行段：',size=22);f.text(525,215,'[1,3]、[1,2]',size=21);f.text(525,270,'以及 [2,3]',size=21)
    f.text(525,340,'总共走 8 步',GREEN,size=24)
    f.text(55,445,'横走 2+2+2，下降 2；终点不是“最后一段走完”就结束',size=21)
    save('P3842',f,'真实三乘三网格中的八步路径，第二行在列三进入后先向左覆盖全段，再下降并走到终点。')

    f=Figure('全周只删一节：删第一天的末课最划算',370)
    f.text(40,130,'第一天',size=22);f.row([0,1,0,0,1],95,x=205,width=100,colors={1:GREEN,4:RED})
    f.text(40,235,'第二天',size=22);f.row([1,0,1,1,0],200,x=205,width=100)
    f.line(605,85,700,155,RED,width=3)
    f.text(65,305,'第一天保留第 2 小时：1 小时；第二天第 1 至 4 小时：4 小时',size=20)
    f.text(65,350,'总在校时间 1+4=5，恰好只缺一节',GREEN,size=24)
    save('CF946D',f,'原样例两天的完整课表，红格课程删除，零是无课小时但位于首末课之间时也计入在校时间。')

    f=Figure('剩余越少，当前轮次越晚，倍数反而越大',405)
    for y,row,label in [(95,[1,2,3],'第 1 轮：1×2=2'),(190,['·',2,3],'第 2 轮：2×4=8'),(285,['·','·',3],'第 3 轮：3×8=24')]:
        f.row(row,y,x=70,width=110);f.text(450,y+32,label,size=23)
    f.text(65,380,'按左、左、唯一数取：总分 34；两端取法需要比较',GREEN,size=22)
    save('P1005',f,'一行一、二、三的完整最优取数过程。已取位置留成点号，只说明位置，不再参与后续区间。')

    f=Figure('相等高度能继续拦截，后来的更高导弹需要另一套',340)
    f.row([3,3,4],95,x=190,width=120,colors={0:BLUE,1:BLUE,2:GREEN})
    f.line(250,160,370,160,BLUE,width=4);f.text(245,215,'系统一：[3,3]',BLUE,size=23)
    f.text(470,215,'系统二：[4]',GREEN,size=23)
    f.text(65,290,'一套最多 2 发；全部拦下至少 2 套',size=23)
    f.text(65,330,'第一问允许相等，第二问的上升下界必须严格',size=21)
    save('P1020',f,'三、三、四保持真实输入顺序，两发三可放在同一套，四号高度不能接在三之后。')

    f=Figure('第一刀两侧都继续切，原图明确不允许',440)
    for ox,allowed in [(70,True),(455,False)]:
        oy=100;cell=25
        for i in range(9):f.line(ox+i*cell,oy,ox+i*cell,oy+8*cell,GRAY,width=1);f.line(ox,oy+i*cell,ox+8*cell,oy+i*cell,GRAY,width=1)
        color=GREEN if allowed else RED
        f.line(ox+3*cell,oy,ox+3*cell,oy+8*cell,color,width=5)
        if allowed:
            for row in [2,4]:f.line(ox+3*cell,oy+row*cell,ox+8*cell,oy+row*cell,color,width=5)
        else:
            f.line(ox,oy+3*cell,ox+3*cell,oy+3*cell,color,width=5);f.line(ox+3*cell,oy+4*cell,ox+8*cell,oy+4*cell,color,width=5)
        for x,y in [(0,0),(0,7),(7,0),(7,7)]:f.text(ox+(x+.5)*cell,oy+(y+.5)*cell+7,'1',BLUE,size=20,anchor='middle')
        f.text(ox+100,350,'允许：平方和 6' if allowed else '不允许：虽算得 4',color,size=23,anchor='middle')
    f.text(50,405,'只有四角各一分，目标四块。每次只留一块继续切，另一块定案',size=21)
    save('P1436',f,'对应原题允许与禁止图的八乘八真实切线；左侧四块得分二、一、零、一，右侧四个一分区域违法。')

    f=Figure('用了相同张数会到同一位置，仍需比较已经得到的分',385)
    f.row([5,1,10,3],95,x=130,width=135,colors={0:GREEN,2:GREEN,3:GREEN})
    for i in range(4):f.text(195+i*135,175,'格 '+str(i+1),GRAY,size=20,anchor='middle')
    f.text(65,245,'先 1 再 2：5+1+3=9',size=23);f.text(65,305,'先 2 再 1：5+10+3=18',GREEN,size=23)
    f.text(65,365,'两种卡各用一张，都到第 4 格；状态保留 18 分',size=22)
    save('P1541',f,'四格分数与一张一步、一张两步卡，起点的五分两种方案都自动获得。')

    f=Figure('共享的一位可以改变，一、三、二是三项合法子序列',360)
    points=[(140,155),(380,155),(620,155)]
    f.line(*points[0],*points[1],GREEN,width=4);f.line(*points[1],*points[2],GREEN,width=4)
    for (x,y),v in zip(points,[1,3,2]):f.circle(x,y,v,GREEN)
    for (x,y),value in zip(points,['01','11','10']):f.text(x,235,value,BLUE,size=27,anchor='middle')
    f.text(260,115,'共享最低位',size=20,anchor='middle');f.text(500,115,'共享次低位',size=20,anchor='middle')
    f.text(65,315,'相邻按位与都非零，三个数一起按位与却为零',size=22)
    save('P4310',f,'两位二进制表示展示真实相邻关系，不能把最长答案误写成某一位的一的总次数。')

    f=Figure('先加一，再或二：最后六优于一直按位或的七',405)
    p={'root':(380,90),'left':(170,200),'right':(570,200),'seven':(170,320),'six':(475,320),'eight':(665,320)}
    for a,b,color in [('root','left',GRAY),('root','right',GREEN),('left','seven',GRAY),('right','six',GREEN),('right','eight',GRAY)]:f.line(*p[a],*p[b],color,width=4)
    for node,value in [('root',5),('left',5),('right',6),('seven',7),('six',6),('eight',8)]:f.circle(*p[node],value,GREEN if node in ['root','right','six'] else BLUE)
    for x,y,text,color in [(220,125,'或 1',GRAY),(545,125,'加 1',GREEN),(75,270,'或 2 或加 2',GRAY),(430,270,'或 2',GREEN),(665,270,'加 2',GRAY)]:f.text(x,y,text,color,size=20,anchor='middle')
    f.text(65,385,'初始 x=3、y=5，p 依次是 1、2；绿色路线最优',size=22)
    save('P17594',f,'完整展示两个操作位的所有不同结果分支，先做局部不变的按位或反而会错过最终六的最优解。')

    for spec in specs:
        if spec.pid not in pictures:continue
        key,data,caption,old=pictures[spec.pid];spec.images.update(old);spec.images[key]=data
        figure='\n\n!['+caption+']('+key+')\n\n';spec.brief=figure+spec.brief;spec.detail=figure+spec.detail
