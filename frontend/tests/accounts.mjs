import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdtemp,mkdir,readFile,writeFile,rm} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {once} from 'node:events';
import {chromium} from 'playwright';
import {startFixture} from '../../server/leaderboard/tests/local-server.mjs';

// Real account/API services, synthetic credentials, disposable state and browser.
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const folder=path.join(root,'.backups/registered-accounts');await mkdir(folder,{recursive:true});
const state=await mkdtemp(path.join(folder,'ui-state-')),service=await startFixture();
assert.equal(new URL(service.endpoint).hostname,'127.0.0.1');
const environment={...process.env,TB_OFFLINE:'1',TB_STATE_DIR:state,TB_PACKAGE_PORT:'0',
  TB_BACKUP_DIR:path.join(state,'backups'),TB_LIBRARY_DB:path.join(state,'tb-library.sqlite3'),
  TB_ARCHIVE_ROOT:path.join(state,'imports'),TB_TEST_ACCOUNTS_ENDPOINT:service.endpoint,PYTHONIOENCODING:'utf-8'};
const wait=milliseconds=>new Promise(resolve=>setTimeout(resolve,milliseconds));
let processHandle,browser,page,probe,base,serverErrors='',phase='startup';
const errors=[],external=[];

async function startApp(){
  if(process.env.TB_ACCOUNT_TEST_EXE){
    const report=path.join(state,'probe.json');
    await rm(report,{force:true});await rm(path.join(state,'probe.stop'),{force:true});
    processHandle=spawn(process.env.TB_ACCOUNT_TEST_EXE,['--serve-account-check',report],{env:environment,windowsHide:true});
    for(let i=0;i<300;i++){
      try{probe=JSON.parse(await readFile(report,'utf8'));break;}catch{}
      if(processHandle.exitCode!=null)throw new Error('Frozen account probe exited early');await wait(100);
    }
    assert(probe?.ok&&probe.frozen);
  }else{
    const python=process.env.TB_TEST_PYTHON||process.env.TB_PYTHON||(process.platform==='win32'?'python':'python3');
    processHandle=spawn(python,[path.join(root,'frontend/tests/accounts-server.py'),service.endpoint],
      {env:environment,windowsHide:true,stdio:['pipe','pipe','pipe']});
    processHandle.stderr.on('data',value=>{serverErrors+=value.toString();});
    probe=await new Promise((resolve,reject)=>{
      let line='';const timeout=setTimeout(()=>reject(new Error('Account UI server timed out: '+serverErrors)),30000);
      processHandle.stdout.on('data',value=>{line+=value.toString();if(line.includes('\n')){clearTimeout(timeout);resolve(JSON.parse(line.split('\n')[0]));}});
      processHandle.once('exit',code=>{clearTimeout(timeout);reject(new Error('Account UI server failed: '+code+' '+serverErrors));});
    });
  }
  base=probe.baseUrl;assert.equal(new URL(base).hostname,'127.0.0.1');assert.notEqual(new URL(base).port,'18765');
}
async function stopApp(){
  if(!processHandle||processHandle.exitCode!=null)return;
  const ended=once(processHandle,'exit');
  if(process.env.TB_ACCOUNT_TEST_EXE)await writeFile(path.join(state,'probe.stop'),'stop');
  else processHandle.stdin.end('stop\n');
  await Promise.race([ended,wait(15000)]);if(processHandle.exitCode==null){processHandle.kill();await ended;}
}

