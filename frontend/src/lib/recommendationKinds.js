import {BookOpen,CalendarCheck,Code2,Crosshair,FileCode2,Flag,FlaskConical,FolderOpen,GraduationCap,History,RotateCcw,Route,Settings2,Shuffle,Target,Timer,TrendingUp} from 'lucide-react';

export const RECOMMENDATION_KINDS={
 knowledge:{Icon:GraduationCap,label:'知识点学习',meaning:'围绕一个知识点接续讲解、实验、应用与间隔检验。'},
 guided:{Icon:Route,label:'跟着做题',meaning:'用配套例题的条件、小实验和迁移指导衔接独立实现。'},
 lecture:{Icon:BookOpen,label:'基础讲解',meaning:'补齐当前知识点需要的概念与先修。'},
 navigation:{Icon:Settings2,label:'学习入口',meaning:'恢复已隐藏的学习入口后继续。'},
 random:{Icon:Shuffle,label:'随机练习',meaning:'从当前适合的完整题目中换一道练习。'},
 specialized:{Icon:Crosshair,label:'专项训练',meaning:'围绕一个知识点选择限时训练。'},
 replay:{Icon:RotateCcw,label:'重现赛',meaning:'选择已有完整题目的比赛进行重现。'},
 'knowledge-review':{Icon:CalendarCheck,label:'知识点间隔检验',meaning:'隔天用陌生题独立检验保留与迁移。'},
 review:{Icon:History,label:'间隔复习',meaning:'到期后独立重写，检验隔日保留。'},
 list:{Icon:FolderOpen,label:'基础题单',meaning:'按题单顺序补齐基础练习。'},
 problem:{Icon:Target,label:'基础练习',meaning:'完成当前适合的单题练习。'},
 course:{Icon:FlaskConical,label:'实验室',meaning:'通过交互实验理解算法。'},
 template:{Icon:Code2,label:'模板',meaning:'学习算法模板与适用条件。'},
 'template-problem':{Icon:FileCode2,label:'模板练习',meaning:'在题目中独立应用模板。'},
 stretch:{Icon:TrendingUp,label:'进阶挑战',meaning:'尝试当前基础之上的题目。'},
 contest:{Icon:Flag,label:'继续比赛',meaning:'回到正在进行的比赛。'},
 mixed:{Icon:Timer,label:'混合限时训练',meaning:'在限时训练中综合运用知识。'},
};
