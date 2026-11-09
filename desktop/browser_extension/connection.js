async function refresh(){
 const state=document.querySelector('#state');state.textContent='正在检查连接…';
 try{const value=await chrome.runtime.sendMessage({type:'connection-status'});state.textContent=value?.connected?'已连接 ToBe':'尚未连接：请先打开新版 ToBe 并登录';document.querySelector('#version').textContent='扩展 '+chrome.runtime.getManifest().version+' · 纯标签页连接 v4'}
 catch{state.textContent='连接暂时中断，请检查 ToBe 后重试'}
}
document.querySelector('#refresh').addEventListener('click',refresh);refresh();
