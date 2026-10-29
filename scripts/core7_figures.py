"""Problem-specific diagrams, with the same objects and values as the articles."""
import base64
from editorial_figures import Figure, BLUE, RED, GREEN, GRAY
from core7_authoring import OUT


def attach_figures(specs):
    figures={}
    directory=OUT/'figures'
    def save(pid,f,caption):
        path=f.save(pid,directory)
        key='assets/core7/'+pid+'.svg'
        figures[pid]=(key,'data:image/svg+xml;base64,'+base64.b64encode(path.read_bytes()).decode(),caption)

    f=Figure('267 度电：按实际落入的区间分别收费',315)
    for x,t in [(90,'0'),(270,'150'),(410,'267'),(570,'400')]:f.text(x,95,t,anchor='middle')
    f.line(90,125,270,125,BLUE,width=12);f.line(270,125,410,125,GREEN,width=12);f.line(410,125,570,125,GRAY,dash=True)
    f.text(150,180,'150 度',BLUE);f.text(310,180,'117 度',GREEN)
    f.text(65,245,'150 × 0.4463 + 117 × 0.4663',size=23)
    f.text(65,290,'400 度以后的区间本次用量为零',GRAY,size=21)
    save('P1422',f,'二百六十七度分为一百五十度与一百一十七度，超出部分为零。')

    f=Figure('较小角在 B，对边 AC=3，斜边 BC=5',385)
    a,b,c=(160,295),(440,295),(160,85)
    for u,v in [(a,b),(b,c),(c,a)]:f.line(*u,*v,BLUE)
    for (x,y),label in [(a,'A'),(b,'B'),(c,'C')]:f.text(x-20,y+30,label)
    f.text(110,200,'3',GREEN);f.text(295,330,'4');f.text(315,180,'5',RED)
    f.line(160,275,180,275);f.line(180,275,180,295)
    f.text(485,180,'sin B = 3/5',GREEN,size=23)
    save('P1888',f,'图中的较小锐角为 B；它的对边是最短边，斜边是最长边。')

    f=Figure('去掉一份最低、一份最高，不删除所有相同分数',270)
    f.row([1,5,5,9],95,x=155,width=110,colors={0:RED,1:GREEN,2:GREEN,3:RED})
    f.text(185,195,'删除',RED,anchor='middle');f.text(350,195,'保留两个五',GREEN,anchor='middle');f.text(515,195,'删除',RED,anchor='middle')
    f.text(125,245,'(1+5+5+9−1−9) / (4−2) = 5',size=23)
    save('P5726',f,'四个分数一、五、五、九，删除两端的一份后，两个五都保留。')

    f=Figure('L=5：六个树位，重叠位置只移除一次',350)
    for i in range(6):f.circle(100+i*110,110,i,GREEN if i in [0,5] else RED)
    f.line(210,175,430,175,BLUE,width=8);f.text(245,210,'操作一：[1,3]',BLUE)
    f.line(430,245,540,245,RED,width=8);f.text(390,285,'操作二：[3,4]',RED)
    f.text(80,330,'最后只留下位置 0、5，共两棵',GREEN)
    save('P1047',f,'两个闭区间的交点三只移除一次；整条道路包含零号和五号树位。')

    f=Figure('翻转会抵消；最后单独翻第三盏',370)
    for y,label,bits in [(85,'初始',[0,0,0]),(155,'翻 1、2',[1,1,0]),(225,'再翻 1、2',[0,0,0]),(295,'翻 3',[0,0,1])]:
        f.text(35,y+30,label,size=20);f.row(bits,y,x=300,width=100,colors={i:GREEN if b else GRAY for i,b in enumerate(bits)})
    save('P1161',f,'两次相同操作相互抵消，之后只翻第三盏灯，答案为三。')

    f=Figure('n=3：游程 3、4、2 可以跨过行尾',330)
    for i,row in enumerate([[0,0,0],[1,1,1],[1,0,0]]):f.row(row,75+i*65,x=215,width=100)
    f.text(35,305,'第 2 段的四个 1：第二行三格，加第三行第一格',size=20)
    save('P1319',f,'三乘三图案编码为三、四、二，第二段的四个一跨过了第二行行尾。')

    f=Figure('三个残留字符都指向同一次 boy 写入',300)
    f.row(['b','o','y'],95,x=180,width=120)
    for i in range(3):f.text(240+120*i,80,i,GRAY,size=18,anchor='middle');f.line(240+120*i,150,240,220,BLUE)
    f.box(130,220,220,55,'起点 0：只计一次',GREEN,size=20)
    save('P1321',f,'b、o、y 分别按零、一、二的偏移还原，得到同一起点零。')

    f=Figure('当前位置 i=4：只检查它左侧的三条鱼',290)
    f.row([4,3,0,5,1,2],100,x=75,width=105,colors={0:GREEN,1:GREEN,2:GREEN,3:RED,4:GRAY,5:GRAY})
    for i in range(6):f.text(125+i*105,83,i+1,GRAY,size=18,anchor='middle')
    f.text(75,220,'4、3、0 都小于 5 → 计三条',GREEN)
    f.text(75,265,'右侧的 1、2 即使更小也不参加本次计数',GRAY,size=20)
    save('P1428',f,'第四条鱼的可爱值是五，左侧三条都更小，所以这一项答案为三。')

    f=Figure('赋值复制当时的值，后续修改不会自动传递',320)
    for x,label,values in [(35,'a:=3',[3,0,0]),(280,'b:=a',[3,3,0]),(525,'a:=5',[5,3,0])]:
        f.text(x+85,90,label,anchor='middle');f.row(values,120,x=x,width=65)
        f.text(x+85,205,'a     b     c',GRAY,size=20,anchor='middle')
    f.text(70,280,'最后 a=5，但 b 保存的仍是复制时的 3',GREEN,size=21)
    save('P1597',f,'按顺序执行 a:=3;b:=a;a:=5;，最终三个值是五、三、零。')

    f=Figure('先模拟得到唯一过程，再反向读取保存的各项',290)
    numbers=[6,3,10,5,16,8,4,2,1]
    for i,x in enumerate(numbers):f.circle(60+i*80,125,x,radius=25)
    for i in range(8):f.line(87+i*80,125,113+i*80,125)
    f.text(60,205,'模拟：从左到右 →',BLUE);f.text(390,250,'输出：← 从右到左',GREEN)
    save('P5727',f,'从六开始到一的完整过程如图，逆序输出从最右的一开始。')

    f=Figure('3×3×3：分别看三个 z 层的实际格子',340)
    for z,x in enumerate([50,290,530],1):
        f.text(x+85,85,'z = '+str(z),anchor='middle')
        for row in range(3):
            for col in range(3):
                removed=z<=2 and row<2 and col<2
                f.box(x+col*52,110+row*52,48,48,'挖' if removed else '留',RED if removed else GREEN,size=18)
    f.text(45,315,'前两层各挖 2×2=4 格，共挖 8 格，留下 27−8=19 格',size=20)
    save('P5729',f,'每层画出三个方向中固定 z 后的九格；挖掘范围的端点格子都包含。')

    f=Figure('第四行的两个三，分别来自上一行相邻两项',350)
    rows=[[1],[1,1],[1,2,1],[1,3,3,1]]
    coords=[]
    for i,row in enumerate(rows):
        points=[]
        for j,v in enumerate(row):
            x=380-(len(row)-1)*55+j*110;y=85+i*65;points.append((x,y));f.circle(x,y,v,GREEN if i==3 and j in [1,2] else BLUE)
        coords.append(points)
    for source,target in [(0,1),(1,1),(1,2),(2,2)]:f.line(coords[2][source][0],coords[2][source][1]+24,coords[3][target][0],coords[3][target][1]-24,GREEN)
    f.text(60,335,'左侧三：1+2；右侧三：2+1；首尾直接为一',size=21)
    save('P5732',f,'图中两组三的全部来源都在上一行，先算上一行再算下一行。')

    f=Figure('600.084：两段分开反转，再删各自无意义的零',345)
    for y,label,values in [(80,'原文',['600','.','084']),(160,'逆序',['006','.','480']),(240,'规范化',['6','.','48'])]:
        f.text(35,y+30,label);f.row(values,y,x=245,width=140)
    f.text(45,325,'整数删左侧零；小数删右侧零；分隔符仍在中间',size=21)
    save('P1553',f,'整数部分去前导零，小数部分去末尾零，得到六点四八。')

    f=Figure('三阶幻方：右上目标被占用，改从原位下移',355)
    grid=[[0,1,0],[3,0,0],[4,0,2]]
    for r,row in enumerate(grid):
        for c,v in enumerate(row):f.box(100+c*75,80+r*75,70,70,v or '',GREEN if v==4 else BLUE,size=24)
    f.line(135,155,210,140,RED,dash=True);f.text(365,135,'从 3 向右上：碰到已有的 1',RED,size=21)
    f.line(135,225,135,240,GREEN);f.text(365,230,'从 3 的原位置下移：填 4',GREEN,size=21)
    f.text(100,335,'右上越界时绕回；发生冲突才改为原位正下方',size=20)
    save('P2615',f,'一、二、三已经填入，四的位置由碰撞规则决定，不能从碰撞目标继续下移。')

    f=Figure('少方一个 A 隔出两个空隙，每隙最多两个 B',295)
    for i,c in enumerate('BBABB'):f.circle(165+i*100,135,c,GREEN if c=='A' else BLUE)
    f.line(140,205,290,205,BLUE,width=6);f.line(440,205,590,205,BLUE,width=6)
    f.text(215,250,'左隙：最多 2 球',BLUE,size=20,anchor='middle');f.text(515,250,'右隙：最多 2 球',BLUE,size=20,anchor='middle')
    save('CF2136A',f,'一比四可排成 BBABB，一比五已经超过两个空隙的总容量。')

    f=Figure('n=5，k=3：一位置放小数，零位置放大数',320)
    f.text(35,115,'s');f.row([1,1,0,1,0],85,x=160,width=105,colors={2:GREEN,4:GREEN})
    f.text(35,215,'p');f.row([1,2,4,3,5],185,x=160,width=105,colors={2:GREEN,4:GREEN})
    f.text(35,290,'任意至少三格都有零位置，那里放的 4 或 5 大于所有一位置',size=19)
    save('CF2136B',f,'字符串与排列按相同下标对齐，零位置承载更大值。')

    f=Figure('末块是三个 3：以前缀位置 2 的最优解接上',345)
    f.row([1,2,3,3,3,1],95,x=70,width=105,colors={0:GREEN,1:GRAY,2:BLUE,3:BLUE,4:BLUE,5:GRAY})
    for i in range(6):f.text(120+i*105,80,i+1,GRAY,size=18,anchor='middle')
    f.line(70,180,275,180,GREEN,width=6);f.line(280,180,590,180,BLUE,width=6)
    f.text(65,230,'f[2]=1：只保留第一个 1',GREEN,size=19)
    f.text(350,230,'本块首位置 l=3，长度 x=3',BLUE,size=19)
    f.text(130,300,'f[5] = f[l−1] + x = f[2] + 3 = 1+3 = 4',size=22)
    save('CF2135A',f,'末块与之前的最优子序列不共用位置，前缀必须停在 l−1。')

    f=Figure('按位或先补齐，再按位与删掉多余的一',340)
    for y,label,bits in [(80,'n=5',[0,1,0,1]),(145,'或 3 → 7',[0,1,1,1]),(210,'与 3 → 3',[0,0,1,1])]:
        f.text(35,y+31,label,size=20);f.row(bits,y,x=290,width=90)
    f.text(35,315,'目标 3 的二进制为 0011，需要同时补一位、删一位',size=21)
    save('P9496',f,'五到三不能只靠一次或或一次与，图中两步构造达到目标。')

    f=Figure('阈值 v=5：三行各有一个有效元素，可覆盖三列',360)
    for base,matrix,label in [(50,[[8,1,1],[9,1,1],[7,1,1]],'原来都集中在第一列'),(430,[[8,1,1],[1,9,1],[1,1,7]],'行内重排后分散到三列')]:
        f.text(base+105,80,label,size=18,anchor='middle')
        for r,row in enumerate(matrix):
            for c,v in enumerate(row):f.box(base+c*70,105+r*60,64,52,v,GREEN if v>=5 else GRAY,size=22)
    f.text(35,335,'有效元素数 c=3，总列数 n=3，最优列数 min(n,c)=3',size=21)
    save('P9497',f,'每次只改一行内部的位置，三个有效元素分别成为三个列的见证。')

    f=Figure('Alice 留出非零 5，把其余含零子集合并',335)
    f.row([0,0,5],80,x=205,width=110,colors={0:RED,1:RED,2:GREEN})
    f.text(35,165,'合并两个零，mex=1；5 留在外面',size=21)
    f.row([1,5],195,x=260,width=110)
    f.text(35,310,'Bob 只能合并 [1,5]，mex=0，终局 Alice 获胜',GREEN,size=21)
    save('P15320',f,'操作子集有两项所以合法；留下的是恰好两个非零数，而非任意多个。')

    f=Figure('相邻四项只有三条相邻边，对应差值 3、2、1',300)
    for i,v in enumerate([1,4,2,3]):f.circle(170+i*140,125,v)
    for i,d in enumerate([3,2,1]):f.line(195+i*140,125,285+i*140,125);f.text(240+i*140,205,'差 '+str(d),GREEN,size=21,anchor='middle')
    f.text(65,270,'三个差覆盖 1、2、3；不是任意两项之间的差',size=22)
    save('P1152',f,'每个差只连接一对相邻元素，三种必需差值各出现一次。')

    f=Figure('计划三人：定位第四名，八十八分同分者全部进入',330)
    f.row([95,95,90,88,88,84],100,x=65,width=105,colors={0:GREEN,1:GREEN,2:GREEN,3:RED,4:GREEN,5:GRAY})
    for i in range(6):f.text(115+i*105,85,'第'+str(i+1)+'名',size=18,anchor='middle')
    f.line(430,155,430,215,RED);f.text(430,245,'第 4 名定位分数线 88',RED,size=21,anchor='middle')
    f.text(65,300,'第 5 名也是 88 分，所以实际面试人数为 5',GREEN,size=21)
    save('P1068',f,'第四名只用来定位分数线，不能截掉后面同分的第五名。')

    f=Figure('相邻交换只消除当前这一对逆序',330)
    for y,row,label in [(75,[3,1,2],'逆序对 2 个'),(155,[1,3,2],'逆序对 1 个'),(235,[1,2,3],'逆序对 0 个')]:
        f.row(row,y,x=170,width=100);f.text(510,y+31,label,GREEN,size=21)
    save('P1116',f,'三先越过一，再越过二，两次相邻交换恰好消除两对逆序。')

    f=Figure('归并排序：两半分别有序，再取两边最小剩余项',365)
    f.text(35,110,'原数组',size=20);f.row([4,2],80,x=220,width=90);f.row([4,5,1],80,x=415,width=90)
    f.text(35,215,'两半有序',size=20);f.row([2,4],185,x=220,width=90);f.row([1,4,5],185,x=415,width=90)
    f.text(35,320,'合并结果',size=20);f.row([1,2,4,4,5],290,x=220,width=90)
    f.line(405,70,405,245,GRAY,dash=True)
    save('P1177',f,'左右两半内部先完成排序，合并时每次比较它们各自未取出的最小项。')

    f=Figure('枢轴 3 的三路划分：只继续包含 k=1 的左段',340)
    f.text(35,110,'划分前');f.row([4,3,2,1,5],80,x=220,width=90)
    f.text(35,235,'划分后');f.row([1,2,3,5,4],205,x=220,width=90,colors={0:GREEN,1:GREEN,2:RED,3:GRAY,4:GRAY})
    f.text(305,190,'小于 3',GREEN,size=20,anchor='middle');f.text(440,190,'等于 3',RED,size=20,anchor='middle');f.text(575,190,'大于 3',GRAY,size=20,anchor='middle')
    f.text(45,315,'零基下标 k=1 在左段；右段 5、4 此时无需排好',size=21)
    save('P1923',f,'两侧内部可以无序，只有小于、等于、大于枢轴这三种关系已经确定。')

    f=Figure('高度顺序固定：五个点必须依次访问',350)
    points=[(100+i*130,265-i*43) for i in range(5)]
    for i in range(4):f.line(*points[i],*points[i+1],BLUE)
    for i,(x,y) in enumerate(points,1):f.circle(x,y,i);f.text(x,y+43,f'({i},{i},{i})',size=18,anchor='middle')
    f.text(80,335,'每一段长 √3，共四段，总长 4√3 ≈ 6.928',GREEN,size=22)
    save('P5143',f,'图按高度投影排列样例五个点，路段的长度仍用全部三维坐标计算。')

    for spec in specs:
        if spec.pid not in figures:continue
        if spec.pid=='P1177' and spec.key!='merge-sort':continue
        key,data,caption=figures[spec.pid]
        image='!['+caption+']('+key+')\n\n'+caption
        spec.images[key]=data
        for field in ['brief','detail']:
            text=getattr(spec,field)
            paragraphs=text.split('\n\n',1)
            setattr(spec,field,paragraphs[0]+'\n\n'+image+('\n\n'+paragraphs[1] if len(paragraphs)>1 else ''))
