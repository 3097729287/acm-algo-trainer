"""Concrete prefix boundaries, coverage cells and game actions for this unit."""
import base64
from editorial_figures import Figure,BLUE,RED,GREEN,GRAY
from core7_authoring import ROOT,OUT

def attach_figures(specs):
    figures={};history={}
    def save(pid,f,caption,filename=None):
        filename=filename or pid
        path=f.save(filename,OUT/'figures');key='assets/core7/'+filename+'.svg'
        if pid in figures:
            old_key,old_data,_=figures[pid];history.setdefault(pid,{})[old_key]=old_data
        figures[pid]=(key,'data:image/svg+xml;base64,'+base64.b64encode(path.read_bytes()).decode(),caption)

    f=Figure('二维差分：六个单位格，四个边界事件',430)
    for x in range(4):
        for y in range(5):f.box(150+y*85,65+x*65,82,62,'',GREEN if 1<=x<3 and 1<=y<4 else GRAY,
                               fill='#e7f6ef' if 1<=x<3 and 1<=y<4 else '#fff')
    for row,column,label,color in [(1,1,'+1',GREEN),(1,4,'−1',RED),(3,1,'−1',RED),(3,4,'+1',GREEN)]:
        f.circle(150+column*85,65+row*65,label,color,radius=24)
    f.text(70,365,'行 [1,3)，列 [1,4)：两行乘三列，共六格',size=22)
    f.text(70,408,'圆点是差分事件；绿色格才是最终覆盖的单元',size=22)
    f.save('rectangle-difference',ROOT/'docs/foundations/assets')

    f=Figure('模二前缀：每个余数三次，各配成三对',330)
    f.row([1,2,3,4,5],75,x=145,width=100)
    for i,v in enumerate([0,1,1,0,0,1]):f.circle(140+i*100,195,v,GREEN if v==0 else BLUE)
    f.text(85,275,'余数零：位置 0、3、4；余数一：位置 1、2、5',size=21)
    f.text(200,315,'总区间数 C(3,2)+C(3,2)=6',GREEN,size=23)
    save('P8649',f,'前缀状态位于元素之间；每对同余边界对应其间唯一的非空连续区间。')

    f=Figure('统一加三后，正值来自原排序数组的一个后缀',350)
    f.row([-7,-5,2,8,12],75,x=110,width=115)
    f.row([-4,-2,5,11,15],190,x=110,width=115,colors={0:GRAY,1:GRAY,2:GREEN,3:GREEN,4:GREEN})
    f.line(335,65,335,260,RED,dash=True)
    f.text(80,300,'原值 >−3 的后缀：2、8、12；实际和 5+11+15=31',size=21)
    f.text(80,337,'每项加同一偏移，排序次序不变',size=22)
    save('B3799',f,'上行原值保持不动，下行只用于展示真实值；红色虚线是 upper_bound 找到的正数后缀起点。')

    f=Figure('火烧赤壁：重叠长度只算一次',350)
    for y,l,r,color,label in [(100,-1,1,BLUE,'原段 1'),(165,2,9,GREEN,'原段 2'),(230,5,11,RED,'原段 3')]:
        f.text(35,y+7,label,color,size=18);f.line(170+(l+1)*40,y,170+(r+1)*40,y,color,width=9)
    for x in [-1,1,2,5,9,11]:f.text(170+(x+1)*40,282,x,size=18,anchor='middle')
    f.text(90,330,'并集为 [−1,1) 与 [2,11)，总长度 2+9=11',size=22)
    save('P1496',f,'同一数轴上画出原区间；绿色与红色的重叠部分不重复计入长度。')

    f=Figure('模七余数三：最早前缀 1 到前缀 6，长度五',330)
    f.row([3,5,1,6,2,14,10],75,x=70,width=92)
    for i,v in enumerate([0,3,1,2,1,3,3,6]):f.text(65+i*92,180,v,GREEN if i in [1,5,6] else GRAY,size=22,anchor='middle')
    f.line(157,230,617,230,GREEN,width=6)
    f.text(80,285,'选第 2 到 6 项：5+1+6+2+14=28',size=22)
    f.text(80,322,'余数三在前缀五重现时，仍不能覆盖最早位置一',size=21)
    save('P3131',f,'同余前缀位置一、五、六各自有含义，固定右端点六时选择最早的一才最长。')

    f=Figure('排列 [2,1,3,5,4]：边界 2、3、5 可切开',325)
    f.row([2,1,3,5,4],80,x=110,width=115,colors={2:GRAY})
    for i in [2,3]:f.line(110+i*115-2,65,110+i*115-2,200,RED,dash=True)
    for x,label in [(220,'费用 2'),(395,'已就位，0'),(565,'费用 2')]:f.text(x,235,label,size=21,anchor='middle')
    f.text(75,305,'三块分别排序；总费用四，整段排序反而要五',size=22)
    save('P7714',f,'切点前的最大值恰等于前缀长度；长度一的正确元素不用花费。')

    f=Figure('每升走四公里：两段各十公里只需五升',345)
    f.line(100,120,660,120,BLUE,width=7)
    for i,x in enumerate([100,380,660]):f.circle(x,120,i+1);f.text(x,180,['0 公里','10 公里','20 公里'][i],size=20,anchor='middle')
    f.text(240,245,'第一次需要 3 升',GREEN,size=23,anchor='middle')
    f.text(540,245,'累计需要 5 升',GREEN,size=23,anchor='middle')
    f.text(80,320,'第二段只新增两升；不能每段分别上取整买三升',size=21)
    save('P9749',f,'节点是实际可加油站；整数升按累计可行驶距离计数，多买的一部分里程可留给下一段。')

    f=Figure('各项可达区间：最大下界八，最小上界五',350)
    for y,l,r,label,color in [(110,2,5,'第一项',BLUE),(185,8,11,'第二项',RED),(260,3,9,'第三项',GREEN)]:
        f.text(40,y+7,label,color,size=20);f.line(170+l*40,y,170+r*40,y,color,width=7)
        f.circle(170+l*40,y,l,color,radius=16);f.circle(170+r*40,y,r,color,radius=16)
    f.line(370,75,370,285,GRAY,dash=True);f.line(490,75,490,285,GRAY,dash=True)
    f.text(90,330,'选值都放在 [5,8] 内，最小极差 8−5=3',size=23)
    save('P14028',f,'三条横线是各元素分别可选的整数区间；虚线圈定最终共同的取值带。')

    grid=[[0,-2,-7,0],[9,2,-6,2],[-4,1,-4,1],[-1,8,0,-2]]
    def rectangle_example(aligned):
        f=Figure('固定第 2 到 4 行，矩形和变成连续列和',405)
        for i,row in enumerate(grid):
            for j,x in enumerate(row):f.box(130+j*105,65+i*57,102,54,x,GREEN if i>=1 and j<2 else GRAY,
                                          fill='#e6f7ec' if i>=1 and j<2 else '#fff')
        f.text(25 if aligned else 50,330,'压成列和：',size=18 if aligned else 20)
        f.row([4,11,-10,1],300,x=130 if aligned else 180,width=105,colors={0:GREEN,1:GREEN})
        f.text(80,395,'第一、二列连续相加为十五，对应绿色的六格矩形',size=21)
        return f
    caption='每个压缩值是同一列在所选行带内的真实总和；不是把不相邻列任意挑选。'
    save('P1719',rectangle_example(False),caption)
    save('P1719',rectangle_example(True),caption,filename='P1719-aligned')

    f=Figure('可见区间嵌套：内部每多一层就再矮一',370)
    f.row([5,4,5,3,4,4,5,5,5],240,x=45,width=76,colors={3:RED})
    for y,l,r,color in [(85,1,3,BLUE),(145,3,7,GREEN),(200,3,5,RED)]:
        f.line(83+(l-1)*76,y,83+(r-1)*76,y,color,width=4)
        f.line(83+(l-1)*76,y,83+(l-1)*76,y+18,color);f.line(83+(r-1)*76,y,83+(r-1)*76,y+18,color)
    f.text(90,340,'位置四同时在 (3,7)、(3,5) 内部：最高 5−2=3',size=21)
    save('P2879',f,'横括号是三个非空可见区间，严格内部才降层；样例另外两条相邻端点关系不降低任何位置。')

    f=Figure('差分 [0,5,0,−5,0] 还原出第三格仍有五',320)
    f.row([0,5,0,-5,0],75,x=125,width=110)
    f.row([0,5,5,0,0],185,x=125,width=110,colors={2:RED})
    f.text(70,295,'只问第三格也要从首项累加，不能从查询左端清零',size=21)
    save('P3948',f,'示例表示给位置二到三加五；下行是真实值，第三格的差分虽为零，真实值仍为五。')

    f=Figure('两个半开矩形恰重叠一个单位方格',410)
    for x in range(6):
        for y in range(5):
            count=int(1<=x<4 and 1<=y<3)+int(3<=x<5 and 2<=y<4)
            f.box(115+x*85,70+y*55,82,52,count if count else '',RED if count==2 else GREEN if count else GRAY,
                  fill='#ffe9ed' if count==2 else '#edf7ef' if count else '#fff',size=18)
    f.text(60,390,'[1,4)×[1,3) 与 [3,5)×[2,4)，恰两层的面积为一',size=21)
    save('P5542',f,'每个方格面积一，数字是覆盖层数；红格为横坐标三到四、纵坐标二到三之间的区域。')

    f=Figure('翻转零异或前三项：内部前缀值只换位置',355)
    f.row([3,1,2,3],70,x=175,width=115)
    for i,v in enumerate([0,3,2,0,3]):f.text(170+i*115,160,v,BLUE,size=22,anchor='middle')
    f.row([2,1,3,3],210,x=175,width=115)
    for i,v in enumerate([0,2,3,0,3]):f.text(170+i*115,300,v,GREEN,size=22,anchor='middle')
    f.text(60,343,'两端零不变，内部三与二对调，全部前缀频次保持',size=21)
    save('P9533',f,'数组画在格子里，前缀异或值画在格子边界；不能把两行的前缀位置当作数组元素。')

    f=Figure('三行带内列计数 [0,1,2,3]，取末两列达到五',350)
    for i,row in enumerate(['0001','0011','0111']):
        for j,c in enumerate(row):f.box(145+j*105,65+i*55,102,52,'●' if c=='1' else '',GREEN if j>=2 else GRAY,
                                      fill='#e6f7ed' if j>=2 else '#fff')
    f.row([0,1,2,3],250,x=145,width=105,colors={2:GREEN,3:GREEN})
    f.text(65,340,'k=5：行带高三，最短合法窗口宽二，面积六',size=22)
    save('P10719',f,'下行是各列真实黑格计数；绿色两列黑格数为五，左侧零黑格列没有保留价值。')

    f=Figure('[1,2,2,1] 的三种合法完整划分',350)
    for y,cuts,label in [(80,[1,2,3],'贡献 1+2+2+1=6'),(165,[1,3],'贡献 1+4+1=6'),(250,[],'贡献 1×2×2×1=4')]:
        f.row([1,2,2,1],y,x=100,width=90)
        for cut in cuts:f.line(100+cut*90-2,y-10,100+cut*90-2,y+58,RED,width=4)
        f.text(490,y+31,label,size=20)
    f.text(100,335,'每块的首尾值相同；贡献总和 6+6+4=16',size=22)
    save('P12674',f,'红线是真正的分块边界，不能把相同值之间的所有区间任意重叠地选取。')

    f=Figure('五乘五地毯样例：每格先异或，再把结果相加',420)
    n=5;count=[[0]*n for _ in range(n)]
    for x1,y1,x2,y2 in [(2,2,3,3),(3,3,5,5),(1,2,1,4)]:
        for x in range(x1-1,x2):
            for y in range(y1-1,y2):count[x][y]+=1
    for x in range(n):
        for y in range(n):f.box(175+y*75,60+x*57,72,54,count[x][y],RED if count[x][y]==2 else BLUE,size=20)
    answer=sum((x+y+2)^count[x][y] for x in range(n) for y in range(n));assert answer==146
    f.text(75,385,'格 (3,3) 覆盖二次，贡献 (3+3) xor 2=4；总和 146',size=21)
    save('P13787',f,'格内数字只表示覆盖次数；坐标从一开始，只有格三三叠了两块地毯。')

    f=Figure('[4,3 | 2,5]：反击后左前线变为空城',420)
    for y,row,cut,label in [(80,[4,3,2,5],2,'初始 7 : 7'),(190,[4,0,5,5],3,'左攻占后 9 : 5'),(300,[4,0,10,0],2,'右反击后 4 : 10')]:
        f.text(25,y+31,label,size=18);f.row(row,y,x=270,width=105)
        f.line(270+cut*105-2,y-10,270+cut*105-2,y+58,RED,width=4)
    f.text(75,401,'右方可以用相等兵力反击；左方当前前线零，不能马上夺回',size=21)
    save('P14520',f,'红线是实际领地分界，部队转入被攻占城，原城确实清零；领地数与总兵力不是同一个量。')

    f=Figure('四十一的三段连续素数表示',325)
    f.row([2,3,5,7,11,13,17,'…',41],65,x=50,width=76)
    for y,left,right,label in [(165,0,5,'2+3+5+7+11+13'),(215,4,6,'11+13+17'),(265,8,8,'41')]:
        f.line(86+left*76,y,86+right*76,y,GREEN,width=6);f.circle(86+left*76,y,'',GREEN,radius=5)
        f.text(45,y+32,label,size=18)
    save('UVA1210',f,'每条绿色线取完整素数表的一段；省略号中的素数依然存在，单独四十一也是一个连续段。')

    for spec in specs:
        if spec.pid not in figures:continue
        key,data,caption=figures[spec.pid];spec.images[key]=data
        spec.images.update(history.get(spec.pid,{}))
        block='\n\n!['+caption+']('+key+')\n\n'+caption
        head,separator,tail=spec.detail.partition('\n\n');spec.detail=head+block+(separator+tail if separator else '')
        spec.brief+=block
