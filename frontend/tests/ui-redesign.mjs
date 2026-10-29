import { openSettings } from './settings-navigation.mjs';
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { createServer } from 'vite';
import { chromium } from 'playwright';

const vite=await createServer({server:{host:'127.0.0.1',port:18827,strictPort:true}});
await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[],writes=[];
page.on('pageerror',error=>errors.push(error.message));
page.setDefaultTimeout(12000);
const timestamp=new Date().toISOString(),date=new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Shanghai'});
const self={userId:'11111111-1111-4111-8111-111111111111',nickname:'训练者甲'},other={userId:'22222222-2222-4222-8222-222222222222',nickname:'训练者乙'};
const rows=Array.from({length:120},(_,index)=>({id:`fixture::${index}`,contest:'周赛 166',problem:String(index+1),title:`列表定位测试 ${String(index+1).padStart(3,'0')}`,tags:['模拟'],knowledge:'模拟',platform:'牛客',series:'周赛',difficulty:800+index*10,url:`https://example.com/${index}`,contestDate:'2026-10-20T00:00:00Z',solutionAvailable:true}));
for(const row of rows){row.contestProblemCount=rows.filter(item=>item.contest===row.contest&&item.platform===row.platform).length;row.catalogContentReady=true;}
const training=rows.map(row=>({id:row.id,activeAt:timestamp,lastActivityAt:timestamp,today:true,accepted:false,verdict:null,attempts:0}));
let preferences=null,likes={total:4,likedToday:false},failLike=true,boardDay=date,notifications=[{id:'33333333-3333-4333-8333-333333333333',kind:'comment',actor:other,recipient:self,text:'一起加油 <script>window.untrusted=true</script>',createdAt:timestamp,read:false}];
notifications.push(...Array.from({length:100},(_,index)=>({id:`55555555-5555-4555-8555-${String(index).padStart(12,'0')}`,kind:'like',actor:other,recipient:self,createdAt:timestamp,read:false})));
const workspace=()=>({training,sets:[],contests:[],activeContest:null,goals:{goals:[]},goalTasks:[],summary:{total:120,accepted:training.filter(row=>row.accepted).length,todayAccepted:0,attempts:0,due:0,pending:0,streak:1},now:timestamp});
const progress={badge:'tier-7',level:8,tier:'大师',rankTier:'大师',rankScore:2000,titles:[]};
const ranked={badge:'tier-7',tier:'大师',qualified:true,abilityScore:2000,nextAbilityScore:2100,evidenceCount:8,minimumEvidence:5,levelGate:5};
ranked.tierRequirements=['黑铁','青铜','白银','黄金','铂金','翡翠','钻石','大师','宗师','王者'].map((tier,index)=>({tier,badge:`tier-${index}`,minAbilityScore:[0,800,1000,1200,1400,1600,1800,2000,2100,2200][index]}));
const hub={settings:{githubRepo:'3097729287/acm-algo-trainer',accounts:{},autoSync:false,intervalHours:6,minDifficulty:0,maxDifficulty:2199},sync:{busy:false},updates:{currentVersion:'1.1.5'},accounts:[],notifications:[]};
await page.addInitScript(()=>localStorage.setItem('tb.preferences',JSON.stringify({onboardingGuideVersion:2,theme:'dark',accent:'teal',backdrop:'aurora',panelOpacity:35,widgets:true,fontSize:16,navOrder:['mine','library','competitions','mock','rankings','growth','records','activity','lectures'],views:[]})));
await page.route('**/api/**',async route=>{
  const request=route.request(),url=new URL(request.url()),path=url.pathname;
  if(!path.startsWith('/api/'))return route.continue();
  const body=request.method()==='POST'?request.postDataJSON():null;
  if(body)writes.push({path,body});
  let value;
  if(path==='/api/account')value={required:false,authenticated:true,usesOriginalWorkspace:true,token:'fixture',account:self};
  else if(path==='/api/training-list-likes')value={likes:[]};
  else if(path==='/api/preferences'){if(body)preferences=body.preferences;value={preferences,updatedAt:timestamp};}
  else if(path==='/api/contest-calendar')value={contests:[],refreshing:false,importing:false};
  else if(path==='/api/content-update')value={revision:0,status:'current',error:''};
  else if(path==='/api/software-update')value={currentVersion:'1.1.5',status:'current',autoCheck:false,canInstall:false};
  else if(path==='/api/browser-preparation')value={available:false};
  else if(path==='/api/data')value={rows,categories:[],token:'fixture',today:date,revision:'ui-social'};
  else if(path==='/api/workspace')value=workspace();
  else if(path==='/api/hub')value=hub;
  else if(path==='/api/insights')value={summary:{officialSolved:0,submissions:0,activeDays:1,streak:1},growth:{confirmed:true,authority:{owner:self.userId,epoch:'legacy-fixture',revision:1},...progress,totalXp:6265,currentLevelXp:665,nextLevelXp:1600,ranked},knowledge:[],achievements:[],activity:[],recommendations:[],assessment:{platforms:[]},dailyTasks:{tasks:[]}};
  else if(path==='/api/profile')value={profile:self,leaderboard:{configured:true,status:'ready'}};
  else if(path==='/api/goals')value={goals:[]};
  else if(path==='/api/contests/events')value={events:[]};
  else if(path==='/api/submissions')value={submissions:[],total:0,hasMore:false};
  else if(path==='/api/lectures')value={lectures:[]};
  else if(path==='/api/desktop/fullscreen')value={available:false,fullscreen:false};
  else if(path==='/api/training/start')value={workspace:workspace()};
  else if(path==='/api/problem')value={id:url.searchParams.get('id'),title:rows.find(row=>row.id===url.searchParams.get('id')).title,markdown:'## 题目描述\n\n测试题面。\n\n## 样例\n\n```text\n1 2\n```',samples:[{input:'1\n',output:'2\n'}],limits:{timeMs:2000,memoryMb:256},judge:{scope:'samples',cases:1},statementAvailable:true,draft:'int main() { return 0; }',submissions:[]};
  else if(path==='/api/draft')value={savedAt:timestamp};
  else if(path==='/api/translation/settings')value={provider:'custom',providerName:'自定义',model:'fixture',configured:false,keyStored:false,providers:[]};
  else if(path==='/api/leaderboard')value={period:url.searchParams.get('period')||'daily',date:boardDay,configured:true,status:'ready',hasSnapshot:true,socialAvailable:true,socialProtocol:1,isAdmin:false,entries:[{...self,rank:1,count:2,likes:{total:9,likedToday:false},publicProgress:progress},{...other,rank:2,count:1,likes,publicProgress:progress}],self};
  else if(path==='/api/leaderboard/sync')value={queued:true};
  else if(path==='/api/social')value={available:true,protocol:1,totalLikes:9,todayLikes:3,unreadCount:notifications.filter(row=>!row.read).length,notifications:notifications.slice(0,100),activity:likes.likedToday?[{id:'44444444-4444-4444-8444-444444444444',kind:'like',actor:self,recipient:other,createdAt:timestamp}]:[]};
  else if(path==='/api/social/likes'){
    await new Promise(resolve=>setTimeout(resolve,120));
    if(failLike){failLike=false;await route.fulfill({status:503,json:{error:'测试连接中断'}});return;}
    likes={total:likes.total+(likes.likedToday?0:1),likedToday:true};value={created:true,targetId:other.userId,likes};
  }
  else if(path==='/api/social/comments')value={created:true,id:body.requestId};
  else if(path==='/api/social/read'){notifications=notifications.map(row=>body.all===true||body.ids?.includes(row.id)?{...row,read:true}:row);value={ok:true};}
  else {await route.fulfill({status:404,json:{error:'fixture missing '+path}});return;}
  await route.fulfill({json:value});
});
const nav=name=>page.locator('.sidebar').getByRole('button',{name,exact:true});
const checkOverflow=async()=>assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
async function shot(name){await page.screenshot({path:`tests/screenshots/ui-social-${name}.png`,animations:'disabled'});}
try {
 await mkdir('tests/screenshots',{recursive:true});
 await page.goto('http://127.0.0.1:18827');
 await page.locator('.problem-table tr[data-id]').first().waitFor();
 await page.getByLabel('爱心：历史 6，今日 3',{exact:true}).waitFor();
 const paths=await page.evaluate(async()=>{const {catalogSegments}=await import('/src/components/CatalogExplorer.jsx');return ['练习赛 153','CCPC 2025 郑州区域赛（热身赛）','CCPC 2025 郑州区域赛','ICPC 2026 亚洲区网络预选赛'].map(contest=>catalogSegments({contest,platform:'牛客'}));});
 assert.deepEqual(paths[0],['牛客','练习赛','练习赛 153']);assert.deepEqual(paths[1].slice(0,3),['XCPC','CCPC 区域赛','2025年']);assert.deepEqual(paths[1].slice(0,-1),paths[2].slice(0,-1));assert.equal(paths[1].at(-1),'热身赛');assert.equal(paths[2].at(-1),'正赛');assert.equal(paths[3][1],'网络预选赛');
 assert.equal(await page.locator('.sidebar').evaluate(el=>Math.round(el.getBoundingClientRect().width)),128);
 assert.equal(await page.locator('.knowledge-drawer-toggle').count(),0);
 await page.keyboard.press('Control+b');await page.keyboard.press('Control+b');
 assert(await page.locator('.topbar-daily-ac').evaluate(el=>getComputedStyle(el).color===getComputedStyle(el.querySelector('b')).color),'AC count inherits intensity');
 assert.equal(await page.locator('.app-statusbar').getByRole('button',{name:'每日任务',exact:true}).count(),1);
 await page.getByRole('button',{name:'设置头像',exact:true}).click();await page.getByRole('dialog',{name:'修改头像',exact:true}).waitFor();await page.getByRole('button',{name:'选择头像图片',exact:true}).waitFor();await page.keyboard.press('Escape');
 await nav('设置').click();await page.locator('.settings-home-grid').waitFor();assert.equal(await page.getByRole('tab',{name:'头像',exact:true}).count(),0);
 await page.getByRole('tab',{name:'外观',exact:true}).click();
 const opacity=page.getByRole('slider',{name:'面板不透明度',exact:true});assert.equal(await opacity.getAttribute('min'),'0');await opacity.fill('0');await page.waitForTimeout(100);
 assert.equal(await page.locator('html').evaluate(el=>el.style.getPropertyValue('--panel-opacity')),'0%');
 await page.getByRole('button',{name:'重置所有透明度',exact:true}).click();await page.waitForTimeout(100);assert.equal(await opacity.inputValue(),'76');
 await page.waitForTimeout(300);await page.locator('.settings-page').evaluate(el=>el.scrollTop=250);const savedScroll=await page.locator('.settings-page').evaluate(el=>el.scrollTop);await nav('我的训练').click();await nav('设置').click();await page.waitForTimeout(350);assert.equal(await page.locator('.settings-page').evaluate(el=>el.scrollTop),savedScroll,'settings restores detailed page and scroll position');
 const styles=[];for(const name of ['清简','线框','极光','蓝图']){await page.getByRole('button',{name,exact:true}).click();styles.push(await page.locator('.appearance-studio').evaluate(el=>{const style=getComputedStyle(el);return [style.borderRadius,style.borderStyle,style.backgroundImage].join('|');}));}assert.equal(new Set(styles).size,4,'all presets produce distinct rendered surfaces');await page.getByRole('button',{name:'清简',exact:true}).click();
 await page.getByRole('button',{name:'返回设置首页',exact:true}).click();await page.getByRole('tab',{name:'翻译 API',exact:true}).click();await page.getByLabel('题面翻译配置',{exact:true}).waitFor();
 await nav('模拟赛').click();await page.locator('.mock-mode-options').waitFor();assert.equal(await page.getByText('按目标组成一套训练',{exact:true}).count(),0);
 await page.getByRole('button',{name:'综合训练',exact:true}).hover();assert.equal(await page.getByRole('tooltip').count(),0);await page.screenshot({path:'tests/screenshots/ui-redesign-mock.png'});
 await nav('比赛').click();await page.getByRole('button',{name:'比赛文件夹浏览',exact:true}).waitFor();await page.locator('.competition-card').first().waitFor();
 await nav('题库').click();assert.equal(await page.getByRole('button',{name:'逐层浏览题库',exact:true}).count(),0);
 await page.locator('.problem-table tr[data-id]').first().waitFor();
 await page.locator('.problem-table tr[data-id]').first().locator('.problem-title').click();await page.locator('.cm-editor').waitFor();assert.equal(await page.locator('.topbar').isVisible(),false);assert.equal(await page.locator('.app-statusbar').isVisible(),false);await page.getByRole('button',{name:'返回列表',exact:true}).click();
 await nav('排行榜').click();await page.locator('.ranking-table tbody tr').first().waitFor();assert.equal(await page.getByText('本榜训练者',{exact:true}).count(),0);assert.equal(await page.getByRole('button',{name:'同步与刷新',exact:true}).innerText(),'');await checkOverflow();await page.screenshot({path:'tests/screenshots/ui-redesign-ranking.png'});
 await openSettings(page,'新手指引');await page.getByRole('button',{name:/入门总览/}).click();await page.getByRole('heading',{name:'按等级逐步开放',exact:true}).waitFor();for(const title of ['下一步推荐做的事','收起与展开侧边栏','连接账号']){await page.locator('.tour-card').getByRole('button',{name:'下一步',exact:true}).click();await page.locator('.tour-card').getByRole('heading',{name:title,exact:true}).waitFor();}
 const next=page.locator('.tour-card').getByRole('button',{name:'下一步',exact:true});
 await next.click();await page.getByRole('heading',{name:'找到想练的题',exact:true}).waitFor();
 await next.click();await page.getByRole('heading',{name:'进入练习',exact:true}).waitFor();assert(await next.isDisabled());
 await page.locator('.problem-table tr[data-id]').first().locator('.problem-title').click();
 await page.getByRole('heading',{name:'阅读题面',exact:true}).waitFor();await page.locator('.cm-editor').waitFor();
 for (const title of ['编写代码','运行与提交','回到题库']) {await next.click();await page.locator('.tour-card').getByRole('heading',{name:title,exact:true}).waitFor();assert(await page.locator('.tour-highlight').isVisible());}
 assert(await next.isDisabled());await page.getByRole('button',{name:'返回列表',exact:true}).click();
 await page.getByRole('heading',{name:'查看提交结果',exact:true}).waitFor();
 for (const title of ['组成一场训练','安排下一次练习','查看比赛日历','完成入门']) {await next.click();await page.locator('.tour-card').getByRole('heading',{name:title,exact:true}).waitFor();}
 await page.locator('.tour-card').getByRole('button',{name:'完成',exact:true}).click();assert.equal(await page.locator('.guided-tour').count(),0);
 await openSettings(page,'新手指引');await page.getByRole('button',{name:/入门总览/}).click();await page.getByRole('heading',{name:'按等级逐步开放',exact:true}).waitFor();
 await page.locator('.tour-card').getByRole('button',{name:'结束指引 ×',exact:true}).click();await page.setViewportSize({width:1280,height:800});await nav('设置').click();if(!(await page.locator('.settings-home-grid').count()))await page.keyboard.press('Escape');await page.getByRole('tab',{name:'外观',exact:true}).click();await page.getByRole('spinbutton',{name:'界面字号',exact:true}).fill('22');await page.getByRole('spinbutton',{name:'界面字号',exact:true}).blur();await checkOverflow();await page.screenshot({path:'tests/screenshots/ui-redesign-settings-22.png'});
 await openSettings(page, '外观');await page.getByRole('button',{name:'云白浅色',exact:true}).click();await nav('模拟赛').click();await page.locator('.mock-mode-options').waitFor();await checkOverflow();await page.getByRole('button',{name:'训练筛选',exact:true}).click();assert((await page.getByLabel('模拟赛时长',{exact:true}).boundingBox()).width>=70);await page.keyboard.press('Escape');await page.screenshot({path:'tests/screenshots/ui-redesign-light-mock-22.png'});
 assert.equal(errors.length,0,JSON.stringify(errors));console.log('UI redesign navigation checks passed');
} finally {await browser.close();await vite.close();}