try{
  await startApp();
  browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
  page=await browser.newPage({viewport:{width:1440,height:1000}});page.setDefaultTimeout(15000);
  page.on('pageerror',issue=>errors.push(issue.message));
  await page.route('**/*',route=>{
    const url=new URL(route.request().url());
    if(url.hostname==='127.0.0.1'||['data:','blob:'].includes(url.protocol))return route.continue();
    external.push(url.origin+url.pathname);return route.abort();
  });
  const get=async name=>{const result=await page.request.get(base+'/api/'+name);assert.equal(result.status(),200,await result.text());return result.json();};
  const post=async(name,body)=>{const auth=await get('account');const result=await page.request.post(base+'/api/'+name,{data:body,headers:{'X-TB-Token':auth.token}});assert.equal(result.status(),200,await result.text());return result.json();};
  const loginPage=()=>page.getByRole('heading',{name:'登录 ToBe',exact:true});
  const guide=()=>page.getByRole('dialog',{name:'新手指引',exact:true});
  const nav=()=>page.getByRole('navigation',{name:'主导航'});
  const editor=()=>page.getByRole('textbox',{name:'C++ 代码',exact:true});
  const accountPanel=()=>page.locator('.account-panel');
  const openAccount=async()=>{await page.getByRole('button',{name:'训练概览',exact:true}).click();await accountPanel().waitFor();};
  const logout=async()=>{await openAccount();await accountPanel().getByRole('button',{name:'退出账号',exact:true}).click();await loginPage().waitFor();};
  const acknowledgeGuide=async()=>{
    await guide().waitFor();assert.match(await guide().innerText(),/Lv\.2.*Lv\.5/);
    await page.keyboard.press('Escape');await guide().waitFor({state:'detached'});
    for(let i=0;i<100;i++){const prefs=(await get('preferences')).preferences;if(prefs?.onboardingCompleted&&prefs.onboardingGuideVersion===2)return;await wait(50);}
    assert.fail('The account-owned current guide acknowledgement was not persisted');
  };
  const levelOne=async()=>{
    await page.waitForFunction(()=>[...document.querySelectorAll('.sidebar nav button')].map(node=>node.textContent).join('|')==='我的训练|题单|提交记录');
    assert.deepEqual(await nav().getByRole('button').allTextContents(),['我的训练','题单','提交记录']);
    assert.equal((await get('insights')).growth.level,1);
    assert.equal((await page.request.get(base+'/api/data')).status(),200,'Level gates affect UI navigation, not authenticated catalog APIs');
    assert.equal((await page.request.get(base+'/api/training-lists')).status(),200);
    assert.equal((await page.request.get(base+'/api/lectures')).status(),200);
    assert.equal(await page.getByRole('button',{name:'比赛日历',exact:true}).count(),0);
  };
  const logIn=async(loginId,password)=>{await page.getByLabel('登录号',{exact:true}).fill(loginId);await page.getByLabel('密码',{exact:true}).fill(password);await page.getByRole('button',{name:'登录',exact:true}).click();};
  const openTraining=async problemId=>{
    await nav().getByRole('button',{name:'我的训练',exact:true}).click();
    await page.locator(`tr[data-id=${JSON.stringify(problemId)}] .problem-title`).click();await editor().waitFor();
  };

  phase='registration-auto-login';await page.goto(base);await loginPage().waitFor();
  assert.equal(await page.locator('.nav-item').count(),0);assert.equal((await page.request.get(base+'/api/data')).status(),401);
  assert.equal(await page.getByText('忘记密码',{exact:true}).count(),0);const bootstrap=await get('account');
  await page.getByRole('tab',{name:'注册',exact:true}).click();
  await page.getByLabel('昵称',{exact:true}).fill('星河');await page.getByLabel('登录号',{exact:true}).fill('ui_account_a');
  await page.getByLabel('密码',{exact:true}).fill('fixture-password');await page.getByLabel('确认密码',{exact:true}).fill('incorrect-password');
  await page.getByRole('button',{name:'注册账号',exact:true}).click();await page.getByRole('alert').getByText('两次输入的密码不一致').waitFor();
  await page.getByLabel('确认密码',{exact:true}).fill('fixture-password');await page.getByRole('button',{name:'注册账号',exact:true}).click();
  await nav().waitFor();await guide().waitFor();await levelOne();
  assert.equal(await page.locator('.workspace-area').getAttribute('data-page'),'training-lists','Registration automatically signs in and opens the introductory list');
  await page.locator('.training-list-path').getByRole('button',{name:'01 编程基础',exact:true}).waitFor();await acknowledgeGuide();
  assert.equal(await loginPage().count(),0);
  const a=await get('account');assert.equal(a.account.nickname,'星河');assert.equal(a.usesOriginalWorkspace,true);
  const library=await get('data'),problemId=(library.rows.find(row=>row.id==='fixture::A')||library.rows.find(row=>row.id==='luogu-training-B2002')||library.rows[0]).id;
  assert.equal((await page.request.post(base+'/api/training/start',{data:{id:problemId},headers:{'X-TB-Token':bootstrap.token}})).status(),403,'A bootstrap token cannot act after login');
  await page.keyboard.press('Control+2');assert.equal(await page.locator('.workspace-area').getAttribute('data-page'),'training-lists','The locked library shortcut cannot bypass Lv1');

  phase='wrong-password-and-stale-poll';await logout();assert.equal((await page.request.get(base+'/api/workspace')).status(),401);
  await logIn('ui_account_a','incorrect-password');await page.getByRole('alert').getByText('登录号或密码错误',{exact:true}).waitFor();assert.equal((await get('account')).authenticated,false);
  const oldDeviceResponse=await page.request.post(service.endpoint+'/v1/accounts/login',{data:{loginId:'ui_account_a',password:'fixture-password'},headers:{'X-TB-State-Protocol':'1','X-TB-Chunk-Protocol':'2'}});
  assert.equal(oldDeviceResponse.status(),200);const oldDevice=await oldDeviceResponse.json();
  let releaseStale,staleReady,staleDone;const held=new Promise(resolve=>{releaseStale=resolve;}),captured=new Promise(resolve=>{staleReady=resolve;}),completed=new Promise(resolve=>{staleDone=resolve;});let capturedOnce=false;
  const staleAccount=async route=>{if(capturedOnce)return route.continue();capturedOnce=true;const response=await route.fetch();assert.equal((await response.json()).authenticated,false);staleReady();await held;await route.fulfill({response});staleDone();};
  await page.route(/\/api\/account(?:\?.*)?$/,staleAccount);
  try{await page.evaluate(()=>window.dispatchEvent(new Event('focus')));await captured;await logIn('ui_account_a','fixture-password');await nav().waitFor();}finally{releaseStale();}
  await completed;await page.unroute(/\/api\/account(?:\?.*)?$/,staleAccount);await wait(200);
  assert.equal((await get('account')).authenticated,true);await levelOne();assert.equal(await guide().count(),0,'An acknowledged guide does not repeat on login');
  assert.equal((await page.request.get(service.endpoint+'/v1/accounts/me',{headers:{'X-TB-User':oldDevice.account.userId,Authorization:'Bearer '+oldDevice.token}})).status(),401,'Signing in invalidates the old synthetic device session');

  phase='saved-login-loading-and-browser-draft';await post('training/start',{id:problemId});
  await page.evaluate(id=>localStorage.setItem(`tb.draft.v2.solo.${encodeURIComponent(id)}`,JSON.stringify({code:'old private browser draft',dirty:true,version:1,owner:'legacy',modifiedAt:Date.now()})),problemId);
  let restoreReadyAt=0,restoreRecognitionMs=null;
  const pendingRestore=async route=>{if(!restoreReadyAt)restoreReadyAt=Date.now()+1600;if(Date.now()<restoreReadyAt)return route.fulfill({json:{token:'restoring-fixture',authenticated:false,restoring:true}});restoreRecognitionMs??=Date.now()-restoreReadyAt;return route.continue();};
  await page.route(/\/api\/account(?:\?.*)?$/,pendingRestore);await page.reload();
  await page.getByRole('heading',{name:'正在加载 ToBe',exact:true}).waitFor();await page.getByText('正在恢复登录与学习记录…',{exact:true}).waitFor();
  assert.equal(await page.locator('.account-card,.account-form,.account-tabs,.nav-item').count(),0);
  await page.screenshot({path:path.join(state,'startup-loading.png'),animations:'disabled'});await nav().waitFor();await page.unroute(/\/api\/account(?:\?.*)?$/,pendingRestore);
  assert(restoreRecognitionMs!==null&&restoreRecognitionMs<1200,'Completed restore is shown promptly: '+restoreRecognitionMs);
  await openTraining(problemId);await page.waitForFunction(()=>document.querySelector('.cm-content')?.textContent.includes('old private browser draft'));
  assert((await editor().innerText()).includes('old private browser draft'));await page.getByRole('button',{name:'返回列表',exact:true}).click();
  assert.equal((await get('problem?id='+encodeURIComponent(problemId))).draft,'old private browser draft');

  phase='nickname-and-password';await openAccount();
  await accountPanel().getByLabel('用户昵称',{exact:true}).fill('新昵称');await accountPanel().getByRole('button',{name:'保存昵称',exact:true}).click();
  await accountPanel().getByLabel('已保存',{exact:true}).waitFor();assert.equal((await get('profile')).profile.displayName,'新昵称');
  await accountPanel().locator('.account-password-edit summary').click();
  await accountPanel().getByLabel('原密码',{exact:true}).fill('incorrect-password');await accountPanel().getByLabel('新密码',{exact:true}).fill('next-fixture-password');await accountPanel().getByLabel('确认新密码',{exact:true}).fill('different-password');
  await accountPanel().getByRole('button',{name:'保存新密码',exact:true}).click();await accountPanel().getByRole('alert').getByText('两次输入的新密码不一致',{exact:true}).waitFor();
  await accountPanel().getByLabel('确认新密码',{exact:true}).fill('next-fixture-password');await accountPanel().getByRole('button',{name:'保存新密码',exact:true}).click();await accountPanel().getByRole('alert').getByText('原密码错误',{exact:true}).waitFor();
  await accountPanel().getByLabel('原密码',{exact:true}).fill('fixture-password');await accountPanel().getByRole('button',{name:'保存新密码',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('.account-panel input[aria-label="原密码"]')?.value==='');await accountPanel().getByLabel('已保存',{exact:true}).waitFor();
  await accountPanel().getByRole('button',{name:'退出账号',exact:true}).click();await loginPage().waitFor();
  await logIn('ui_account_a','fixture-password');await page.getByRole('alert').getByText('登录号或密码错误',{exact:true}).waitFor();assert.equal((await get('account')).authenticated,false);

  phase='account-b-isolation';await post('account/register',{loginId:'ui_account_b',nickname:'另一个账号',password:'fixture-password'});
  assert.equal((await page.request.get(base+'/api/workspace')).status(),401,'Registration API alone does not authenticate');
  await logIn('ui_account_b','fixture-password');await nav().waitFor();
  const b=await get('account');assert.notEqual(b.account.userId,a.account.userId);
  const experience=page.getByRole('dialog',{name:'你有编程经验吗？',exact:true});await experience.waitFor();
  const offered=(await get('insights')).growth.experienceChallenge;
  assert.equal(offered.owner,b.account.userId);assert.equal(offered.eligible,true);assert.equal(offered.choice,null);
  assert.equal(await page.evaluate(()=>window.__tbAccountUserId),b.account.userId,'The experience choice belongs to the newly signed-in account');
  await experience.getByRole('button',{name:/我是新手/}).click();await experience.waitFor({state:'detached'});
  const chosen=(await get('insights')).growth.experienceChallenge;
  assert.equal(chosen.owner,b.account.userId);assert.equal(chosen.choice,'beginner');assert.equal(chosen.status,'beginner');assert.equal(chosen.promptRequired,false);assert.equal(chosen.allNavigationUnlocked,false);
  await acknowledgeGuide();await levelOne();
  assert.equal(b.usesOriginalWorkspace,false);assert.equal((await get('workspace')).summary.total,0);
  assert.equal((await page.request.post(base+'/api/draft',{data:{id:problemId,code:'must be rejected'},headers:{'X-TB-Token':a.token}})).status(),403,'An old local token cannot write another account draft');
  await post('training/start',{id:problemId});await page.reload();await nav().waitFor();await openTraining(problemId);
  await page.waitForFunction(()=>document.querySelector('.cm-content')?.getAttribute('contenteditable')==='true');assert(!(await editor().innerText()).includes('old private browser draft'));
  const bCode='// private B draft\nint main(){return 2;}';await editor().fill(bCode);await editor().press('Control+s');await page.getByRole('button',{name:'返回列表',exact:true}).click();
  assert.equal((await get('problem?id='+encodeURIComponent(problemId))).draft,bCode);await logout();
  await logIn('ui_account_a','next-fixture-password');await nav().waitFor();assert.equal(await guide().count(),0);
  assert.equal((await get('account')).account.userId,a.account.userId);assert.equal((await get('problem?id='+encodeURIComponent(problemId))).draft,'old private browser draft');assert.equal((await get('profile')).profile.displayName,'新昵称');

  phase='actual-backend-restart';await stopApp();await startApp();await page.goto(base);await nav().waitFor();await levelOne();
  assert.equal((await get('account')).account.userId,a.account.userId);assert.equal((await get('problem?id='+encodeURIComponent(problemId))).draft,'old private browser draft');
  assert.equal((await get('profile')).profile.displayName,'新昵称');assert.equal(await guide().count(),0,'An actual service restart does not repeat the acknowledged guide');
  await openTraining(problemId);assert.equal(await editor().innerText(),'old private browser draft');await page.getByRole('button',{name:'返回列表',exact:true}).click();await logout();
  assert.equal((await page.request.get(base+'/api/workspace')).status(),401);
  phase='mobile-login';await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=390));
  await page.screenshot({path:path.join(state,'login-mobile.png'),fullPage:true});assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
  console.log(JSON.stringify({ok:true,frozen:Boolean(probe.frozen),wholeAppLogin:true,registrationAutoLogin:true,newAccountFoundation:true,levelOneNavigation:true,authenticatedApisAvailable:true,onboarding:true,stalePollIgnored:true,oldDeviceSessionRejected:true,passwordChange:true,oldPasswordRejected:true,nicknameChange:true,accountIsolation:true,oldLocalTokenRejected:true,legacyBrowserDrafts:true,actualBackendRestart:true,restoreRecognitionMs,startupLoading:true,mobile:true,realAccountUsed:false,realOfficialSubmissionsSent:0,state}));
}catch(error){
  console.error(JSON.stringify({phase,errors,external,serverErrors,body:page?await page.locator('body').innerText():null}));
  if(page)await page.screenshot({path:path.join(state,'failure.png')}).catch(()=>{});throw error;
}finally{await browser?.close();await stopApp();await service.close();}
