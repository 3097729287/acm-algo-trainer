import assert from 'node:assert/strict';
import {SHORTCUTS,eventShortcut} from '../src/lib/shortcuts.js';
import {deliverNativeShortcut,dispatchApplicationShortcut,registerShortcutRoute,shortcutBinding,shortcutSnapshot,textSafeCombo} from '../src/lib/applicationShortcuts.js';
import {availableProblemNeighbour} from '../src/lib/problemNeighbours.js';

const editing={closest:()=>true};
const eventFor=combo=>{const modifiers=[];let key=combo,match;while((match=/^(Ctrl|Alt|Shift|Meta)\+/i.exec(key))){modifiers.push(match[1].toLowerCase());key=key.slice(match[0].length);}return {key,ctrlKey:modifiers.includes('ctrl'),altKey:modifiers.includes('alt'),shiftKey:modifiers.includes('shift'),metaKey:modifiers.includes('meta'),target:editing,repeat:false,defaultPrevented:false,preventDefault(){this.defaultPrevented=true;},stopImmediatePropagation(){}};};
let count=0;
for(const [id,,combo] of SHORTCUTS.filter(([, ,combo])=>combo&&textSafeCombo(combo))){
 let calls=0;const key='test-'+id;
 const remove=registerShortcutRoute({key,priority:1,context:'current',bindings:[{id,combo}],target:()=>editing,handle:event=>{calls++;event.preventDefault();}});
 assert(dispatchApplicationShortcut(eventFor(combo)),id+' must work while an input/editor owns focus');assert.equal(calls,1);
 const registration=shortcutSnapshot().serial;
 assert(deliverNativeShortcut({route:key,id,ageSeconds:.1},registration),id+' must use the same native route');assert.equal(calls,2);
 assert(!deliverNativeShortcut({route:key,id,ageSeconds:.1},registration+1));
 assert(!deliverNativeShortcut({route:key,id,ageSeconds:3},registration));
 const repeat={...eventFor(combo),repeat:true};assert(dispatchApplicationShortcut(repeat));assert.equal(calls,2);
 remove();count++;
}
let calls=0;
const remove=registerShortcutRoute({key:'override',priority:1,bindings:[shortcutBinding('run',{run:'Ctrl+J'})],target:()=>editing,handle:event=>{calls++;event.preventDefault();}});
assert(!dispatchApplicationShortcut(eventFor('Ctrl+R')));assert(dispatchApplicationShortcut(eventFor('Ctrl+J')));assert.equal(calls,1);remove();
const text=registerShortcutRoute({key:'text',bindings:[{id:'help',combo:'?'},{id:'solution',combo:'U'}],handle:()=>{throw new Error('Typing is not an application command');}});
assert(!dispatchApplicationShortcut(eventFor('?')));assert(!dispatchApplicationShortcut(eventFor('U')));assert.equal(shortcutSnapshot().bindings.length,0);text();
for(const combo of ['Ctrl++','Ctrl+?','Ctrl+,','Alt+Shift+T'])assert.equal(eventShortcut(eventFor(combo)).toLowerCase(),combo.toLowerCase());
const queue=['A','missing','removed','D'],rows=[{id:'A'},{id:'missing',statementAvailable:false},{id:'D',statementAvailable:true}];
assert.equal(availableProblemNeighbour(queue,'A',rows),'D');assert.equal(availableProblemNeighbour(queue,'D',rows),null);assert.equal(availableProblemNeighbour(queue,'D',rows,-1),'A');
console.log(JSON.stringify({ok:true,registeredModifiedAndFunctionCombinations:count,focusedInputsAndEditors:true,nativeUsesSameRoutes:true,accountOverrides:true,oldContextAndExpiredActionsRejected:true,repeatSuppressed:true,ordinaryTypingPreserved:true}));
