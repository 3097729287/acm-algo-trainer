import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {mkdir,mkdtemp,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
import {startFixture} from '../../server/leaderboard/tests/local-server.mjs';
import {openSettings} from './settings-navigation.mjs';
import {availablePages} from '../src/lib/featureUnlocks.js';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const out=path.join(root,'.backups/next-150/admin-workspace-ui');await mkdir(out,{recursive:true});
const state=await mkdtemp(path.join(out,'state-')),fixture=await startFixture();
async function cloud(pathname,body){const response=await fetch(fixture.endpoint+pathname,{method:'POST',headers:{'Content-Type':'application/json','X-TB-State-Protocol':'1','X-TB-Chunk-Protocol':'2'},body:JSON.stringify(body)});assert.equal(response.status,pathname.endsWith('/register')?201:200,await response.clone().text());return response.json();}
const password='isolated-admin-password';
const administrator=await cloud('/v1/accounts/register',{loginId:'admin',nickname:'Admin fixture',password});
fixture.STORE.database.prepare('INSERT INTO ranking_admins VALUES(?,?)').run(administrator.account?.userId||administrator.userId,new Date().toISOString());
const target=await cloud('/v1/accounts/register',{loginId:'ui_delete_target',nickname:'Synthetic target',password});
const env={...process.env,TB_OFFLINE:'1',TB_STATE_DIR:state,TB_UI_DIST:process.env.TB_UI_DIST||path.join(root,'frontend/dist'),PYTHONIOENCODING:'utf-8'};
const child=spawn(process.env.TB_TEST_PYTHON||'python',[path.join(root,'frontend/tests/admin-server.py'),fixture.endpoint],{env,windowsHide:true,stdio:['pipe','pipe','pipe']});
let stderr='',browser,page,phase='backend';child.stderr.on('data',value=>stderr+=value);
const errors=[],external=[],report={ok:false,realOfficialSubmissionsSent:0,productionAccountOperations:0};
try{
 const probe=await new Promise((resolve,reject)=>{let line='';const timeout=setTimeout(()=>reject(Error('Admin server timeout: '+stderr)),30000);child.stdout.on('data',chunk=>{line+=chunk;if(line.includes('\n')){clearTimeout(timeout);resolve(JSON.parse(line.split('\n')[0]));}});child.once('exit',code=>{clearTimeout(timeout);reject(Error('Admin server exit '+code+' '+stderr));});});
 const base=probe.baseUrl;assert.notEqual(new URL(base).port,'18766');
 browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});page=await browser.newPage({viewport:{width:1440,height:1000}});page.setDefaultTimeout(15000);page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/*',route=>{const url=new URL(route.request().url());if(url.hostname==='127.0.0.1'||['data:','blob:'].includes(url.protocol))return route.continue();external.push(url.origin+url.pathname);return route.abort();});
 const get=async endpoint=>{const response=await page.request.get(base+'/api/'+endpoint);assert.equal(response.status(),200,await response.text());return response.json();};
 phase='complete-navigation';await page.goto(base);await page.getByRole('navigation',{name:'主导航'}).getByRole('button',{name:'成长',exact:true}).waitFor();
 assert.equal(await page.locator('.navigation-pending').count(),0);const account=await get('account');assert.equal((await get('insights')).growth.authority.owner,account.account.userId);
 await openSettings(page,'管理员');await page.getByLabel('管理员等级',{exact:true}).fill('7');await page.waitForFunction(()=>JSON.parse(localStorage.getItem('tb.navigation-level.v1.'+window.__tbAccountUserId)||'null')?.level===7);
 assert.equal((await get('insights')).growth.level,7);await page.getByLabel('管理员等级',{exact:true}).fill('100');await page.waitForTimeout(150);
 phase='synthetic-account-management';await page.getByLabel('admin 密码',{exact:true}).fill(password);await page.getByRole('button',{name:'登录管理账号'}).click();await page.getByRole('region',{name:'账号维护'}).waitFor();
 await page.getByRole('textbox',{name:'查找账号',exact:true}).fill('ui_delete_target');await page.getByRole('button',{name:'查找账号',exact:true}).click();await page.getByRole('button',{name:'删除账号 ui_delete_target'}).click();await page.getByRole('textbox',{name:'确认操作的登录号'}).fill('ui_delete_target');await page.getByRole('button',{name:'确认删除',exact:true}).click();await page.getByText('账号已删除',{exact:true}).waitFor();
 assert.equal(fixture.STORE.database.prepare('SELECT COUNT(*) AS n FROM accounts WHERE login_id=?').get('ui_delete_target').n,0);
 phase='fresh-private-scenario';await page.getByRole('button',{name:'重置为新注册状态',exact:true}).click();await page.getByRole('alertdialog',{name:'测试工作区操作确认'}).getByRole('button',{name:'确认',exact:true}).click();
 await page.waitForFunction(owner=>window.__tbAccountUserId&&window.__tbAccountUserId!==owner,account.account.userId);
 await page.waitForFunction(count=>document.querySelectorAll('.sidebar nav .nav-item').length===count,availablePages(1).filter(id=>id!=='settings').length);
 assert.equal((await get('workspace')).summary.total,0);assert.equal((await get('insights')).growth.level,1);const scenario=(await get('account')).scenario;assert.equal(scenario.kind,'fresh');
 const prompt=page.getByRole('dialog',{name:'你有编程经验吗？'});await prompt.waitFor();await prompt.getByRole('button',{name:/我是新手/}).click();
 const guide=page.getByRole('dialog',{name:'新手指引',exact:true});await guide.waitFor();await guide.getByRole('button',{name:'结束指引 ×',exact:true}).click();await guide.waitFor({state:'hidden'});
 await openSettings(page,'管理员');await page.getByLabel('管理员等级',{exact:true}).fill('2');await page.waitForTimeout(350);assert.equal((await get('insights')).growth.level,2);
 phase='visual-alignment';for(const width of [1440,960,430]){await page.setViewportSize({width,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:path.join(out,'admin-'+width+'.png'),fullPage:true});}
 phase='restore-maintenance';await page.getByLabel('测试工作区',{exact:true}).selectOption('maintenance');await page.waitForFunction(owner=>window.__tbAccountUserId===owner,account.account.userId);assert.equal((await get('workspace')).summary.total,1);
 const original=await get('problem?id=fixture%3A%3AA');assert.equal(original.draft,'private maintenance draft');assert.equal((await get('account')).scenario.active,'maintenance');
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);Object.assign(report,{ok:true,identityAuthorityMatches:true,navigationHydrates:true,manualLevel:true,syntheticAccountDeletion:true,freshScenario:true,normalBeginnerChoice:true,scenarioLevel:true,maintenanceDraftPreserved:true,widths:[1440,960,430]});
}catch(error){report.failure=error.stack;report.phase=phase;if(page)await page.screenshot({path:path.join(out,'failure.png'),fullPage:true}).catch(()=>{});throw error;}
finally{await writeFile(path.join(out,'report.json'),JSON.stringify({...report,errors,external,serverErrors:stderr},null,2)+'\n');if(browser)await browser.close();const stopped=once(child,'exit');child.stdin.end('stop\n');await stopped;await fixture.close();}
console.log(JSON.stringify(report));
