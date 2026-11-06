import {BookOpen,NotebookTabs,Code2,FlaskConical,LayoutDashboard,CalendarDays,ChartNoAxesCombined,History,Trophy,Swords,UsersRound,Flag,Clock,Target,Library,FolderOpen,Settings,LogIn,UserPlus,Brain,Layers,Globe,GraduationCap} from 'lucide-react';

const icons={概况:LayoutDashboard,计划:CalendarDays,进度:ChartNoAxesCombined,过题数:Trophy,排位分:Swords,团队训练:UsersRound,维基百科:NotebookTabs,从零讲:BookOpen,模板:Code2,实验室:FlaskConical,学习概览:LayoutDashboard,本周计划:CalendarDays,专题进度:ChartNoAxesCombined,历史记录:History,过题数排行榜:Trophy,排位分排行榜:Swords,团队训练排行榜:UsersRound,比赛:Flag,模拟赛:Clock,对战:Swords,我的训练:Target,题库:Library,题单:FolderOpen,排位:Trophy,思维对决:Brain,登录:LogIn,注册:UserPlus,设置:Settings,每日:CalendarDays,本周:CalendarDays,累计:History,全部比赛:Layers,牛客:GraduationCap,洛谷:GraduationCap,CF:Code2,AC:Code2,QOJ:Code2,XCPC:Trophy,蓝桥杯:Trophy};
export default function BookmarkLabel({children,icon}){
 const Icon=icon||icons[String(children)]||Globe;
 return <><Icon size={15} aria-hidden="true"/><span>{children}</span></>;
}
