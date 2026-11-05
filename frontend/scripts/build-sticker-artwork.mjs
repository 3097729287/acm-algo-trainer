import {readFile,writeFile,readdir} from 'node:fs/promises';
const base=new URL('../public/stickers/cartoon/',import.meta.url),assets={};
for(const file of (await readdir(base)).sort())if(file.endsWith('.svg')){const data=await readFile(new URL(file,base));if(/<script\b|(?:href|src)=["'](?:https?:|javascript:)/i.test(data.toString()))throw new Error('Unexpected external vector content');assets[file.slice(0,-4)]='data:image/svg+xml;base64,'+data.toString('base64');}
await writeFile(new URL('../src/lib/stickerArtwork.js',import.meta.url),'// Generated from original cartoon-paper SVGs; no per-sticker HTTP loading.\nexport default Object.freeze('+JSON.stringify(assets)+');\n');
const duck=await readFile(new URL('../public/sounds/stickers/duck.ogg',import.meta.url));
await writeFile(new URL('../src/lib/stickerDuckAudio.js',import.meta.url),'// Jonathon Jongsma, Mallard XC62258, CC BY-SA 3.0; see licenses/sticker-audio/NOTICE.txt.\nexport default '+JSON.stringify(duck.toString('base64'))+';\n');
console.log('Embedded '+Object.keys(assets).length+' vector stickers and the licensed duck recording');
const policy=JSON.parse(await readFile(new URL('../../server/leaderboard/src/sticker-rewards.json',import.meta.url),'utf8'));
const rarities=Object.fromEntries([...policy.collection,...policy.stickers].map(item=>[item.id,item.rarity]));rarities['epic-crystal']='rare';
await writeFile(new URL('../src/lib/stickerPolicy.js',import.meta.url),'// Generated from the shared cosmetic policy; regenerate with build-sticker-artwork.mjs.\nexport const BACKGROUND_THEMES='+JSON.stringify(policy.backgroundThemes)+';\nexport const STICKER_RARITIES='+JSON.stringify(rarities)+';\n');
