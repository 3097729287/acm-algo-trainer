import './StickerArt.css';
import ARTWORK from '@/lib/stickerArtwork.js';

export const STICKER_NAMES={common:'普通',rare:'稀有',epic:'史诗',legendary:'传说'};
export function StickerArt({item,size=64}) {
 return <img className="sticker-art sticker-art-image" data-shape={item?.shape} data-sticker-style="cartoon-paper-v1" src={ARTWORK[item?.shape]||ARTWORK.spark} width={size} height={size} alt="" draggable={false}/>;
}
