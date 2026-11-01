import {Clock,Code2,Flag,GraduationCap,Layers,Medal,Settings} from 'lucide-react';

export const OPACITY_GROUPS=[
  {id:'pages',label:'主要界面',icon:Layers,items:[['mine','我的训练'],['library','题库'],['training-lists','题单'],['rankings','排行榜'],['growth','成长'],['records','提交记录'],['activity','活动记录']]},
  {id:'practice',label:'单题',icon:Code2,items:[['statement','题面'],['editor','代码编辑器'],['solution','题解界面'],['practice-toolbar','顶部工具栏'],['practice-picker','选题菜单'],['template-picker','模板选择']]},
  {id:'contests',label:'比赛',icon:Flag,items:[['competitions','比赛目录'],['contest-statement','比赛题面'],['contest-editor','比赛代码编辑器'],['contest-toolbar','比赛工具栏'],['contest-picker','比赛选题菜单'],['contest-calendar','比赛日历']]},
  {id:'mock',label:'模拟赛',icon:Clock,items:[['mock','模拟赛界面'],['mock-statement','模拟赛题面'],['mock-editor','模拟赛代码编辑器'],['mock-toolbar','模拟赛工具栏'],['mock-picker','模拟赛选题菜单']]},
  {id:'learning',label:'学习内容',icon:GraduationCap,items:[['paths','实验室'],['templates','模板'],['lectures','从零讲'],['initial-code','初始代码模板']]},
  {id:'growth-dialogs',label:'任务与成就',icon:Medal,items:[['daily-tasks','每日任务'],['achievements','成就'],['level-up','等级提升']]},
  {id:'settings',label:'设置与弹窗',icon:Settings,items:[['settings','设置'],['popups','其他弹窗'],['messages','消息与更新'],['accounts','账号与身份']]},
];
export const OPACITY_KEYS=OPACITY_GROUPS.flatMap(group=>group.items.map(([key])=>key));
export const SURFACE_DEFAULTS=Object.fromEntries(['practice-picker','contest-picker','mock-picker','template-picker','popups','daily-tasks','achievements','level-up','messages','accounts','contest-calendar'].map(key=>[key,100]));
export const surfaceOpacityValue=(prefs,key)=>prefs.pageOpacities?.[key]??SURFACE_DEFAULTS[key]??prefs.panelOpacity??76;
export function opacityStyle(key,fallback='var(--panel-opacity,76%)') {
  const opacity=`var(--opacity-${key},${fallback})`;
  return {'--page-opacity':opacity,'--panel':`color-mix(in srgb,var(--panel-base) ${opacity},transparent)`,'--panel-2':`color-mix(in srgb,var(--panel-raised-base) ${opacity},transparent)`};
}
