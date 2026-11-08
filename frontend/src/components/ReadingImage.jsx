import {dialogPointerDown,dialogBackdropClick} from '@/lib/dialogBackdrop.js';
import { useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { defaultUrlTransform } from 'react-markdown';
import './ReadingImage.css';
import {adaptReadingImage} from '@/lib/readingImageTheme.js';
import {readEditorialMotion} from '@/lib/editorialMotion.js';
import ReadingMotion from './ReadingMotion.jsx';

// Markdown links retain react-markdown's protocol restrictions. Embedded image
// data is allowed only as an img source, never as navigation or inline HTML.
const imageData = /^data:image\/(?:svg\+xml|png|jpeg|gif|webp|avif|bmp);base64,[a-z\d+/=\s]+$/i;
export function readingUrlTransform(url, key) {
  return key === 'src' && imageData.test(url) ? url : defaultUrlTransform(url);
}

export function resolveReadingImage(src, images = {}) {
  if (!src) return '';
  const variants = [src];
  try { variants.push(decodeURI(src), decodeURIComponent(src)); } catch { /* Invalid URL stays unresolved. */ }
  const mapped = variants.find(key => Object.hasOwn(images, key));
  const value = mapped ? images[mapped] : src;
  return imageData.test(value) || /^https?:\/\//i.test(value) || /^\/api\/library-assets\/[a-f0-9]{64}$/.test(value) ? value : '';
}

export default function ReadingImage({ src, alt = '', title, images = {} }) {
  const resolved = resolveReadingImage(src, images);
  const motion=useMemo(()=>readEditorialMotion(resolved),[resolved]);
  return motion?<ReadingMotion key={resolved} model={motion} renderImage={({source,toolbar,onZoomChange})=><ReadingImageView resolved={source} alt={alt} title={title} toolbar={toolbar} onZoomChange={onZoomChange}/>}/>:<ReadingImageView resolved={resolved} alt={alt} title={title}/>;
}

function ReadingImageView({resolved,alt,title,toolbar,onZoomChange}){
  const [failed, setFailed] = useState('');
  const dialog = useRef(null), trigger = useRef(null);
  if (!resolved || failed === resolved) {
    return <span className="reading-image-missing" role="status">图片未能加载{alt ? `：${alt}` : ''}</span>;
  }
  const close = () => { dialog.current?.close(); onZoomChange?.(false);trigger.current?.focus(); };
  return <span className="reading-image">
    <button ref={trigger} type="button" className="reading-image-open" aria-label={`放大图片：${alt || '题解配图'}`} onClick={() => {dialog.current?.showModal();onZoomChange?.(true);}}>
      <img onLoad={event=>void adaptReadingImage(event.currentTarget)} src={resolved} alt={alt} title={title || '点击放大'} loading="lazy" onError={() => setFailed(resolved)} />
    </button>
    {createPortal(<dialog onPointerDown={dialogPointerDown} onClick={dialogBackdropClick} ref={dialog} className="reading-image-dialog" aria-label={alt || '题解配图'}
      onKeyDown={event => event.stopPropagation()} onCancel={event => { event.preventDefault(); close(); }}
      onClick={event => { if (event.target === event.currentTarget) close(); }}>
      <div className="reading-image-toolbar"><span>{alt || '题解配图'}</span><button type="button" onClick={close}>关闭</button></div>
      <div className="reading-image-full"><img onLoad={event=>void adaptReadingImage(event.currentTarget)} src={resolved} alt={alt} /></div>
      {toolbar}
    </dialog>, document.body)}
  </span>;
}
