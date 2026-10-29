"""Actual cells, point pairs, prefix intervals and contribution rectangles."""
import base64
from editorial_figures import Figure,BLUE,RED,GREEN,GRAY
from core7_authoring import OUT

def attach_figures(specs):
    figures={};history={}
    def save(pid,f,caption,filename=None):
        filename=filename or pid
        path=f.save(filename,OUT/'figures');key='assets/core7/'+filename+'.svg'
        if pid in figures:
            old_key,old_data,_=figures[pid];history.setdefault(pid,{})[old_key]=old_data
        figures[pid]=(key,'data:image/svg+xml;base64,'+base64.b64encode(path.read_bytes()).decode(),caption)

    f=Figure('当前坐标 5：左边距离 4+2，右边距离 1',300)
    f.line(90,140,675,140,GRAY)
    for value,x in [(1,110),(3,300),(5,490),(6,585)]:
        f.circle(x,140,value,RED if value==5 else BLUE);f.text(x,195,'当前' if value==5 else '此前',size=18,anchor='middle')
    f.text(60,245,'左组：2×5−(1+3)=6；右组：6−5=1',size=22)
    f.text(60,280,'距离共 7；当前听力 4，贡献 28',GREEN,size=22)
    save('P2345',f,'点是一条数轴上的奶牛位置，当前听力不小于此前三头；左右距离按同一坐标方向相减。')

    f=Figure('马在 (2,2)：红叉是禁行点，不是一整片区域',455)
    for x in range(5):
        for y in range(5):
            px,py=160+x*90,95+y*65
            f.circle(px,py,'×' if (x==2 and y==2) or abs(x-2)*abs(y-2)==2 else '·',
                     RED if (x==2 and y==2) or abs(x-2)*abs(y-2)==2 else GRAY,radius=17)
    f.text(90,105,'y=0',size=17);f.text(90,365,'y=4',size=17)
    f.text(160,404,'x=0',size=18,anchor='middle');f.text(520,404,'x=4',size=18,anchor='middle')
    f.text(55,445,'起点 (0,0) 的右侧与下侧都被控制，路径数为零',size=21)
    save('P1002',f,'坐标 x 向右、y 向下；红叉包括马所在点及八个日字终点，原点自身未禁行但无路可出。')

    f=Figure('元素 1 弹出之前与之后：两段各自完成栈操作',310)
    f.box(40,100,250,65,'先出：2 … k+1',BLUE)
    f.box(315,100,90,65,'1',RED)
    f.box(430,100,290,65,'后出：k+2 … n',GREEN)
    f.text(165,215,'k 个数，f[k] 种',BLUE,anchor='middle')
    f.text(575,215,'n−1−k 个数',GREEN,anchor='middle')
    f.text(90,280,'固定 k 时两侧独立配对；不同 k 由 1 的位置区分',size=21)
    save('P1044',f,'方框区分输出阶段，内部可有不同合法顺序；它不是强迫这些数字按升序出栈。')

    f=Figure('跨中线的近点对，只需看两侧窄条',405)
    f.box(180,80,160,250,'',BLUE,fill='#eef5ff');f.box(340,80,160,250,'',GREEN,fill='#eff9f1')
    f.line(340,65,340,340,RED,dash=True)
    points=[(280,260,'A'),(390,275,'B'),(210,100,'C'),(455,95,'D'),(90,210,'E'),(640,160,'F')]
    for x,y,label in points:f.circle(x,y,label,GRAY if label in ['E','F'] else BLUE,radius=17)
    f.line(280,260,390,275,RED);f.text(340,365,'中线左右各宽 δ，只检查纵距也小于 δ 的点',size=20,anchor='middle')
    f.text(45,397,'两侧内部最短距均 ≥δ；小格装点的上界来自这个前提',size=20)
    save('P1257',f,'蓝绿区域构成宽二倍 δ 的窄条；E、F 与中线已太远，不可能属于更近的跨组点对。')

    f=Figure('四乘四棋盘：先盖中心三格，四个象限各缺一格',425)
    for row in range(4):
        for column in range(4):
            label='公主' if (row,column)==(0,0) else '中' if (row,column) in [(1,2),(2,1),(2,2)] else ''
            f.box(190+column*65,75+row*65,62,62,label,RED if label=='公主' else GREEN if label=='中' else GRAY,
                  fill='#ffeef0' if label=='公主' else '#e4f5eb' if label=='中' else '#fff',size=19)
    f.line(318,70,318,338,BLUE,width=4);f.line(185,203,452,203,BLUE,width=4)
    f.text(75,375,'中心毯：拐角 (3,3)，方向 1（向上、向左）',size=22)
    f.text(75,411,'绿色格对子棋盘成为人工缺格，递归时不能再覆盖',size=21)
    save('P1228',f,'公主在左上象限；中心毯覆盖 (2,3)、(3,2)、(3,3)，同一个绿色 L 不覆盖左上中心格。')

    f=Figure('合并 [2,4,5] 与 [1,3,6]：右值 1 一次匹配三项',330)
    f.row([2,4,5],85,x=130,width=110);f.row([1,3,6],210,x=130,width=110,colors={0:RED})
    for i in range(3):f.line(183+i*110,135,183,207,RED,width=2)
    f.text(515,125,'1 < 2 ≤ 4 ≤ 5',RED,size=22,anchor='middle')
    f.text(515,250,'本次增加 3 对',RED,size=22,anchor='middle')
    f.text(80,315,'左半原下标都较小；归并排序不改变左右所属半段',size=21)
    save('P1908',f,'红线表示三个不同下标对，不表示交换操作；后续右值三还会匹配四、五。')
    # Preserve the first illustration while giving the right-side labels room.
    f.parts=[part.replace('x="515"','x="625"') for part in f.parts]
    save('P1908',f,'红线表示三个不同下标对，不表示交换操作；后续右值三还会匹配四、五。',filename='P1908-readable')

    f=Figure('AC[2[3B]]：先展开内层，再复制外层',370)
    f.box(205,70,350,55,'AC + [2 [3 B]]',BLUE)
    f.box(45,180,260,55,'内层返回 BBB',GREEN)
    f.box(405,180,310,55,'外层复制为 BBBBBB',RED)
    f.line(260,125,175,180,BLUE);f.line(305,207,405,207,GREEN)
    f.box(185,285,390,55,'最终 ACBBBBBB',BLUE)
    f.line(560,235,440,285,RED)
    save('P1928',f,'每个括号层返回完整展开的片段，次数属于当前左括号，不能在嵌套时混用。')

    f=Figure('排列 [3,1,4,2,5]：数 2 负责的端点组合',435)
    f.row([3,1,4,2,5],75,x=120,width=110,colors={1:RED,3:GREEN})
    for i in range(5):f.text(173+i*110,150,i+1,size=18,anchor='middle')
    for y,l,r in [(205,3,4),(250,3,5),(295,4,4),(340,4,5)]:
        f.line(173+(l-1)*110,y,173+(r-1)*110,y,GREEN,width=6)
        f.circle(173+(l-1)*110,y,'',GREEN,radius=5);f.circle(173+(r-1)*110,y,'',GREEN,radius=5)
        f.text(45,y+7,f'[{l},{r}]',size=18)
    f.text(55,405,'L=2，R=6：左端点 3、4；右端点 4、5，共 2×2=4 段',size=20)
    save('AT_agc005_b',f,'红色一是左边第一个更小值；右侧没有更小值，用六作边界。四条实线画出数二负责的全部区间。')

    f=Figure('JOI：两种计数差回到原状态，整段三种数量相同',340)
    f.row(['J','O','I'],90,x=220,width=115)
    states=['(0,0)','(1,1)','(0,1)','(0,0)']
    for i,state in enumerate(states):f.text(210+i*115,190,state,GREEN if i in [0,3] else BLUE,size=20,anchor='middle')
    f.line(210,230,555,230,GREEN,width=5)
    f.text(380,285,'两端前缀的 (J−O,J−I) 相同',GREEN,size=23,anchor='middle')
    f.text(60,328,'状态写在字符边界；区间从左边界之后到右边界为止',size=21)
    save('AT_joisc2014_h',f,'四个前缀状态对应零、一、二、三个字符，不是每个字符自身的状态。')

    f=Figure('前缀 [0,−1,−1,0]：后一个零贡献三段',355)
    f.row([1,2,3],75,x=255,width=115)
    for i,value in enumerate([0,-1,-1,0]):f.circle(245+i*115,200,value,RED if i==3 else BLUE)
    for i in range(3):f.line(245+i*115,235,590,280+i*15,GREEN,width=2)
    f.text(40,210,'前缀和值',size=20)
    f.text(50,342,'k=2；三个此前前缀都 ≤ 当前零，对应 [1,3]、[2,3]、[3,3]',size=20)
    save('P2717',f,'圆点是字符间的前缀边界；中间两个负一位置不同，要作为两个左边界分别计数。')

    f=Figure('喷泉：1→2→5，等直径或更小盘直接跳过',445)
    for i,(diameter,capacity) in enumerate([(4,10),(6,8),(3,5),(4,14),(10,9)],1):
        y=70+i*55;left=275-diameter*8;right=275+diameter*8
        f.line(left,y,right,y,BLUE,width=6);f.text(75,y+7,f'盘 {i}',size=20)
        f.text(390,y+7,f'直径 {diameter}，容量 {capacity}',size=20)
    f.line(180,130,165,180,RED);f.line(165,185,165,340,RED)
    f.text(535,383,'倒入 25：10+8 后剩 7，停盘 5',GREEN,size=19,anchor='middle')
    f.text(75,425,'若只倒入 18，恰好填满盘 2，答案是 2，不能再跳',size=21)
    save('P7167',f,'水平线段长度按直径绘制；盘三、四都比盘二小，溢流不经过它们，容量也不能被扣除。')

    f=Figure('右端加入 3：旧后缀两段合成同一 GCD 组',355)
    f.row([2,2,3],75,x=200,width=115,colors={2:RED})
    for y,l,label in [(190,2,'[3]：GCD 3'),(240,1,'[2,3]：GCD 1'),(290,0,'[2,2,3]：GCD 1')]:
        f.line(255+l*115,y,485,y,GREEN if l<2 else RED,width=6);f.circle(255+l*115,y,'',GREEN if l<2 else RED,radius=5)
        f.text(555,y+7,label,size=18,anchor='middle')
    f.text(95,345,'分组为 (3,1)、(1,2)，本轮贡献 3×1+1×2=5',size=22)
    save('SP32079',f,'三条线是三个真实后缀，其中两个不同区间共享 GCD 一，数量合并但区间不能去重。')

    f=Figure('11010111：前缀 1 与前缀 5 同为一',310)
    f.row(list('11010111'),75,x=85,width=78,colors={1:GREEN,2:GREEN,3:GREEN,4:GREEN})
    for i,value in enumerate([0,1,2,1,2,1,2,3,4]):f.text(80+i*78,170,value,RED if i in [1,5] else GRAY,size=18,anchor='middle')
    f.line(158,215,470,215,GREEN,width=6)
    f.text(380,270,'字符 2 到 5 为 1010，长度 5−1=4',size=22,anchor='middle')
    save('CF873B',f,'数字写在字符边界，绿色线两端相同前缀和，区间不包括左边界前缀中的字符。')

    f=Figure('二级图腾：一个上方、两个下方的一级图形',315)
    for x,y in [(310,75),(230,155),(390,155)]:
        f.line(x,y,x-80,y+80,BLUE);f.line(x,y,x+80,y+80,BLUE);f.line(x-80,y+80,x+80,y+80,BLUE)
    f.text(310,280,'中心朝下的空洞保持为空格',size=22,anchor='middle')
    save('P1498',f,'示意的三角形是三个一级图腾占据的区域；真正输出用斜线与下划线构成，空洞不能填满。')

    f=Figure('当前值 3：此前四项中严格大于它的有三项',310)
    f.row([5,4,2,6],80,x=110,width=110,colors={2:GRAY})
    f.box(590,80,100,48,'3',RED)
    for i in [0,1,3]:f.line(163+i*110,145,640,210,GREEN,width=2)
    f.text(85,265,'此前共 4 项，≤3 的只有 2：严格大于者 4−1=3',size=21)
    save('P1908-fenwick',f,'绿线是与当前三构成逆序对的此前元素；灰色二属于查询的“不大于三”集合，应被扣除。')

    for spec in specs:
        if spec.pid not in figures:continue
        figure_id='P1908-fenwick' if spec.pid=='P1908' and spec.key=='fenwick' else spec.pid
        key,data,caption=figures[figure_id];spec.images[key]=data
        spec.images.update(history.get(figure_id,{}))
        block='\n\n!['+caption+']('+key+')\n\n'+caption
        # Put the exact object immediately after the first concrete paragraph.
        head,separator,tail=spec.detail.partition('\n\n');spec.detail=head+block+(separator+tail if separator else '')
        spec.brief+=block
