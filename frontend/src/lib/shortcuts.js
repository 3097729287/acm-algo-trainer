export const SHORTCUTS=[
 ['commands','命令面板','Ctrl+K','全局'],['sidebar','展开或收起菜单','Ctrl+B','全局'],['settings','打开设置','Ctrl+,','全局'],['search','搜索','Ctrl+F','全局'],['refresh','刷新','F5','全局'],['regions','切换焦点区域','F6','全局'],['help','快捷键设置','?','全局'],
 ['page-mine','我的训练','Ctrl+1','导航'],['page-library','题库','Ctrl+2','导航'],['page-paths','题单','Ctrl+3','导航'],['page-competitions','比赛','Ctrl+4','导航'],['page-mock','模拟赛','Ctrl+5','导航'],['page-records','提交记录','Ctrl+6','导航'],['page-growth','成长与能力','Ctrl+7','导航'],['page-activity','活动记录','Ctrl+8','导航'],['page-lectures','从零讲','Ctrl+9','导航'],
 ['practice','打开选中题目','Enter','题目列表'],['solution','查看题解','U','题目列表'],['favorite','收藏题目','S','题目列表'],['listSearch','搜索题目','F','题目列表'],
 ['run','运行样例','Ctrl+R','编辑器'],['submit','提交','Ctrl+Enter','编辑器'],['official','原站提交','Ctrl+Shift+Enter','编辑器'],['save','保存草稿','Ctrl+S','编辑器'],['pane-0','题面与代码','Alt+0','编辑器'],['pane-1','只看题面','Alt+1','编辑器'],['pane-2','只看代码','Alt+2','编辑器']
];
export function shortcutValue(id,overrides={}) {return overrides[id]??SHORTCUTS.find(item=>item[0]===id)?.[2]??'';}
export function eventShortcut(event) {
 const key=event.key;
 if(['Control','Meta','Shift','Alt','Dead','Unidentified'].includes(key))return '';
 const value=key===' '?'Space':key.length===1?key.toUpperCase():key;
 return [(event.ctrlKey||event.metaKey)&&'Ctrl',event.altKey&&'Alt',event.shiftKey&&key.length!==1&&'Shift',event.shiftKey&&/[A-Za-z]/.test(key)&&key.length===1&&'Shift',value].filter(Boolean).join('+');
}
export function matchesShortcut(event,id,overrides) {const value=shortcutValue(id,overrides);return !!value&&eventShortcut(event).toLowerCase()===value.toLowerCase();}
