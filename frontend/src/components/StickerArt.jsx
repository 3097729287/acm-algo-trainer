import './StickerArt.css';
import ARTWORK from '@/lib/stickerArtwork.js';
import {memo} from 'react';
import {BackgroundArt,SceneStickerArt,SCENE_SHAPES} from './SceneStickerArt.jsx';

export const STICKER_NAMES={common:'普通',rare:'稀有',epic:'史诗',legendary:'传说'};
export const StickerArt=memo(function StickerArt({item,size=64,appearance}) {
 if(item?.kind==='background'||item?.shape?.startsWith('background-'))return <span className="sticker-art background-card-art" style={{width:size,height:size}}><BackgroundArt item={item} thumbnail/></span>;
 if(SCENE_SHAPES.has(item?.shape))return <SceneStickerArt item={item} size={size} appearance={appearance}/>;
 return <img className="sticker-art sticker-art-image" data-shape={item?.shape} data-sticker-style="cartoon-paper-v1" src={ARTWORK[item?.shape]||ARTWORK.spark} width={size} height={size} alt="" draggable={false}/>;
});
