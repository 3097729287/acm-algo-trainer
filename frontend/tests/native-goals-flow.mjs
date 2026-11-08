import assert from 'node:assert/strict';
import {resolve} from 'node:path';

// The ordinary React training table is the existing visible entry. Goal CRUD
// itself is checked through real native IPC because no retired editor is added
// back to the current task UI for this migration test.
export async function exerciseNativeGoals(page, output, ordinaryTitle) {
 const back=()=>page.getByRole('button',{name:'返回主界面',exact:true}).first();
 if(await back().isVisible())await back().click();
 await page.locator('.tb-workbench:visible').waitFor({state:'hidden'});
 const created=await page.evaluate(async()=>{
  const invoke=window.__TAURI__.core.invoke;
  const rpc=async(path,body)=>{
   const account=await invoke('api_request',{request:{version:1,id:crypto.randomUUID(),method:'GET',path:'account',query:{}}});
   const result=await invoke('api_request',{request:{version:1,id:crypto.randomUUID(),method:body===undefined?'GET':'POST',path,query:{},...(body===undefined?{}:{body,token:account.data.token})}});
   if(!result.ok)throw Error(result.error.code+': '+result.error.message);return result.data;
  };
  const deadline=new Date(Date.now()+32*3600000).toISOString().slice(0,10);
  const body={kind:'custom',deadline,totalProblems:4,dailyMinutes:90};
  await rpc('goals/save',{...body,title:'原生目标甲'});
  const second=await rpc('goals/save',{...body,title:'原生目标乙'});
  const workspace=await rpc('workspace');
  const task=workspace.goalTasks.find(task=>workspace.training.some(row=>row.id===task.id&&row.goalTask));
  if(!task)throw Error('Real goal allocation did not reach the ordinary training rows');
  return {ids:second.goals.map(goal=>goal.id),task,targets:second.goals.map(goal=>goal.dailyTask.target),taskIds:workspace.goalTasks.map(task=>task.id)};
 });
 assert.equal(created.ids.length,2);assert.equal(new Set(created.taskIds).size,created.taskIds.length);
 await page.reload();
 await page.locator('.sidebar').waitFor({state:'attached'});
 if(await back().isVisible())await back().click();
 await page.locator('.sidebar').getByRole('button',{name:'我的训练',exact:true}).click();
 const selected=page.locator('.problem-title').filter({hasText:created.task.title}).first();
 await selected.waitFor();await selected.click();
 const editor=page.getByRole('textbox',{name:'C++ 代码',exact:true});
 await page.locator('.tb-workbench:visible').waitFor();
 if(!await editor.isVisible())await page.keyboard.press('Alt+2');await editor.waitFor();
 const code='// Actual native goal task draft\nint main() { return 0; }\n';
 await editor.fill(code);await editor.press('Control+s');
 await page.waitForFunction(async({id,code})=>{
  const result=await window.__TAURI__.core.invoke('api_request',{request:{version:1,id:crypto.randomUUID(),method:'GET',path:'problem',query:{id:[id]}}});
  return result.ok&&result.data.draft===code;
 },{id:created.task.id,code});
 await page.screenshot({path:resolve(output,'native-goal-task.png')});
 await page.reload();await page.locator('.tb-workbench:visible').waitFor();
 if(!await editor.isVisible())await page.keyboard.press('Alt+2');
 await editor.waitFor();assert.equal((await editor.innerText()).trimEnd(),code.trimEnd());
 const archived=await page.evaluate(async({ids,id})=>{
  const invoke=window.__TAURI__.core.invoke;
  const account=await invoke('api_request',{request:{version:1,id:crypto.randomUUID(),method:'GET',path:'account',query:{}}});
  for(const goal of ids){const result=await invoke('api_request',{request:{version:1,id:crypto.randomUUID(),method:'POST',path:'goals/archive',query:{},body:{id:goal},token:account.data.token}});if(!result.ok)throw Error(result.error.message);}
  const goals=await invoke('api_request',{request:{version:1,id:crypto.randomUUID(),method:'GET',path:'goals',query:{}}});
  const problem=await invoke('api_request',{request:{version:1,id:crypto.randomUUID(),method:'GET',path:'problem',query:{id:[id]}}});
  return {active:goals.data.goals.length,draft:problem.data.draft};
 },{ids:created.ids,id:created.task.id});
 assert.equal(archived.active,0);assert.equal(archived.draft,code);
 await back().click();await page.locator('.sidebar').getByRole('button',{name:'我的训练',exact:true}).click();
 await page.locator('.problem-title').filter({hasText:ordinaryTitle}).first().click();
 await editor.waitFor();
 return {realTauriIpc:true,goalCrudThroughIpc:true,existingReactTrainingEntry:true,goals:2,
  independentSelections:true,actualTaskOpened:true,ordinaryDraftSaved:true,recoveredAfterReload:true,
  archivalPreservesDraft:true,noOfficialPassClaimed:true,goalIds:created.ids,problemId:created.task.id};
}
