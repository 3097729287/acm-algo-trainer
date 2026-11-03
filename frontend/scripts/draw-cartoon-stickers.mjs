// Original, editable vector artwork: bold ink, flat color and a white die-cut edge.
import {mkdir,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const path=(d,fill,extra='')=>`<path d="${d}" fill="${fill}" ${extra}/>`;
const ellipse=(cx,cy,rx,ry,fill,extra='')=>`<ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="${fill}" ${extra}/>`;
const circle=(x,y,r,fill,extra='')=>ellipse(x,y,r,r,fill,extra);
const line=d=>path(d,'none');
const star=(x,y,r=8,color='#ffe158')=>path(`M${x} ${y-r} ${x+r*.3} ${y-r*.3} ${x+r} ${y} ${x+r*.3} ${y+r*.3} ${x} ${y+r} ${x-r*.3} ${y+r*.3} ${x-r} ${y} ${x-r*.3} ${y-r*.3}Z`,color,'stroke-width="2.8"');
const face=(x=64,y=65)=>`<g fill="#231f23" stroke="none">${ellipse(x-12,y-5,3,4,'#231f23')}${ellipse(x+12,y-5,3,4,'#231f23')}</g>${path(`M${x-5} ${y+4}q5 6 10 0`,'none','stroke-width="3"')}`;
const cheeks=(x,y)=>`<g stroke="none">${ellipse(x-21,y,6,3.5,'#ffa3a2')}${ellipse(x+21,y,6,3.5,'#ffa3a2')}</g>`;
const art={
 duck:path('M41 63C29 64 21 57 23 48c2-9 9-11 16-9C34 23 47 14 61 17c3-8 14-9 14 3 18 5 24 23 15 39 11 0 18-9 21-7 16 38-10 60-48 60-30 0-45-11-43-28 1-10 10-18 21-21Z','#ffdf43')+cheeks(67,50)+ellipse(55,36,3.2,4.2,'#231f23','stroke="none"')+ellipse(72,37,3.2,4.2,'#231f23','stroke="none"')+path('M38 42c4-6 12-5 16 0 10 0 14 8 8 14-7 7-27 8-36 2-7-6-5-14 3-14 3-2 6-3 9-2Z','#ff982e')+line('M47 52q4 4 8 0M62 78c15 4 26-4 28 2 2 12-16 20-26 10-3-3-4-7-3-11'),
 cloud:path('M29 94C7 94 7 61 27 58c-4-24 24-38 41-20 17-7 30 3 31 19 26-1 28 37 1 37Z','#b9eaff')+face(65,76)+cheeks(65,81),
 heart:path('M64 109C46 99 15 77 15 49c0-26 34-34 49-11 17-24 49-15 49 11 0 26-30 50-49 60Z','#ff7e94')+face(64,66)+cheeks(64,71),
 spark:path('M64 16 77 45 109 48 85 70 92 103 64 87 35 103 42 70 18 48 51 45Z','#ffd54e')+face(64,63),
 bolt:path('M70 14 29 69h30l-5 44 46-61H70l9-38Z','#ffdc4d')+path('m61 47-11 16h12','none','stroke="#fff5ad" stroke-width="4"'),
 leaf:path('M102 22C57 9 19 38 28 75c9 32 64 25 74-53Z','#8cd780')+line('M24 108 84 43M44 84l-5-21M57 70l22 1M68 57l-4-17'),
 drop:path('M64 14C53 34 27 56 27 78a37 37 0 0 0 74 0c0-22-26-44-37-64Z','#80d8f7')+face(64,77)+cheeks(64,82),
 flame:path('M64 13c21 20 41 39 38 66-2 23-18 34-38 34-25 0-40-16-38-36 1-15 8-27 18-35-1 12 1 18 6 24 11-13 21-28 14-53Z','#ff9450')+path('M64 67c12 11 19 24 9 32-13 11-29-2-20-18 0 7 5 10 6 7 3-5 7-12 5-21Z','#ffe05d','stroke-width="3"'),
 sun:line('M64 13v9M64 106v9M13 64h9M106 64h9M28 28l7 7M93 93l7 7M28 100l7-7M93 35l7-7')+circle(64,64,33,'#ffda50')+face(64,64)+cheeks(64,70),
 moon:path('M83 17C38 6 12 40 23 77c9 31 41 42 66 25-21 0-38-16-40-36-2-22 11-41 34-49Z','#ffdf64')+path('M34 66q5 6 10 0M35 83q4 4 8 0','none','stroke-width="3"')+star(96,42,7),
 rainbow:`<g fill="none" stroke-width="16">${path('M22 91V67a42 42 0 0 1 84 0v24','none','stroke="#231f23" stroke-width="27"')}${path('M22 91V67a42 42 0 0 1 84 0v24','none','stroke="#ff91a6"')}${path('M34 90V67a30 30 0 0 1 60 0v23','none','stroke="#ffd45c"')}${path('M46 89V67a18 18 0 0 1 36 0v22','none','stroke="#93d9ba"')}</g>`+path('M13 102c-7-11 1-21 11-18 4-15 27-10 25 4 14-1 18 17 3 18H23c-4 0-8-1-10-4Z','#f7fbff','stroke-width="3.5"')+path('M79 102c-7-11 1-21 11-18 4-15 27-10 25 4 9 1 10 17-2 18H89c-4 0-8-1-10-4Z','#f7fbff','stroke-width="3.5"'),
 compass:circle(64,68,41,'#ffdc7c')+circle(64,68,31,'#fff7de','stroke-width="3"')+path('m79 44-9 30-22 17 9-30Z','#ff8988','stroke-width="3.5"')+path('m57 61 13 13-22 17Z','#8bd7dd','stroke-width="3"')+circle(64,68,4,'#fff')+line('M64 30v8M64 98v8M26 68h8M94 68h8')+path('M57 26v-9h14v9','#ffdc7c'),
 gift:path('M25 57h78v48H25Z','#ffa0b3')+path('M19 43h90v21H19Z','#ffbdcb')+path('M54 43h20v62H54Z','#ffe278')+path('M64 43C31 49 24 17 39 18c14-1 23 15 25 25ZM64 43c33 6 40-26 25-25-14-1-23 15-25 25Z','#ffe278')+line('M36 52h10'),
 envelope:path('M15 38h98v65H15Z','#fff0d4')+path('m16 39 48 37 48-37','#ffbbbe')+line('m16 102 33-29m63 29L79 73')+path('M64 30c-12-18-27-5-20 6L64 52l20-16c7-11-8-24-20-6Z','#ff7c99','stroke-width="3"'),
 key:circle(48,45,27,'#ffdc69')+path('m66 61 39 37v14H91v-12H79V89L61 71Z','#ffdc69')+circle(48,43,11,'#fff6de')+star(23,92,7),
 fox:path('M23 19 51 36h26l28-17-4 54-19 28H46L27 73Z','#ffac69')+path('m29 28 9 30 12-15Z','#ffe9c6','stroke-width="3"')+path('m99 28-9 30-12-15Z','#ffe9c6','stroke-width="3"')+path('M29 66c10-5 22 1 35 16 13-15 25-21 35-16l-17 35H46Z','#fff3dc','stroke-width="3"')+circle(46,65,3,'#231f23','stroke="none"')+circle(82,65,3,'#231f23','stroke="none"')+path('m58 82 6 6 6-6Z','#231f23','stroke-width="2"')+line('M64 88v5m0 0-5 3m5-3 5 3'),
 orbit:ellipse(64,65,31,34,'#b4b4f2')+path('M35 65c-26-6-25-23-14-27 10-5 31 3 50 15 26 17 42 35 35 44-6 9-30 1-52-12','none','stroke="#231f23" stroke-width="12"')+path('M35 65c-26-6-25-23-14-27 10-5 31 3 50 15 26 17 42 35 35 44-6 9-30 1-52-12','none','stroke="#94e4e8" stroke-width="6"')+star(97,25,7)+star(25,104,6),
 planet:circle(65,64,32,'#b5b9f8')+path('M33 61c-20 12-27 25-20 31 12 13 103-32 102-50-1-8-12-8-27-3','none','stroke="#231f23" stroke-width="14"')+path('M33 61c-20 12-27 25-20 31 12 13 103-32 102-50-1-8-12-8-27-3','none','stroke="#ffd88a" stroke-width="7"')+circle(57,45,5,'#dce0ff','stroke-width="2.5"')+circle(80,65,4,'#dce0ff','stroke-width="2.5"')+star(25,27,6),
 comet:path('M108 20 85 92 41 109 18 86 34 45Z','#ffd86d')+path('m94 34-49 52m58-27L67 96','none','stroke="#ff9b62" stroke-width="8"')+circle(43,84,25,'#ffc575')+face(44,81),
 crystal:path('m65 14 25 23 13 52-39 23-39-23 13-52Z','#b0d9ff')+path('m38 37 26 27 26-27M25 89l39-25 39 25M65 14l-1 98','none','stroke-width="3"')+path('m65 14 25 23-26 27Z','#e3f5ff','stroke-width="3"')+path('m64 64 39 25-39 23Z','#91b5f4','stroke-width="3"'),
 butterfly:path('M62 65C27 6 5 25 23 61 2 66 19 111 50 88l14-13 14 13c31 23 48-22 27-27 18-36-4-55-39 4Z','#c7a0ed')+path('M44 58c-22-30-27-15-10 5m50-5c22-30 27-15 10 5','none','stroke="#ffc8df" stroke-width="8"')+line('M64 55v38M64 55 53 39M64 55l11-16')+circle(64,56,6,'#fff0c9'),
 gem:path('M36 25h56l22 31-50 55L14 56Z','#9cdfee')+path('M14 56h100M36 25l11 31 17 55 18-55 10-31M47 56l17-31 18 31','none','stroke-width="3.5"')+path('M36 25h28L47 56H14Z','#d8f6ff','stroke-width="3"')+star(104,104,6),
 crown:path('m20 37 25 21 19-35 20 35 24-21-12 64H32Z','#ffd666')+path('M31 85h66v17H31Z','#ffbc53','stroke-width="3.5"')+path('m64 57 9 12-9 12-9-12Z','#ff8c96','stroke-width="3"')+circle(20,34,5,'#ffe6a1','stroke-width="3"')+circle(64,22,5,'#ffe6a1','stroke-width="3"')+circle(108,34,5,'#ffe6a1','stroke-width="3"'),
 galaxy:path('M28 92C0 68 25 21 66 18c39-3 56 27 42 57-12 26-50 38-67 16-16-20 4-43 23-42 20 0 23 23 9 29-13 5-20-7-12-13','none','stroke="#231f23" stroke-width="22"')+path('M28 92C0 68 25 21 66 18c39-3 56 27 42 57-12 26-50 38-67 16-16-20 4-43 23-42 20 0 23 23 9 29-13 5-20-7-12-13','none','stroke="#b7a2f2" stroke-width="14"')+star(32,43,7)+star(95,91,8)+circle(87,32,3,'#ffdc6b','stroke="none"'),
 phoenix:path('M61 52C43 32 33 40 17 21c-3 20 8 31 18 38L17 53c2 17 17 29 34 32L40 99l23-7 23 7-11-14c17-3 32-15 34-32l-18 6c10-7 21-18 18-38-16 19-26 11-44 31Z','#ff9b69')+path('M63 92 53 67c-5-13-3-27 6-33l12-1-5 9 10 4-12 4c6 17 7 28-1 42Z','#ffe071','stroke-width="3.5"')+line('m27 39 19 22m-15 7 15 7m55-36L82 61m15 7-15 7')+circle(61,43,2,'#231f23','stroke="none"'),
 semicolon:circle(66,34,17,'#bfa3ec')+path('M50 63h33v19c-1 18-16 29-34 31l-4-15c12-1 17-8 17-13H50Z','#bfa3ec')+circle(60,30,2.7,'#231f23','stroke="none"')+circle(72,30,2.7,'#231f23','stroke="none"')+path('M61 39q5 4 10 0','none','stroke-width="2.5"'),
 answer42:circle(64,64,43,'#a9dcd4')+path('M44 43 31 69h25M49 44v40M71 50c0-13 23-13 23 0 0 10-22 16-22 33h23','none','stroke="#231f23" stroke-width="10"')+path('M44 43 31 69h25M49 44v40M71 50c0-13 23-13 23 0 0 10-22 16-22 33h23','none','stroke="#fff8dc" stroke-width="5"')+star(103,23,6),
};
const folder=new URL('../public/stickers/cartoon/',import.meta.url);await mkdir(folder,{recursive:true});
const manifest={style:'cartoon-paper-v1',description:'Original rounded flat-color illustrations, dark ink and white die-cut borders; no external resources',viewBox:'0 0 128 128',files:{}};
for(const [name,body] of Object.entries(art)){
 const drawing=['galaxy','planet','rainbow'].includes(name)?`<g transform="translate(6.4 6.4) scale(.9)">${body}</g>`:body;
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" fill="none" data-sticker-style="cartoon-paper-v1"><defs><filter id="cut" filterUnits="userSpaceOnUse" x="-12" y="-12" width="152" height="152" color-interpolation-filters="sRGB"><feMorphology in="SourceAlpha" operator="dilate" radius="3.5" result="cutline"/><feFlood flood-color="#fff"/><feComposite in2="cutline" operator="in"/><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs><g filter="url(#cut)" stroke="#231f23" stroke-width="4" stroke-linejoin="round" stroke-linecap="round">${drawing}</g></svg>\n`;
 await writeFile(new URL(name+'.svg',folder),svg);manifest.files[name+'.svg']=createHash('sha256').update(svg).digest('hex');
}
await writeFile(new URL('manifest.json',folder),JSON.stringify(manifest,null,2)+'\n');
console.log(`Drew ${Object.keys(art).length} cartoon paper stickers`);
