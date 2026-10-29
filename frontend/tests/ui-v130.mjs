import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { createServer } from 'vite';
import { chromium } from 'playwright';

const vite=await createServer({server:{host:'127.0.0.1',port:18828,strictPort:true}});
await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[],writes=[];
page.on('pageerror',error=>errors.push(error.message));
page.setDefaultTimeout(12000);
const timestamp=new Date().toISOString(),date=new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Shanghai'});
const self={userId:'11111111-1111-4111-8111-111111111111',nickname:'训练者甲'},other={userId:'22222222-2222-4222-8222-222222222222',nickname:'训练者乙'};
const rows=Array.from({length:120},(_,index)=>({id:`fixture::${index}`,contest:'周赛 166',problem:String(index+1),title:`列表定位测试 ${String(index+1).padStart(3,'0')}`,tags:['模拟'],knowledge:'模拟',platform:'牛客',series:'周赛',difficulty:800+index*10,url:`https://example.com/${index}`,contestDate:'2026-10-20T00:00:00Z',solutionAvailable:true}));
const training=rows.map(row=>({id:row.id,activeAt:timestamp,lastActivityAt:timestamp,today:true,accepted:false,verdict:null,attempts:0}));
let preferences=null,likes={total:4,likedToday:false},failLike=true,boardDay=date,notifications=[{id:'33333333-3333-4333-8333-333333333333',kind:'comment',actor:other,recipient:self,text:'一起加油 <script>window.untrusted=true</script>',createdAt:timestamp,read:false}];
notifications.push(...Array.from({length:100},(_,index)=>({id:`55555555-5555-4555-8555-${String(index).padStart(12,'0')}`,kind:'like',actor:other,recipient:self,createdAt:timestamp,read:false})));
const workspace=()=>({training,sets:[],contests:[],activeContest:null,goals:{goals:[]},goalTasks:[],summary:{total:120,accepted:training.filter(row=>row.accepted).length,todayAccepted:0,attempts:0,due:0,pending:0,streak:1},now:timestamp});
const progress={badge:'tier-7',level:8,tier:'大师',rankTier:'大师',rankScore:2000,titles:[]};
const ranked={badge:'tier-7',tier:'大师',qualified:true,abilityScore:2000,nextAbilityScore:2100,evidenceCount:8,minimumEvidence:5,levelGate:5};
ranked.tierRequirements=['黑铁','青铜','白银','黄金','铂金','翡翠','钻石','大师','宗师','王者'].map((tier,index)=>({tier,badge:`tier-${index}`,minAbilityScore:[0,800,1000,1200,1400,1600,1800,2000,2100,2200][index]}));
const hub={settings:{githubRepo:'3097729287/acm-algo-trainer',accounts:{},autoSync:false,intervalHours:6,minDifficulty:0,maxDifficulty:2199},sync:{busy:false},updates:{currentVersion:'1.1.5'},accounts:[],notifications:[]};
await page.addInitScript(()=>localStorage.setItem('tb.preferences',JSON.stringify({theme:'dark',accent:'teal',backdrop:'aurora',panelOpacity:35,widgets:true,fontSize:16,navOrder:['mine','library','competitions','mock','rankings','growth','records','activity','lectures'],views:[]})));
await page.route('**/api/**',async route=>{
  const request=route.request(),url=new URL(request.url()),path=url.pathname;
  if(!path.startsWith('/api/'))return route.continue();
  const body=request.method()==='POST'?request.postDataJSON():null;
  if(body)writes.push({path,body});
  let value;
  if(path==='/api/account')value={required:false,authenticated:true,usesOriginalWorkspace:true,token:'fixture',account:self};
  else if(path==='/api/preferences'){if(body)preferences=body.preferences;value={preferences,updatedAt:timestamp};}
  else if(path==='/api/contest-calendar')value={contests:[],refreshing:false,importing:false};
  else if(path==='/api/content-update')value={revision:0,status:'current',error:''};
  else if(path==='/api/software-update')value={currentVersion:'1.1.5',status:'current',autoCheck:false,canInstall:false};
  else if(path==='/api/browser-preparation')value={available:false};
  else if(path==='/api/data')value={rows,categories:[{name:'数据结构',tags:['栈','单调栈'],children:[{name:'单调栈',tags:['单调栈']}]}],token:'fixture',today:date,revision:'ui-social'};
  else if(path==='/api/workspace')value=workspace();
  else if(path==='/api/hub')value=hub;
  else if(path==='/api/insights')value={summary:{officialSolved:0,submissions:0,activeDays:1,streak:1},growth:{...progress,totalXp:6265,currentLevelXp:665,nextLevelXp:1600,ranked},knowledge:[],achievements:[],activity:[],recommendations:[],assessment:{platforms:[]},dailyTasks:{tasks:[]}};
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
 await page.goto('http://127.0.0.1:18828');
 await page.locator('.problem-table tr[data-id]').first().waitFor();
 assert.equal(await page.getByLabel('逐层浏览题库',{exact:true}).count(),0);
 await page.getByLabel('连续练习 1 天',{exact:true}).waitFor();
 await page.getByRole('button',{name:'筛选题目',exact:true}).click();
 await page.getByText('比赛分类',{exact:true}).click();
 await page.getByRole('button',{name:'CF',exact:true}).waitFor();
 await page.locator('.filter-popover').getByText('知识点',{exact:true}).click();
 await page.locator('.filter-knowledge-list').getByRole('button',{name:'单调栈',exact:true}).waitFor();
 await page.keyboard.press('Escape');assert.equal(await page.locator('.filter-popover').count(),0);
 await page.getByRole('button',{name:'正序，点击改为倒序',exact:true}).click();
 await page.getByRole('button',{name:'倒序，点击改为正序',exact:true}).waitFor();
 await nav('成长').click();await page.getByLabel('一级知识雷达',{exact:true}).waitFor();
 assert.equal(await page.locator('.growth-account-panel').count(),0);
 await page.getByRole('button',{name:'数据结构，掌握 ?%，进入二级雷达',exact:true}).click();
 await page.getByLabel('数据结构二级雷达',{exact:true}).waitFor();
 await page.getByRole('button',{name:'单调栈，掌握 ?%，筛选题目',exact:true}).waitFor();
 await page.getByRole('button',{name:'返回一级雷达',exact:true}).click();
 await page.screenshot({path:'tests/screenshots/v130-growth.png'});
 await nav('比赛').click();await page.getByRole('button',{name:'比赛文件夹浏览',exact:true}).waitFor();
 assert.equal(await page.getByRole('button',{name:'文件夹浏览',exact:true}).count(),0);
 await page.locator('.competition-card').first().waitFor();await page.getByRole('button',{name:'开始比赛 周赛 166',exact:true}).waitFor();
 await page.screenshot({path:'tests/screenshots/v130-competitions.png'});
 await nav('题单').click();await page.getByRole('button',{name:/双指针/}).click();
 await page.getByRole('tab',{name:/交互推演/}).click();
 for(let step=0;step<3;step++)await page.getByRole('button',{name:'下一步',exact:true}).click();assert.match(await page.locator('.pointer-demo p').innerText(),/找到/);
 await page.screenshot({path:'tests/screenshots/v130-path.png'});
 await nav('模拟赛').click();await page.getByRole('radio',{name:'简单',exact:true}).click();
 assert.equal(await page.getByRole('radio',{name:'简单',exact:true}).getAttribute('aria-checked'),'true');
 assert.equal(await page.getByText('计时与评测规则',{exact:true}).count(),0);
 const y=await page.locator('.difficulty-presets button').evaluateAll(nodes=>nodes.map(node=>node.getBoundingClientRect().y));assert(Math.max(...y)-Math.min(...y)<1);
 await page.getByRole('button',{name:'训练筛选',exact:true}).click();await page.getByRole('spinbutton',{name:'模拟赛最低难度',exact:true}).waitFor();await page.keyboard.press('Escape');
 await page.screenshot({path:'tests/screenshots/v130-training.png'});
 await nav('设置').click();await page.getByRole('tab',{name:'鸣谢',exact:true}).click();
 assert.equal(await page.locator('.acknowledgements p').count(),5);assert.equal(await page.locator('.acknowledgements p').last().innerText(),'jiahao27');
 await page.getByRole('button',{name:'全部设置',exact:false}).click();await page.getByRole('tab',{name:'账号与身份',exact:true}).click();await page.locator('.growth-account-panel').waitFor();
 await page.getByRole('button',{name:'全部设置',exact:false}).click();await page.getByRole('tab',{name:'外观',exact:true}).click();
 await page.getByRole('spinbutton',{name:'题解界面不透明度',exact:true}).fill('0');await page.getByRole('spinbutton',{name:'题解界面不透明度',exact:true}).blur();
 await page.locator('.background-playlist input[type=file]').setInputFiles({name:'animated.gif',mimeType:'image/gif',buffer:Buffer.from('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7','base64')});
 await page.locator('.playlist-images img').waitFor();assert((await page.locator('.playlist-images img').getAttribute('src')).startsWith('blob:'));
 await page.getByRole('button',{name:'全部设置',exact:false}).click();
 for(const width of [1280,1600,2048]){await page.setViewportSize({width,height:900});await checkOverflow();const tiles=await page.locator('.settings-home-grid [role=tab]').evaluateAll(nodes=>nodes.map(node=>({width:node.clientWidth,height:node.clientHeight})));assert(tiles.every(tile=>tile.width>130&&tile.height>=100));}
 await page.screenshot({path:'tests/screenshots/v130-settings.png'});
 await nav('题库').click();assert.equal(await page.getByLabel('逐层浏览题库',{exact:true}).count(),0);
 const classifications=await page.evaluate(async()=>{const {matchesShelf}=await import('/src/lib/contestShelves.js');const row={platform:'Codeforces',series:'XCPC',contest:'ICPC 2025 区域赛'};return [matchesShelf(row,'Codeforces'),matchesShelf(row,'xcpc')];});assert.deepEqual(classifications,[true,true]);
 await page.locator('.problem-table tr[data-id] .problem-title').first().click();await page.locator('.cm-editor').waitFor();
 await page.getByRole('combobox',{name:'编程语言',exact:true}).selectOption('python3');await page.getByRole('textbox',{name:'Python 代码',exact:true}).waitFor();
 await page.screenshot({path:'tests/screenshots/v130-python.png'});
 const flameSizes=await page.evaluate(async()=>{
   const reactModule=await import('/node_modules/.vite/deps/react.js'),React=reactModule.default||reactModule,clientModule=await import('/node_modules/.vite/deps/react-dom_client.js'),{createRoot}=clientModule.default||clientModule,{default:Flame}=await import('/src/components/PracticeStreak.jsx');
   const host=document.createElement('div');host.id='flame-sizes';document.body.append(host);const root=createRoot(host);root.render(React.createElement('div',{},...[1,2,4,7,15,30,60,120].map(days=>React.createElement(Flame,{key:days,days}))));
   await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));const sizes=[...host.querySelectorAll('svg')].map(node=>getComputedStyle(node).height);root.unmount();host.remove();return sizes.map(parseFloat);
 });
 assert.equal(flameSizes.length,8);for(let index=1;index<7;index++)assert(flameSizes[index]>flameSizes[index-1]);assert.equal(flameSizes[6],flameSizes[7]);
 assert.deepEqual(errors,[]);console.log('PASS: v1.3.0 unified UI, filters, radar drilldown, contest rows, learning paths, training, thanks, animation uploads, alignment, Python editor');
} catch(error) {await page.screenshot({path:'tests/screenshots/v130-failure.png'}).catch(()=>{});throw error;}
finally {await browser.close();await vite.close();}
