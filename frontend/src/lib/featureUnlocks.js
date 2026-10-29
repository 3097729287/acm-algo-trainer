// One source for navigation, shortcuts, commands, guides and level notices.
export const PAGE_UNLOCKS=Object.freeze([
 {id:'mine',level:1,label:'我的训练',always:true},{id:'training-lists',level:1,label:'题单'},
 {id:'library',level:2,label:'题库'},{id:'rankings',level:2,label:'排行榜'},
 {id:'competitions',level:3,label:'比赛'},{id:'mock',level:3,label:'模拟赛'},
 {id:'paths',level:4,label:'算法实验室'},{id:'templates',level:4,label:'模板'},{id:'lectures',level:4,label:'从零讲'},
 {id:'growth',level:5,label:'成长与能力'},{id:'activity',level:5,label:'活动记录'},
 {id:'records',level:1,label:'提交记录',always:true},{id:'settings',level:1,label:'设置',always:true},
]);
export const PAGE_LEVELS=Object.freeze(Object.fromEntries(PAGE_UNLOCKS.map(item=>[item.id,item.level])));
export const ESSENTIAL_PAGES=Object.freeze(PAGE_UNLOCKS.filter(item=>item.always).map(item=>item.id));
export const optionalPages=PAGE_UNLOCKS.filter(item=>!item.always).map(item=>item.id);
export function hiddenPages(value){return [...new Set((Array.isArray(value)?value:[]).filter(id=>optionalPages.includes(id)))];}
export function canOpenPage(id,level,preferences={}){
 if(id==='goals')id='growth';if(typeof id!=='string')return false;
 if(id==='practice'||id==='overview'||id.startsWith('settings:'))return true;
 const page=PAGE_UNLOCKS.find(item=>item.id===id);
 const current=level===Infinity?Infinity:Number.isFinite(level)?level:1;
 return !!page&&(page.always||(!hiddenPages(preferences.hiddenNavPages).includes(id)&&current>=page.level));
}
export const pageAvailable=canOpenPage,guideAvailable=canOpenPage;
export const availablePages=(level,preferences={})=>PAGE_UNLOCKS.filter(item=>canOpenPage(item.id,level,preferences)).map(item=>item.id);
export function newlyUnlocked(from,to){return PAGE_UNLOCKS.filter(item=>!item.always&&item.level>from&&item.level<=to);}
export function nextUnlock(level){const next=PAGE_UNLOCKS.filter(item=>item.level>level);return next.length?next.filter(item=>item.level===Math.min(...next.map(item=>item.level))):[];}
