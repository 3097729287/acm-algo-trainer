import './StickerArt.css';
import {useRef} from 'react';
export const STICKER_NAMES={common:'普通',rare:'稀有',epic:'史诗',legendary:'传说'};
const SHAPES={
 duck:'M16 60C25 67 31 65 38 56V37a19 19 0 1 1 33 12L87 54 72 61C70 87 35 91 19 74ZM55 30a3 3 0 1 0 0 6 3 3 0 1 0 0-6Z',
 semicolon:'M48 9a15 15 0 1 0 0 30 15 15 0 1 0 0-30ZM34 51H65V67C64 82 53 92 34 94L31 80C43 78 47 73 47 68H34Z',
 answer42:'M16 14H31V42H42V14H56V84H42V57H10ZM64 29C64 8 94 8 94 29 94 44 78 48 78 62H94V82H63V65C63 41 80 40 80 29Z',
 heart:'M50 88C35 75 8 57 8 34 8 8 40 7 50 28 61 7 92 8 92 34 92 58 65 75 50 88Z',
 rainbow:'M9 80V53a41 41 0 0 1 82 0V80H76V53a26 26 0 0 0-52 0V80ZM33 80V53a17 17 0 0 1 34 0V80H55V53a5 5 0 0 0-10 0V80Z',
 compass:'M50 7a43 43 0 1 0 0 86 43 43 0 1 0 0-86ZM70 25 58 59 26 73 40 40ZM50 14V25M50 76V87M14 50H25M76 50H87',
 gift:'M12 38H88V57H12ZM20 57H80V91H20ZM44 36H57V91H44ZM49 37C21 37 17 13 31 11 43 9 48 26 49 37ZM52 37C79 37 85 13 71 11 59 9 54 26 52 37Z',
 envelope:'M8 24H92V80H8ZM8 24 50 58 92 24M9 80 37 53M91 80 63 53M75 8 79 17 89 19 81 25 83 35 75 30 67 35 69 25 61 19 71 17Z',
 key:'M32 9a24 24 0 1 0 17 41L67 68V82H81V94H94V69L56 31A24 24 0 0 0 32 9ZM29 22a8 8 0 1 0 0 16 8 8 0 1 0 0-16Z',
 fox:'M12 10 38 28H62L88 10 85 62 66 85H34L15 62ZM32 49a4 4 0 1 0 0 8 4 4 0 1 0 0-8ZM68 49a4 4 0 1 0 0 8 4 4 0 1 0 0-8ZM39 67 50 79 61 67Z',
 orbit:'M50 26a24 24 0 1 0 0 48 24 24 0 1 0 0-48ZM8 65C-8 84 40 91 72 57 105 22 89 5 69 16M12 32C-3 13 37 8 72 42 105 75 91 96 73 84M49 5 55 16 67 18 58 27 60 39 49 33 38 39 40 27 31 18 43 16Z',
 spark:'M50 8 59 36 88 40 65 58 70 88 50 71 28 88 33 58 11 40 41 36Z',
 leaf:'M79 17C25 9 10 49 29 72 51 99 91 66 79 17ZM28 75 69 33M47 54 44 36M54 48 70 50',
 drop:'M50 8C42 24 18 42 18 63a32 32 0 0 0 64 0C82 42 58 24 50 8Z',
 cloud:'M24 76a20 20 0 0 1-4-39 26 26 0 0 1 49-9 24 24 0 1 1 9 48Z',
 flame:'M49 7C61 28 82 37 81 61a31 31 0 0 1-62 0c0-15 9-27 17-35-2 17 6 22 6 22S57 33 49 7Z',
 bolt:'M57 7 17 56 44 56 36 94 85 40 58 40 66 7Z',
 sun:'M50 19 57 6 63 22 80 15 78 33 95 40 80 50 94 64 75 67 77 86 59 79 49 95 41 79 22 86 25 67 6 62 21 48 6 37 25 31 23 14 40 22Z',
 comet:'M91 8 68 65 38 86 16 69 14 43 41 22ZM19 61 60 21M36 82 79 39',
 moon:'M77 72C25 79 20 30 47 8 8 15-2 70 31 87 51 98 74 90 85 76Z',
 planet:'M73 26a31 31 0 1 0-46 48 31 31 0 0 0 46-48ZM13 61C-2 92 102 45 89 37M10 64C8 81 69 57 86 36',
 crystal:'M50 7 77 32 85 68 50 94 14 68 23 32ZM23 32 50 56 77 32M14 68 50 56 85 68M50 7 50 94',
 butterfly:'M49 47C5-11 3 36 24 53 1 57 16 95 42 70L50 58 58 70C84 95 99 57 76 53 97 36 95-11 51 47ZM50 42 50 82M50 42 41 27M50 42 59 27',
 gem:'M24 13H76L94 40 50 93 6 40ZM6 40H94M24 13 36 40 50 93 64 40 76 13M36 40 50 13 64 40',
 crown:'M12 23 33 42 50 13 68 42 88 23 77 79H23ZM23 65H77',
 galaxy:'M50 41C8 4 1 42 24 58 48 83 90 59 84 33 77 5 38 15 32 42 22 79 73 95 83 60M50 33 55 46 69 50 55 55 50 69 45 55 31 50 45 46Z',
 phoenix:'M48 72C12 85 9 53 6 23 20 44 34 28 50 55 66 28 80 44 94 23 91 53 88 85 52 72L50 94ZM50 58 50 24 64 15 57 32',
};
const READY_ART=new Set(['duck','heart','rainbow','compass','gift','envelope','key','fox','orbit','spark','leaf','drop','cloud','flame','bolt','sun','comet','moon','planet','crystal','butterfly','gem','crown','galaxy']);
export function StickerArt({item,size=64}){
 const id=useRef('sticker-'+crypto.randomUUID()).current,shape=item?.shape;
 if(READY_ART.has(shape))return <img className="sticker-art sticker-art-image" data-shape={shape} src={'/stickers/fluent/'+shape+'.svg'} width={size} height={size} alt="" draggable={false}/>;
 const colors=shape==='phoenix'?['#f7c958','#e98638','#b64c35']:shape==='semicolon'?['#d0c9ea','#aca6d4','#827ba9']:['#c5e3d7','#83bba7','#548b7b'];
 return <svg className="sticker-art" data-shape={shape} viewBox="0 0 100 100" width={size} height={size} aria-hidden="true"><defs><linearGradient id={id} x1="0" y1="0" x2="1" y2="1"><stop stopColor={colors[0]}/><stop offset=".5" stopColor={colors[1]}/><stop offset="1" stopColor={colors[2]}/></linearGradient></defs><path d={SHAPES[shape]||SHAPES.spark} fill={`url(#${id})`} stroke={colors[2]} strokeWidth="1" strokeLinejoin="round" strokeLinecap="round"/></svg>;
}
