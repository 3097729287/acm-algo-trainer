// Reuse the existing full-App offline API fixture, with a smaller action set.
import {mkdir,readFile,realpath,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {isAbsolute,relative,sep} from 'node:path';
const caseUrl=new URL('../.backups/shortcut-fullapp-'+Date.now()+'/',import.meta.url);
await mkdir(caseUrl,{recursive:true});await mkdir(new URL('temp/',caseUrl));
process.env.TEMP=process.env.TMP=fileURLToPath(new URL('temp/',caseUrl));
if(process.env.TB_SHORTCUT_SOURCE==='1')delete process.env.TB_UI_DIST;
else process.env.TB_UI_DIST||=fileURLToPath(new URL('../dist/',import.meta.url));
const original=new URL('./app.mjs',import.meta.url),source=await readFile(original,'utf8');
const split=source.indexOf('\ntry {\n');if(split<0)throw new Error('Existing App fixture boundary changed');
let prefix=source.slice(0,split);
if(process.env.TB_SHORTCUT_PROFILE){
 const root=await realpath(new URL('../../.backups/',import.meta.url)),profile=await realpath(process.env.TB_SHORTCUT_PROFILE),within=relative(root,profile);
 if(isAbsolute(within)||within.startsWith('..'+sep)||!/^deepseek-ui-\d+[\\/]profile$/.test(within))throw new Error('Only this worktree owned anonymous UI fixture profile may be reused');
 const originalLaunch="const browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });\nconst page = await browser.newPage({ viewport: { width: 2048, height: 1152 } });";
 if(!prefix.includes(originalLaunch))throw new Error('Existing App browser fixture changed');
 prefix=prefix.replace(originalLaunch,"const shortcutContext=await chromium.launchPersistentContext("+JSON.stringify(profile)+",{channel:'msedge',headless:true,viewport:{width:2048,height:1152}});const browser={close:()=>shortcutContext.close()};const page=shortcutContext.pages()[0];");
}
prefix=prefix.replace("createServer({ cacheDir:","createServer({ optimizeDeps:{entries:['index.html']},cacheDir:");
for(const name of ['settings-navigation.mjs','mock-mode-selection.mjs'])prefix=prefix.replaceAll("'./"+name+"'",JSON.stringify(new URL('./'+name,original).href));
prefix=prefix.replaceAll('import.meta.url',JSON.stringify(original.href));
prefix=prefix.replace("theme: 'light', fontSize: 18,","theme: 'light', fontSize: 18, shortcuts:{'workbench-next':'Ctrl+J'},");
prefix=prefix.replace("account: null };","account: {userId:profile.userId,nickname:profile.nickname,loginId:'isolated-shortcut'},usesOriginalWorkspace:true };");
prefix=prefix.replace("else if(path==='/api/contest-calendar')", "else if(path==='/api/preferences') {if(body?.preferences)Object.assign(shortcutPreferences,body.preferences);value={preferences:shortcutPreferences};}\n  else if(path==='/api/contest-calendar')");
prefix=prefix.replace("else throw new Error('Unhandled fixture request: ' + path);","else { fixtureUnsupportedPaths.add(path); value={available:false}; }");
prefix="const fixtureUnsupportedPaths=new Set(),shortcutPreferences={theme:'light',fontSize:18,shortcuts:{'workbench-next':'Ctrl+J'},onboardingCompleted:true,onboardingGuideVersion:999,levelNoticeVersion:1,levelNoticeSeen:100,levelNoticePending:0,onboardingUnlockedPages:['mine','library','templates','paths','competitions','mock','records','growth','activity','lectures']};\n"+prefix;
const checks=`
const consoleErrors=[];page.on('console',message=>{if(message.type()==='error')consoleErrors.push(message.text());});
const report={ok:false,actualFullApp:true,allApiExplicitlyMocked:true,nativeApiUnavailableInThisProbe:true,productionOrOjRequests:false,consoleErrors};
Object.assign(insights.growth,{level:100,confirmed:true,authority:{owner:profile.userId,epoch:'isolated-shortcut-fixture',revision:1}});
await page.route('**/*',route=>new URL(route.request().url()).hostname==='127.0.0.1'?route.fallback():route.abort('blockedbyclient'));
await page.route('**/api/desktop/deepseek**',route=>route.fulfill({json:{available:false,status:'unavailable'}}));
try{
 bootstrap.enabled=false;releaseBootstrap();await page.goto('http://127.0.0.1:18775');await page.locator('.problem-table').waitFor();await page.getByRole('tab',{name:'题库',exact:true}).first().waitFor();
 await page.keyboard.press('Control+1');await page.locator('[data-page="mine"] .problem-table:visible').waitFor();
 await page.locator('tr[data-id="'+rows[1].id+'"]:visible').first().click();
 const editor=()=>page.locator('.study-pane:not([hidden]) .cm-content');await editor().waitFor();
 await page.waitForFunction(()=>document.querySelector('.study-pane:not([hidden]) .wb-next-button')?.title.includes('Ctrl+J'));
 await editor().fill('int main(){return 17;} // isolated saved source');
 const font=page.locator('.study-pane:not([hidden]) input[aria-label="题面字号"]');await font.focus();
 const id=()=>page.locator('.study-pane:not([hidden]) .tb-workbench').getAttribute('data-problem-id');
 await page.keyboard.press('Control+ArrowRight');await page.waitForTimeout(120);assert.equal(await id(),rows[1].id,'Account override removes the default binding');
 await page.keyboard.press('Control+J');await page.waitForFunction(id=>{const next=document.querySelector('.study-pane:not([hidden]) .tb-workbench')?.dataset.problemId;return next&&next!==id;},rows[1].id);await editor().waitFor();
 const nextId=await id();assert(rows.some(row=>row.id===nextId));
 assert(writes.some(item=>item.path==='/api/draft'&&item.body.id===rows[1].id&&item.body.code.includes('isolated saved source')));
 await editor().fill('// global shortcut draft');await editor().focus();await page.keyboard.press('Control+K');
 const dialog=page.getByRole('dialog',{name:'快捷操作',exact:true});await dialog.waitFor();assert(await dialog.evaluate(node=>!node.closest('[inert]')));
 await dialog.locator('input').first().fill('isolated');assert(await dialog.locator('input').first().evaluate(node=>node===document.activeElement));
 await page.keyboard.press('Escape');await dialog.waitFor({state:'hidden'});assert.equal(await id(),nextId);
 await editor().focus();const before=await page.evaluate(()=>document.activeElement?.className);await page.keyboard.press('F6');
 assert(await page.evaluate(before=>document.activeElement?.className!==before&&!!document.activeElement?.closest('.study-browser'),before));
 await font.focus();const collapsed=await page.locator('.app-shell').evaluate(node=>node.classList.contains('sidebar-collapsed'));
 await page.keyboard.press('Control+B');await page.waitForFunction(value=>document.querySelector('.app-shell').classList.contains('sidebar-collapsed')!==value,collapsed);
 await editor().focus();await page.keyboard.press('Control+F');await page.getByRole('combobox',{name:'搜索学习内容'}).waitFor();await page.keyboard.press('Escape');
 await editor().waitFor();assert((await editor().innerText()).includes('global shortcut draft'));
 await page.keyboard.press('Control+2');await page.waitForFunction(()=>!document.querySelector('.study-browser'));assert.equal(await page.locator('.app-shell').evaluate(node=>node.inert),false);
 assert.deepEqual(errors,[]);await page.screenshot({path:${JSON.stringify(fileURLToPath(new URL('full-app.png',caseUrl)))},animations:'disabled'});
 Object.assign(report,{ok:true,customBindingHonoredFromInput:true,defaultBindingNotHijacked:true,savedBeforeNext:true,globalCommandDialogAccessibleAboveInertStudyShell:true,focusRegionsStayInActiveStudy:true,sidebarBindingFromEditorContext:true,studySearchFromEditor:true,navigationFromAnyFocus:true,errors,fixtureUnsupportedPaths:[...fixtureUnsupportedPaths]});
}catch(error){Object.assign(report,{errorClass:error.name,error:error.message,errors,fixtureUnsupportedPaths:[...fixtureUnsupportedPaths]});await page.screenshot({path:${JSON.stringify(fileURLToPath(new URL('failure.png',caseUrl)))}});throw error;}
finally{await (await import('node:fs/promises')).writeFile(${JSON.stringify(fileURLToPath(new URL('result.json',caseUrl)))},JSON.stringify(report,null,2));console.log(JSON.stringify({...report,receipt:${JSON.stringify(fileURLToPath(new URL('result.json',caseUrl)))}}));releaseBootstrap();await browser.close();await vite.close();}
`;
const generated=new URL('probe.mjs',caseUrl);await writeFile(generated,prefix+checks);
await import(generated.href);
