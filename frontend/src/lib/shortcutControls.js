export function activateControl(selector,root=document) {
 const target=[...root.querySelectorAll(selector)].find(node=>!node.disabled&&node.getClientRects().length&&!node.closest('[inert],[hidden],[aria-hidden=true]'));
 if(!target)return false;
 target.focus({preventScroll:true});
 if(target.tagName==='SELECT')target.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowDown',bubbles:true,cancelable:true}));else target.click();
 return true;
}
export function activatePageAction(id) {
 const selectors={
  'list-filter':'#tb-page-search [aria-label="筛选题目"]','list-random':'#tb-page-search [aria-label="随机单题"]',
  'catalog-up':'.training-lists-page [data-folder-up]','catalog-home':'.training-lists-page [aria-label="全部题单"]','catalog-filter':'#tb-page-search [aria-label="筛选题单题目"]','catalog-new':'#tb-page-search [aria-label="新建题单"]',
  'contest-filter':'#tb-page-search [aria-label="筛选比赛"]','contest-folders':'#tb-page-search [aria-label="比赛文件夹浏览"]','contest-up':'.competition-page [data-folder-up],.competition-page [aria-label="全部比赛"]',
  'mock-filter':'#tb-page-search [aria-label="模拟赛筛选"]','mock-regenerate':'.mock-create [aria-label="生成试卷"]',
  'lecture-learned':'.lectures-detail .lesson-learned-toggle','lecture-fullscreen':'.lecture-fullscreen-toggle','lecture-back':'.lectures-detail [aria-label="返回上篇"]',
  'template-copy':'.templates-page [aria-label="复制模板"]','template-back':'.templates-page [aria-label="返回模板"]',
  'records-platform':'#tb-page-search [aria-label="提交平台"]','records-result':'#tb-page-search [aria-label="提交结果分类"]',
  'initial-new':'.initial-code-settings [aria-label="新建初始代码模板"]','initial-copy':'.initial-code-settings [aria-label="复制为初始代码模板"]',
 };
 if(selectors[id])return activateControl(selectors[id]);
 const period={'ranking-daily':'每日','ranking-weekly':'本周','ranking-all':'累计'}[id];
 if(period){const tab=[...document.querySelectorAll('[aria-label="排行榜时间范围"] [role=tab]')].find(node=>node.textContent.trim()===period);if(tab&&!tab.disabled){tab.click();return true;}}
 return false;
}
