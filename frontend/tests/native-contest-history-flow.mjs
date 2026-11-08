import assert from 'node:assert/strict';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {resolve} from 'node:path';

async function rpc(page,path,query={}) {
 return page.evaluate(async({path,query})=>{
  const result=await window.__TAURI__.core.invoke('api_request',{request:{version:1,id:crypto.randomUUID(),method:'GET',path,query}});
  if(!result.ok)throw new Error(result.error.code+': '+result.error.message);return result.data;
 },{path,query});
}

export async function exerciseNativeContestHistory(page,output,sandbox,python) {
 assert(python,'Set TB_NATIVE_TEST_PYTHON for isolated frozen-history fixtures');
 assert(resolve(sandbox).startsWith(resolve(output)+'\\sandbox-'),'Only the fresh test journal can receive generated history');
 const id='luogu-training-P1001',cancelled='luogu-training-P1002',contest='generated-frozen-window-history';
 const normal=await rpc(page,'problem',{id:[id]}),other=await rpc(page,'problem',{id:[cancelled]});
 const at=(await rpc(page,'workspace')).now;
 const start=new Date(Date.parse(at)-2*86400000).toISOString();
 const plus=minutes=>new Date(Date.parse(start)+minutes*60000).toISOString();
 const slots=[{letter:'A',id,title:normal.title,difficulty:800,tags:['模拟'],judgeScope:'official',statementAvailable:true,trainingAdded:false},
  {letter:'B',id:cancelled,title:other.title,difficulty:1200,tags:['动态规划'],judgeScope:'unsupported',statementAvailable:false,trainingAdded:false}];
 const fixture={contest,id,cancelled,start,deadline:plus(60),slots,code:'// frozen exam draft remains independent 😀\n',cancelledCode:'// cancelled context recovered 😀\n',attempts:[['CE',plus(1)],['WA',plus(2)],['AC',plus(8)]]};
 const script=`import json,sqlite3,sys\nfrom pathlib import Path\np=Path(sys.argv[1]);assert p.name.startswith('sandbox-') and p.is_dir()\nf=json.loads(sys.argv[2])\nwith sqlite3.connect(p/'personal.sqlite3') as db:\n db.execute("INSERT INTO contests(id,name,status,started_at,deadline,finished_at,duration,slots,config) VALUES(?,'原生历史窗口验证','finished',?,?,?,60,?,?)",(f['contest'],f['start'],f['deadline'],f['deadline'],json.dumps(f['slots'],ensure_ascii=False),json.dumps({'strategy':'replay','contest':'ABC 001','wrongPenalty':20,'compilePenalty':False})))\n db.execute("INSERT INTO drafts VALUES(?,?,?,?)",(f['id'],f['contest'],f['code'],f['start']))\n for verdict,at in f['attempts']:db.execute("INSERT INTO submissions(id,problem_id,contest_id,mode,scope,verdict,code,submitted_at,finished_at,message) VALUES(?,?,?,'submit','official',?,'generated frozen test receipt',?,?,'Generated offline fixture')",(f['contest']+'-'+verdict,f['id'],f['contest'],verdict,at,at))\n db.execute("INSERT INTO contests(id,name,status,started_at,deadline,duration,slots,config,deleted_at) VALUES('generated-cancelled-window','取消考场','cancelled',?,?,60,?,'{}',?)",(f['start'],f['deadline'],json.dumps([{'letter':'A','id':f['cancelled'],'title':'取消题目'}],ensure_ascii=False),f['deadline']))\n db.execute("INSERT INTO drafts VALUES(?,'generated-cancelled-window',?,?)",(f['cancelled'],f['cancelledCode'],f['start']))\n`;
 await promisify(execFile)(python,['-c',script,sandbox,JSON.stringify(fixture)],{windowsHide:true});
 let view=await rpc(page,'contest',{id:[contest]});
 assert.equal(view.contest.accepted,1);assert.equal(view.contest.penalty,28);assert.equal(view.contest.slots[1].statementAvailable,false);
 assert.equal((await rpc(page,'problem',{id:[id],contestId:[contest]})).draft,fixture.code);
 assert.equal((await rpc(page,'problem',{id:[id]})).draft,normal.draft);
 assert.equal((await rpc(page,'problem',{id:[cancelled]})).draft,fixture.cancelledCode);
 const workspace=await rpc(page,'workspace');assert(workspace.contests.some(row=>row.id===contest));assert(workspace.completedReplayContests.includes('ABC 1'));
 // Only the generated WebView's navigation cache is elevated to expose the
 // existing history UI. No account level, XP or authorization is persisted.
 const {owner}=await rpc(page,'api/capabilities');assert.equal(typeof owner,'string');assert(owner);
 await page.evaluate(owner=>localStorage.setItem('tb.navigation-level.v1.'+owner,JSON.stringify({owner,level:6})),owner);
 await page.setViewportSize({width:1500,height:950});await page.reload();
 await page.locator('.tb-workbench:visible').waitFor();
 await page.locator('button[aria-label="返回主界面"]:visible').first().click();
 await page.locator('.tb-workbench:visible').waitFor({state:'hidden'});
 await page.keyboard.press('Control+5');
 const history=page.getByRole('region',{name:'模拟赛记录',exact:true});
 await history.getByRole('button',{name:/原生历史窗口验证/}).first().click();
 const details=page.locator('.record-detail');await details.getByRole('heading',{name:'原生历史窗口验证',exact:true}).waitFor();
 assert((await details.innerText()).includes('1/2 AC'));assert((await details.innerText()).includes('罚时 28 分钟'));
 assert.equal(await details.locator('.record-slot').count(),2);
 await page.screenshot({path:resolve(output,'native-frozen-contest-history.png')});
 await details.getByRole('button',{name:'只看未 AC',exact:true}).click();assert.equal(await details.locator('.record-slot').count(),1);
 await details.getByRole('button',{name:'只看未 AC',exact:true}).click();
 await details.getByRole('button',{name:'再练一次',exact:true}).click();
 const editor=page.locator('.tb-workbench .cm-content[contenteditable=true]:visible').first();
 if(!await editor.isVisible())await page.keyboard.press('Alt+2');await editor.waitFor();
 await page.waitForFunction(expected=>[...document.querySelectorAll('.tb-workbench .cm-content[contenteditable=true]')].some(node=>node.getClientRects().length&&node.innerText.trimEnd()===expected),normal.draft.trimEnd());
 assert.equal((await editor.innerText()).trimEnd(),normal.draft.trimEnd());
 await page.reload();await page.locator('.tb-workbench').waitFor();if(!await editor.isVisible())await page.keyboard.press('Alt+2');await editor.waitFor();
 assert.equal((await editor.innerText()).trimEnd(),normal.draft.trimEnd());
 view=await rpc(page,'contest',{id:[contest]});assert.equal(view.contest.penalty,28);
 assert.equal((await rpc(page,'problem',{id:[id],contestId:[contest]})).draft,fixture.code);
 return {realTauriIpc:true,generatedIsolatedJournal:true,externalSubmissionsSent:0,frozenHistoryDisplayed:true,filteredUnsolved:true,officialScore:{accepted:1,total:2,penalty:28},absentStatementSlotPreserved:true,normalAndFrozenDraftsIndependent:true,cancelledDraftRecovered:true,ordinaryReopenAndReloadPreserved:true,realAccountLevelChanged:false};
}
