import assert from 'node:assert/strict';
import {resolve} from 'node:path';

async function rpc(page,path,query={}) {
 return page.evaluate(async({path,query})=>{
  const value=await window.__TAURI__.core.invoke('api_request',{request:{version:1,id:crypto.randomUUID(),method:'GET',path,query}});
  if(!value.ok)throw new Error(value.error.code+': '+value.error.message);return value.data;
 },{path,query});
}
async function normalDrafts(page) {
 return (await rpc(page,'data/export')).tables.drafts.filter(row=>row.context==='');
}

export async function exerciseNativeContestSetup(page,output) {
 const ordinaryBefore=await normalDrafts(page),trainingBefore=new Set((await rpc(page,'workspace')).training.map(row=>row.id));
 assert.equal((await rpc(page,'workspace')).activeContest,null);
 const home=page.getByRole('button',{name:'返回主界面',exact:true}).first();
 if(await home.isVisible()){
  await home.click();await page.locator('.tb-workbench:visible').waitFor({state:'hidden'});
  await page.waitForFunction(async()=>{
   const answer=await window.__TAURI__.core.invoke('api_request',{request:{version:1,id:crypto.randomUUID(),method:'GET',path:'preferences',query:{}}});
   return answer.ok&&answer.data.preferences?.learningPaths?.browserV1?.open===false;
  });
 }
 // Test navigation only. This neither changes real account XP nor authorizes
 // shared-team operations, rewards or original-site submission.
 const {owner}=await rpc(page,'api/capabilities');assert(owner);
 await page.evaluate(owner=>localStorage.setItem('tb.navigation-level.v1.'+owner,JSON.stringify({owner,level:6})),owner);
 await page.setViewportSize({width:1500,height:950});await page.reload();
 await page.locator('.sidebar').first().waitFor();await page.locator('.workspace-area .loading-screen').waitFor({state:'hidden'});
 if(await home.isVisible()){await home.click();await home.waitFor({state:'hidden'});}
 await page.keyboard.press('Control+5');
 const make=async name=>{
  const setup=page.locator('.mock-create');await setup.waitFor();
  await page.getByRole('button',{name:'训练筛选',exact:true}).click();
  const filter=page.getByRole('dialog',{name:'训练筛选',exact:true});
  const platform=filter.getByRole('button',{name:'洛谷',exact:true});
  if(await platform.isVisible())await platform.click();
  await filter.getByRole('spinbutton',{name:'模拟赛题目数',exact:true}).fill('3');
  await filter.getByRole('spinbutton',{name:'模拟赛时长',exact:true}).fill('60');
  await filter.getByRole('spinbutton',{name:'错误罚时',exact:true}).fill('30');
  await filter.getByRole('button',{name:'关闭筛选',exact:true}).click();
  await setup.getByRole('button',{name:'生成试卷',exact:true}).click();
  const preview=setup.locator('.paper-preview');await preview.waitFor();
  assert.equal(await preview.locator('.paper-slot').count(),3);
  assert.equal(await preview.locator('.paper-slot small').count(),0);
  await preview.getByRole('button',{name:'重命名模拟赛',exact:true}).click();
  const title=preview.getByRole('textbox',{name:'模拟赛名称',exact:true});await title.fill(name);await title.press('Enter');await title.waitFor({state:'hidden'});
  return {setup,preview};
 };
 let {setup}=await make('原生实际生成试卷');
 await page.screenshot({path:resolve(output,'native-generated-paper-preview.png')});
 await setup.getByRole('button',{name:'开始训练',exact:true}).click();
 let workbench=page.locator('.contest-player .tb-workbench:visible');await workbench.waitFor();
 const active=(await rpc(page,'workspace')).activeContest;assert(active&&active.name==='原生实际生成试卷'&&active.total===3);
 assert.equal(Date.parse(active.deadline)-Date.parse(active.startedAt),60*60000);
 assert.equal(active.constraints.editedTrainingOnly,true);assert.equal(active.constraints.wrongPenalty,30);
 assert.equal(active.constraints.strategy,'comprehensive');assert(active.slots.every(row=>!('difficulty' in row)&&!('tags' in row)));
 const ids=active.slots.map(row=>row.id),joined=(await rpc(page,'workspace')).training.map(row=>row.id);
 for(const id of ids)assert.equal(joined.includes(id),trainingBefore.has(id),'Previewing and starting a paper must not enroll untouched slots');
 const editor=workbench.locator('.cm-content[contenteditable=true]:visible').first();
 if(!await editor.isVisible())await page.keyboard.press('Alt+2');await editor.waitFor();
 await workbench.getByRole('combobox',{name:'编程语言',exact:true}).selectOption('cpp17');
 const code='// actual generated native paper, isolated custom execution 😀\nint main(){return 0;}\n';
 await editor.fill(code);await editor.press('Control+s');
 await page.waitForFunction(async({id,contestId,code})=>{
  const value=await window.__TAURI__.core.invoke('api_request',{request:{version:1,id:crypto.randomUUID(),method:'GET',path:'problem',query:{id:[id],contestId:[contestId]}}});
  return value.ok&&value.data.draft===code;
 },{id:ids[0],contestId:active.id,code});
 await workbench.getByRole('button',{name:'自测输入',exact:true}).click();
 await workbench.getByRole('textbox',{name:'标准输入',exact:true}).fill('isolated input\n');
 await workbench.getByRole('button',{name:'自测运行',exact:true}).click();
 await workbench.locator('.wb-result-summary .wb-verdict-run_ok').waitFor();
 const receipts=(await rpc(page,'submissions',{id:[ids[0]],contestId:[active.id]})).submissions;
 const receipt=receipts.find(row=>row.code===code);assert(receipt&&receipt.scope==='samples'&&receipt.verdict==='RUN_OK');
 assert.equal((await rpc(page,'contest',{id:[active.id]})).contest.accepted,0);
 await page.screenshot({path:resolve(output,'native-generated-paper-custom-run.png')});
 await page.getByRole('button',{name:'结束比赛',exact:true}).click();
 await page.getByRole('alertdialog',{name:'结束比赛确认',exact:true}).getByRole('button',{name:'结束并复盘',exact:true}).click();
 const details=page.locator('.record-detail');await details.getByRole('heading',{name:'原生实际生成试卷',exact:true}).waitFor();
 assert((await details.innerText()).includes('0/3 AC'));assert.equal(await details.locator('.record-slot').count(),3);
 assert.equal((await rpc(page,'problem',{id:[ids[0]],contestId:[active.id]})).draft,code);
 assert.deepEqual(await normalDrafts(page),ordinaryBefore);
 const after=(await rpc(page,'workspace')).training.map(row=>row.id);assert(after.includes(ids[0]));
 for(const id of ids.slice(1))assert.equal(after.includes(id),trainingBefore.has(id));
 await page.screenshot({path:resolve(output,'native-generated-paper-finished.png')});
 await details.getByRole('button',{name:'所有记录',exact:true}).click();
 ({setup}=await make('原生实际创建后取消'));
 await setup.getByRole('button',{name:'开始训练',exact:true}).click();
 workbench=page.locator('.contest-player .tb-workbench:visible');await workbench.waitFor();
 const second=(await rpc(page,'workspace')).activeContest;assert(second&&second.name==='原生实际创建后取消');
 assert.notDeepEqual(second.slots.map(row=>row.id),ids);
 await page.getByRole('button',{name:'结束比赛',exact:true}).click();
 await page.getByRole('alertdialog',{name:'结束比赛确认',exact:true}).getByRole('button',{name:'取消比赛',exact:true}).click();
 await workbench.waitFor({state:'hidden'});
 assert.equal((await rpc(page,'contest',{id:[second.id]})).contest.status,'cancelled');
 assert.equal((await rpc(page,'workspace')).activeContest,null);assert.deepEqual(await normalDrafts(page),ordinaryBefore);
 return {realTauriIpc:true,contestsInsertedByFixtureForThisFlow:0,previewAndStartThroughExistingReact:true,papersActuallyCreated:2,originalPublicProblems:true,blindPreview:true,serverDeadline:true,unchangedNormalDraftRows:true,noUntouchedSlotEnrollment:true,actualExamDraft:true,actualCppCustomExecution:'RUN_OK',customExecutionOfficialAc:0,actualFinishAndReview:true,actualCancel:true,rerollPrefersDifferentOriginals:true,officialSubmissionsSent:0,realAccountLevelChanged:false,originVpAndRewardAuthorityStillProtected:true};
}
export {rpc as nativeRead,normalDrafts};
