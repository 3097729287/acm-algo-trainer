import {rankIndex,TIER_NAMES} from '@/lib/rankTiers.js';
import assets from '@/lib/rankAssets.json';

export default function DuelBannerFrame({rank}){
 const tier=rankIndex(rank),asset=assets[tier],base=import.meta.env.BASE_URL+'ranks/';
 return <svg className={'duel-banner-frame banner-tier-'+tier} viewBox="0 0 320 520" aria-hidden="true" data-tier={tier} data-tier-name={TIER_NAMES[tier]} data-rank-art={asset.name} fill="none" preserveAspectRatio="none" style={{overflow:'hidden'}}>
  <rect x="12" y="12" width="296" height="496" fill="#111a23"/>
  <svg x="0" y="0" width="320" height="520" viewBox={asset.borderBounds.join(' ')} preserveAspectRatio="none" style={{overflow:'hidden'}}>
   <image href={`${base}frames-${asset.borderAtlas}.png`} width="1024" height="1024"/>
  </svg>
  <image href={`${base}crest-${asset.name}.png`} x="145" y="70" width="30" height="30"/>
 </svg>;
}
