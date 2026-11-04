import {safeTier} from './RankArtwork.jsx';
import assets from '@/lib/rankAssets.json';

export default function AvatarFrame({index=0}) {
 const tier=safeTier(index),asset=assets[tier];
 return <svg className={`avatar-rank-frame rank-reference-art tier-${tier}`} viewBox="0 0 512 512" fill="none" aria-hidden="true" data-rank-art={asset.name}>
  <image href={`${import.meta.env.BASE_URL}ranks/avatar-${asset.name}.png`} width="512" height="512"/>
 </svg>;
}
