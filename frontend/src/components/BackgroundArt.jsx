import {memo} from 'react';
import {canonicalStickerId} from '@/lib/stickerCatalogue.js';
import {backgroundThumbnail} from '@/lib/motionBackgrounds.js';
import './BackgroundArt.css';
export default memo(function BackgroundArt({item}){
 const id=canonicalStickerId(item?.id)?.replace(/^background-/,'')||item?.theme,url=backgroundThumbnail(id);
 return <img className="scene-background-art background-library-thumbnail" src={url} alt="" data-background-theme={id} aria-hidden="true"/>;
});
