import assert from 'node:assert/strict';
import { createServer } from 'vite';
import { chromium } from 'playwright';

// Actual AccountGate and HTTP client; synthetic route responses only. No real
// password, production account, submission, or persistent personal workspace.
const server = await createServer({server:{host:'127.0.0.1',port:0}});
await server.listen();
const base=server.resolvedUrls.local[0];
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const report={singleSend:true,pendingGate:true,retryWithoutPassword:true,lateReplyIgnored:true,uncertainRegistration:true};
try {
  for(const scenario of ['pending','late','uncertain','quiet-sync']) {
    const page=await browser.newPage(),errors=[],posts=[];
    let ready=scenario==='quiet-sync',restore=false,release,entered;
    let sync={status:'error',pending:true,recoverable:true,attention:'',error:'isolated network outage'};
    const gate=new Promise(resolve=>{release=resolve;}),started=new Promise(resolve=>{entered=resolve;});
    page.on('pageerror',issue=>errors.push(issue.message));
    await page.addInitScript(()=>{window.attentionEvents=[];window.addEventListener('tb:account-sync-attention',event=>window.attentionEvents.push(event.detail));});
    if(scenario==='uncertain')await page.clock.install();
    const account=()=>({required:true,authenticated:ready,restoring:restore,token:'isolated-local-token',
      account:ready?{userId:'isolated-user',loginId:'isolated_user',nickname:'Synthetic'}:null,sync,
      error:!ready&&!restore&&posts.some(item=>item.path.endsWith('/login'))?'登录验证已完成，学习记录尚未同步；请重新连接，本机数据已保留':''});
    await page.route(/\/api\//,async route=>{
      const req=route.request(),url=new URL(req.url()),path=url.pathname;
      if(!path.startsWith('/api/'))return route.continue();
      if(req.method()==='POST')posts.push({path,body:req.postDataJSON()});
      if(path==='/api/account') {
        if(url.searchParams.get('retry')==='1')restore=true;
        return route.fulfill({json:account()});
      }
      if(path==='/api/software-update')return route.fulfill({json:{status:'idle',currentVersion:'1.4.30',autoCheck:false,canInstall:false}});
      if(path==='/api/account/register') {
        if(scenario==='uncertain') { entered();await gate;return route.fulfill({json:{registered:true,loginId:'isolated_user'}}).catch(()=>{}); }
        return route.fulfill({json:{registered:true,loginId:'isolated_user'}});
      }
      if(path==='/api/account/login') {
        if(scenario==='late') { entered();await gate;return route.fulfill({json:{...account(),authenticated:true,account:{userId:'stale-owner',loginId:'isolated_user'}}}); }
        return route.fulfill({json:account()});
      }
      throw new Error(`Unexpected isolated API: ${path}`);
    });
    try {
      await page.goto(base+'tests/auth-recovery-fixture.html');
      if(scenario==='quiet-sync') {
        await page.getByTestId('unlocked-workspace').waitFor();
        const draft=page.getByLabel('Isolated draft');await draft.fill('unfinished local draft');await draft.focus();
        assert.equal(await page.locator('.account-sync-alert').count(),0);
        assert.equal(await page.getByRole('button',{name:'重试同步',exact:true}).count(),0);
        assert.deepEqual(await page.evaluate(()=>window.attentionEvents),[]);
        sync={...sync,recoverable:false,attention:'recovery',error:'isolated checksum mismatch'};
        for(let i=0;i<2;i++) { await page.evaluate(()=>window.dispatchEvent(new Event('focus')));await page.waitForTimeout(100); }
        assert.equal((await page.evaluate(()=>window.attentionEvents)).length,1,'Necessary state is announced once');
        assert.equal(await draft.inputValue(),'unfinished local draft');
        assert.equal(await draft.evaluate(node=>document.activeElement===node),true);
        assert.equal(posts.length,0,'Polling never starts a manual sync POST or interrupts editing');
        assert.deepEqual(errors,[]);
        continue;
      }
      await page.getByRole('heading',{name:'登录 ToBe',exact:true}).waitFor();
      if(scenario!=='late') {
        await page.getByRole('tab',{name:'注册',exact:true}).click();
        await page.getByLabel('昵称',{exact:true}).fill('Synthetic');
      }
      await page.getByLabel('登录号',{exact:true}).fill('isolated_user');
      assert.equal(await page.getByLabel('密码',{exact:true}).getAttribute('minlength'),scenario==='late'?'6':'8');
      await page.getByLabel('密码',{exact:true}).fill(scenario==='late'?'123456':'isolated-password');
      if(scenario!=='late')await page.getByLabel('确认密码',{exact:true}).fill('isolated-password');
      // Two same-tick submit events must still send one password request.
      await page.locator('form').evaluate(form=>{form.requestSubmit();form.requestSubmit();});
      if(scenario==='pending') {
        await page.getByRole('alert').filter({hasText:'学习记录尚未同步'}).waitFor();
        assert.equal(await page.getByTestId('unlocked-workspace').count(),0);
        assert.equal(await page.getByLabel('密码',{exact:true}).inputValue(),'');
        assert.equal(posts.filter(item=>item.path.endsWith('/register')).length,1);
        assert.equal(posts.filter(item=>item.path.endsWith('/login')).length,1);
        await page.getByRole('button',{name:'重新连接',exact:true}).click();
        await page.getByLabel('ToBe 启动',{exact:true}).waitFor();
        assert.equal(await page.getByTestId('unlocked-workspace').count(),0);
        ready=true;restore=false;
        await page.getByTestId('unlocked-workspace').waitFor();
        assert.equal(posts.filter(item=>item.path.endsWith('/login')).length,1,'Reconnect never repeats the password POST');
      } else if(scenario==='late') {
        await started;
        await page.evaluate(()=>window.dispatchEvent(new Event('tb:account-change')));
        release();await page.getByRole('heading',{name:'登录 ToBe',exact:true}).waitFor();
        await page.waitForTimeout(250);
        assert.equal(await page.getByTestId('unlocked-workspace').count(),0,'A superseded response cannot unlock the old account');
        assert.notEqual(await page.evaluate(()=>window.__tbAccountUserId),'stale-owner');
        assert.equal(posts.length,1);
        assert.equal(posts[0].body.password,'123456','A valid existing reset credential reaches the login API');
      } else {
        await started;await page.clock.fastForward(15100);
        await page.getByRole('alert').filter({hasText:'尚未收到注册结果'}).waitFor();
        assert.equal(posts.length,1,'Unknown registration results never replay register or auto-login');
        assert.equal(await page.getByTestId('unlocked-workspace').count(),0);
        release();
      }
      const storage=await page.evaluate(()=>JSON.stringify({local:{...localStorage},session:{...sessionStorage}}));
      assert(!storage.includes('isolated-password'));
      assert.deepEqual(errors,[]);
    } finally { release();await page.close(); }
  }
  console.log(JSON.stringify({ok:true,...report,productionAuthRequests:0}));
} finally { await browser.close();await server.close(); }
