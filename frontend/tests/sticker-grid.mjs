import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {STICKERS} from '../../server/leaderboard/src/gameplay.mjs';
const server=await createServer({server:{host:'127.0.0.1',port:0,watch:null}});await server.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1000,height:780}}),errors=[];
page.on('pageerror',issue=>errors.push(issue.message));
try{
 await page.addInitScript(catalogue=>{
  window.rewardFixtureData={catalogue,boxes:[],packPolicy:{}};
  const owner='11111111-1111-4111-8111-111111111111';localStorage.setItem('sticker-reward-fixture',JSON.stringify({owner,revision:1,catalogue,units:catalogue.map((item,i)=>({id:'owned-'+i,stickerId:item.id,revision:0,placement:null})),boxes:{},replies:[],operations:{}}));
 },STICKERS);
 await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/tests/sticker-rewards-fixture.html`);
 await page.getByRole('button',{name:'贴纸',exact:true}).click();await page.getByRole('region',{name:'贴纸区域',exact:true}).click({position:{x:100,y:180}});
 const picker=page.getByRole('dialog',{name:'选择贴纸',exact:true});await picker.waitFor();
 for(const width of [1000,360]){
  await page.setViewportSize({width,height:780});
  const state=await picker.evaluate(node=>{const list=node.querySelector('.sticker-inventory'),cards=[...node.querySelectorAll('.sticker-choice')];return {mode:getComputedStyle(list).display,overflow:list.scrollWidth-list.clientWidth,cards:cards.map(card=>({rarity:card.className.match(/rarity-(\w+)/)[1],border:getComputedStyle(card).borderTopStyle,colour:getComputedStyle(card).borderTopColor,y:card.getBoundingClientRect().y})),width:node.getBoundingClientRect().width};});
  assert.equal(state.mode,'grid');assert(state.overflow<=1);assert.equal(state.cards.length,STICKERS.filter(s=>s.kind!=='background').length);assert(state.width<=width-16);
  const order={legendary:0,epic:1,rare:2,common:3};assert(state.cards.every((card,i)=>i===0||order[card.rarity]>=order[state.cards[i-1].rarity]));assert(state.cards.every(card=>card.border==='solid'&&!card.colour.endsWith(', 0)')));assert(state.cards.at(-1).y>state.cards[0].y);
 }
 assert.deepEqual(errors,[]);console.log('PASS collectible sticker types, persistent rarity borders, sorted rows, vertical scrolling and narrow width');
}finally{await browser.close();await server.close();}
