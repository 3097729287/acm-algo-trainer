import {memo, useEffect, useRef} from 'react';
import './MeteorsBackground.css';

// Stable positions avoid a new sky whenever preferences or the current page change.
const noise = seed => {
  const value = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return value - Math.floor(value);
};
const starGroups = Array.from({length: 3}, (_, group) =>
  Array.from({length: 60}, (_, index) => {
    const seed = group * 60 + index;
    return {x: noise(seed + 1) * 1600, y: noise(seed + 201) * 1000,
      radius: .3 + noise(seed + 401) * 1.2, opacity: .2 + noise(seed + 601) * .8};
  }));
const meteors = Array.from({length: 28}, (_, index) => ({
  top: `${noise(index + 801) * 70 - 10}%`,
  left: `${noise(index + 901) * 90 + 10}%`,
  '--meteor-tail': `${160 + noise(index + 1001) * 120}px`,
  animationDuration: `${1 + noise(index + 1101) * 1.2}s`,
  animationDelay: `${-noise(index + 1201) * 6}s`,
}));

export default memo(function MeteorsBackground() {
  const sky = useRef(null);
  useEffect(() => {
    const pause = () => { sky.current.dataset.paused = String(document.hidden); };
    pause();
    document.addEventListener('visibilitychange', pause);
    return () => document.removeEventListener('visibilitychange', pause);
  }, []);
  return <div ref={sky} className="meteors-background" aria-hidden="true">
    <svg className="meteors-background-stars" viewBox="0 0 1600 1000" preserveAspectRatio="none">
      {starGroups.map((stars, group) => <g key={group} className="meteors-star-group">
        {stars.map((star, index) => <circle key={index} cx={star.x} cy={star.y} r={star.radius} opacity={star.opacity}/>)}
      </g>)}
    </svg>
    <div className="meteors-background-rays">
      {meteors.map((style, index) => <span key={index} className="meteors-background-ray" style={style}/>)}
    </div>
  </div>;
});
