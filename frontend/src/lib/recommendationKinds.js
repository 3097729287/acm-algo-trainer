import {Code2,FileCode2,Flag,FlaskConical,FolderOpen,History,Target,Timer,TrendingUp} from 'lucide-react';

export const RECOMMENDATION_KINDS={
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
