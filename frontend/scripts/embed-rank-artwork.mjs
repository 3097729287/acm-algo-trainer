import {readFile,writeFile} from 'node:fs/promises';
const tiers=JSON.parse(await readFile(new URL('../src/lib/rankAssets.json',import.meta.url),'utf8')),result={};
for(const tier of tiers){
 result[tier.name]={};
 for(const type of ['avatar','emblem']){
  const bytes=await readFile(new URL(`../public/ranks/${type}-${tier.name}.png`,import.meta.url));
  result[tier.name][type]='data:image/png;base64,'+bytes.toString('base64');
 }
}
await writeFile(new URL('../src/lib/rankArtworkInline.json',import.meta.url),JSON.stringify(result)+'\n');
console.log('Embedded unchanged rank PNGs for immediate avatar/frame/medal rendering');
