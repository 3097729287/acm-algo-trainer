export const SHORTCUTS=[
 ['commands','命令面板','Ctrl+K','全局'],['sidebar','展开或收起菜单','Ctrl+B','全局'],['settings','打开设置','Ctrl+,','全局'],['search','搜索','Ctrl+F','全局'],['refresh','刷新','F5','全局'],['regions','切换焦点区域','F6','全局'],['help','快捷键设置','?','全局'],
 ['page-mine','我的训练','Ctrl+1','导航'],['page-library','题库','Ctrl+2','导航'],['page-training-lists','题单','','导航'],['page-templates','模板','','导航'],['page-paths','实验室','Ctrl+3','导航'],['page-competitions','比赛','Ctrl+4','导航'],['page-mock','模拟赛','Ctrl+5','导航'],['page-records','提交记录','Ctrl+6','导航'],['page-growth','成长','Ctrl+7','导航'],['page-activity','活动记录','Ctrl+8','导航'],['page-lectures','从零讲','Ctrl+9','导航'],
 ['practice','打开选中题目','Enter','题目列表'],['solution','查看题解','U','题目列表'],['favorite','收藏题目','S','题目列表'],['listSearch','搜索题目','F','题目列表'],
 ['run','自测运行','Ctrl+R','编辑器'],['submit','提交','Ctrl+Enter','编辑器'],['official','原站提交','Ctrl+Shift+Enter','编辑器'],['save','格式化代码','Ctrl+S','编辑器'],['pane-0','题面与代码','Alt+0','编辑器'],['pane-1','只看题面','Alt+1','编辑器'],['pane-2','只看代码','Alt+2','编辑器']
];
export const EXTRA_SHORTCUTS=[
 ['statement-font','调整题面字号','Alt+F','编辑器'],['statement-original','在浏览器打开原题','Alt+O','编辑器'],['code-language','选择编程语言','Alt+G','编辑器'],['workbench-undo','撤销载入代码','Alt+Z','编辑器'],
 ['theme','切换日夜间模式','Ctrl+Shift+L','全局'],['calendar','比赛日历','Ctrl+Shift+C','全局'],['daily-tasks','每日任务','Ctrl+Shift+D','全局'],['achievements','成就','Ctrl+Shift+A','全局'],
 ['list-filter','筛选题目','Alt+F','题目列表'],['list-random','随机选题','Alt+R','题目列表'],['list-difficulty','按难度排序','Alt+D','题目列表'],['list-recent','按最近练习排序','Alt+T','题目列表'],
 ['workbench-back','返回列表','Alt+ArrowLeft','编辑器'],['workbench-next','下一题','Ctrl+ArrowRight','编辑器'],['statement-language','切换题面语言','Alt+L','编辑器'],['statement-copy','复制题面','Alt+C','编辑器'],['toolbar-lock','锁定或解锁工具栏','Alt+T','编辑器'],['initial-code','选择初始代码模板','Alt+I','编辑器'],['code-templates','打开模板','Alt+M','编辑器'],['workbench-solution','题解','Alt+U','编辑器'],['console-toggle','展开或收起运行结果','Alt+R','编辑器'],
 ['catalog-up','返回上层','Alt+ArrowLeft','题单'],['catalog-home','返回题单首页','Alt+Home','题单'],['catalog-filter','筛选题单','Alt+F','题单'],['catalog-new','新建题单','Alt+N','题单'],
 ['contest-filter','筛选比赛','Alt+F','比赛'],['contest-folders','比赛文件夹浏览','Alt+V','比赛'],['contest-up','返回上层','Alt+ArrowLeft','比赛'],
 ['mock-filter','模拟赛筛选','Alt+F','模拟赛'],['mock-regenerate','重新选题','Alt+R','模拟赛'],
 ['lecture-learned','标记或取消已学会','Alt+K','从零讲'],['lecture-fullscreen','切换全屏阅读','Alt+Enter','从零讲'],['lecture-back','返回上篇','Alt+ArrowLeft','从零讲'],
 ['template-copy','复制模板代码','Alt+C','模板'],['template-back','返回模板目录','Alt+ArrowLeft','模板'],
 ['records-platform','提交平台筛选','Alt+P','提交记录'],['records-result','提交结果筛选','Alt+V','提交记录'],
 ['ranking-daily','每日排行榜','Alt+1','排行榜'],['ranking-weekly','本周排行榜','Alt+2','排行榜'],['ranking-all','累计排行榜','Alt+3','排行榜'],
 ['initial-new','新建初始代码模板','Alt+N','初始代码模板'],['initial-copy','复制为初始代码模板','Alt+C','初始代码模板']
];
SHORTCUTS.push(...EXTRA_SHORTCUTS);
export const SHORTCUT_GROUPS=[
 ['global','全局',['全局','导航']],['practice','单题界面',['编辑器']],['lists','题库与我的训练',['题目列表']],['catalog','题单',['题单']],['contests','比赛',['比赛']],['mock','模拟赛',['模拟赛']],['lectures','从零讲',['从零讲']],['templates','模板',['模板']],['records','提交记录',['提交记录']],['rankings','排行榜',['排行榜']],['initial','初始代码模板',['初始代码模板']]
];
export function shortcutGroupsConflict(first,second){return first===second||['全局','导航'].includes(first)||['全局','导航'].includes(second);}
export function shortcutValue(id,overrides={}) {return overrides[id]??SHORTCUTS.find(item=>item[0]===id)?.[2]??'';}
export function eventShortcut(event) {
 const key=event.key;
 if(['Control','Meta','Shift','Alt','Dead','Unidentified'].includes(key))return '';
 const value=key===' '?'Space':key.length===1?key.toUpperCase():key;
 return [(event.ctrlKey||event.metaKey)&&'Ctrl',event.altKey&&'Alt',event.shiftKey&&key.length!==1&&'Shift',event.shiftKey&&/[A-Za-z]/.test(key)&&key.length===1&&'Shift',value].filter(Boolean).join('+');
}
export function matchesShortcut(event,id,overrides) {const value=shortcutValue(id,overrides);return !!value&&eventShortcut(event).toLowerCase()===value.toLowerCase();}
