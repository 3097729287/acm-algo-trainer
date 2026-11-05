import {memo,useEffect,useId,useRef,useState} from 'react';
import './BackgroundArt.css';

// The light, haze and terrain share a palette, rather than filling silhouettes
// with unrelated flat colours. Geometry stays gentle at every aspect ratio.
const PALETTES={
 night:{sky:['#111c36','#263653','#47566e','#817b8a','#b39b9d'],land:['#6c7385','#343e59','#1c2b43'],mist:'#b4adca',light:'#c1b4d4'},
 morning:{sky:['#536f91','#8caac0','#b9ced1','#ead6c7','#f3dbbd'],land:['#c7c6b3','#809a91','#466e70'],mist:'#e9ddce',light:'#ffe4c2'},
 rain:{sky:['#283c51','#526579','#7f919e','#aab5b5','#b6b8ad'],land:['#8c9e98','#4a7478','#284f59'],mist:'#c2cfd1',light:'#d0d9cc'},
 coast:{sky:['#527e9c','#85acbd','#acc9cb','#d8d5c2','#e5d3b7'],land:['#e1c6a4','#c5a988','#a9846f'],mist:'#dbdfce',light:'#f1e2be'},
 beach:{sky:['#6b708f','#a59aaf','#d9b7bc','#f0c7ad','#f2d6b3'],land:['#e6b994','#cf997c','#a77369'],mist:'#f3d1bc',light:'#ffddb9'},
 desert:{sky:['#696a86','#a78e9c','#ceb0a8','#e7c2ad','#edcda8'],land:['#dfb393','#c78c77','#986b69'],mist:'#edc2aa',light:'#ffdfba'},
 rainforest:{sky:['#173d43','#366561','#679189','#9eb6a3','#c0c9a9'],land:['#839e84','#386f62','#184d48'],mist:'#c2d7be',light:'#e2ddb0'},
 mountains:{sky:['#536f88','#89a6b6','#b9c9c9','#e0d5c5','#e9d9bf'],land:['#a9bbbd','#647f8e','#344e65'],mist:'#d4d7cf',light:'#f0dbba'},
 snow:{sky:['#6a81a1','#a5b7cc','#ced8df','#e6dfdd','#f0dfd1'],land:['#e5e3e1','#b2c6d4','#7998b6'],mist:'#e3e6e9',light:'#ffe6d5'},
 river:{sky:['#6f979e','#a0bab8','#c5cec0','#e6d7bd','#f1d9b7'],land:['#b7b99a','#789887','#416c6c'],mist:'#d9dfcb',light:'#ffe2bb'},
 sky:{sky:['#426b99','#779dc2','#b1c8d9','#ded9da','#f0d7c9'],land:['#e7e2e2','#c1c4d7','#8fabc5'],mist:'#f4e5df',light:'#ffe6ce'},
 underground:{sky:['#101f2b','#193a44','#2d5962','#4e7c80','#7f9c94'],land:['#567b7c','#28494f','#142c37'],mist:'#8fd1c6',light:'#b6e9d3'},
 room:{sky:['#61545c','#a78e88','#c9b09a','#dfc9ac','#e9d2b2'],land:['#c3a184','#94765e','#5d514b'],mist:'#ead5b6',light:'#ffdfb0'},
 galaxy:{sky:['#050a1c','#101430','#23213e','#282138','#121c34'],land:['#191d38','#10182f','#070f24'],mist:'#b9adce',light:'#f6d5be'},
};
const noise=n=>{const v=Math.sin(n*127.1+311.7)*43758.5453;return v-Math.floor(v);};
const HILLS=[
 'M-60 542C90 506 150 459 269 469S465 547 594 482 803 385 1060 480V740H-60Z',
 'M-60 579C92 580 180 481 321 500S487 585 650 522 842 476 1060 533V740H-60Z',
 'M-60 632C110 577 248 605 380 586S574 636 733 589 919 572 1060 612V740H-60Z',
];
function Gradient({id,colours,vertical=true}){return <linearGradient id={id} x1="0" y1="0" x2={vertical?'.12':'1'} y2="1">{colours.map((colour,index)=><stop key={index} offset={index/(colours.length-1)} stopColor={colour}/>)}</linearGradient>;}

export default memo(function BackgroundArt({item,thumbnail=false,interactive=!thumbnail,demo=0}){
 const id='atmos-'+useId().replaceAll(':',''),theme=item?.theme||item?.shape?.replace('background-','')||'morning',p=PALETTES[theme]||PALETTES.morning;
 const ref=useRef(null),timer=useRef(null),[windowOpen,setWindowOpen]=useState(false),[debris,setDebris]=useState(0),[flight,setFlight]=useState(0);
 const url=name=>`url(#${id}-${name})`,space=theme==='galaxy';
 useEffect(()=>()=>clearTimeout(timer.current),[]);
 useEffect(()=>{
  if(!space||!interactive)return;
  const svg=ref.current,surface=svg.closest('.sticker-surface')||svg.parentElement;let frame=0;
  const move=event=>{if(frame)return;const x=event.clientX,y=event.clientY;frame=requestAnimationFrame(()=>{frame=0;const b=svg.getBoundingClientRect();svg.style.setProperty('--space-x',((x-b.left)/b.width-.5)*10+'px');svg.style.setProperty('--space-y',((y-b.top)/b.height-.5)*8+'px');});};
  const leave=()=>{svg.style.setProperty('--space-x','0px');svg.style.setProperty('--space-y','0px');};
  surface.addEventListener('pointermove',move,{passive:true});surface.addEventListener('pointerleave',leave);
  return()=>{cancelAnimationFrame(frame);surface.removeEventListener('pointermove',move);surface.removeEventListener('pointerleave',leave);};
 },[space,interactive]);
 const rockfall=()=>{setDebris(value=>value+1);clearTimeout(timer.current);timer.current=setTimeout(()=>setDebris(0),1900);};
 const travel=()=>{setFlight(value=>value+1);clearTimeout(timer.current);timer.current=setTimeout(()=>setFlight(0),1700);};
 useEffect(()=>{if(!demo)return;if(theme==='underground')rockfall();if(theme==='room')setWindowOpen(value=>!value);if(space)travel();},[demo,theme]);
 const keyActivate=action=>event=>{if(['Enter',' '].includes(event.key)){event.preventDefault();action();}};
 const terrain=(path,index,opacity=1)=><path key={index} d={path} fill={url('ground-'+index)} opacity={opacity}/>;
 const haze=(y,opacity=.35)=> <ellipse cx="510" cy={y} rx="690" ry="40" fill={url('mist')} opacity={opacity}/>;
 return <svg ref={ref} className={'scene-background-art atmosphere-art'+(thumbnail?' scene-background-thumbnail':'')} data-background-theme={theme} data-background-version="atmosphere-v2" data-window-open={windowOpen} viewBox="0 0 1000 700" preserveAspectRatio="none" aria-hidden={interactive?undefined:true}>
  <defs>
   <Gradient id={id+'-sky'} colours={p.sky}/>
   {[0,1,2].map((index)=><Gradient key={index} id={id+'-ground-'+index} colours={[p.land[0],p.land[index],p.land[2]]}/>)}
   <Gradient id={id+'-water'} colours={theme==='beach'?['#b4b5c3','#758f9f','#496f87']:['#aec9c4','#699eac','#386c89']}/>
   <Gradient id={id+'-fade-ground'} colours={['#00000000',p.land[0]+'35',p.land[1]+'b0',p.land[2]]}/>
   <Gradient id={id+'-glass'} colours={['#5f86a0','#a9b7b9','#ddd2bd']}/>
   <Gradient id={id+'-wood'} colours={['#d6b18b','#a87e5b','#765b48']}/>
   <radialGradient id={id+'-light'} cx={theme==='beach'?'.27':'.73'} cy=".59" r=".73"><stop stopColor={p.light} stopOpacity=".5"/><stop offset=".48" stopColor={p.light} stopOpacity=".12"/><stop offset="1" stopColor={p.light} stopOpacity="0"/></radialGradient>
   <radialGradient id={id+'-mist'}><stop stopColor={p.mist} stopOpacity=".65"/><stop offset=".58" stopColor={p.mist} stopOpacity=".22"/><stop offset="1" stopColor={p.mist} stopOpacity="0"/></radialGradient>
   <radialGradient id={id+'-cloud'}><stop stopColor="#ffebe0" stopOpacity=".65"/><stop offset=".45" stopColor="#f4e5e1" stopOpacity=".3"/><stop offset="1" stopColor="#dde3e7" stopOpacity="0"/></radialGradient>
   <filter id={id+'-soft'} x="-25%" y="-80%" width="150%" height="260%"><feGaussianBlur stdDeviation="14"/></filter>
   <filter id={id+'-far'} x="-10%" y="-20%" width="120%" height="140%"><feGaussianBlur stdDeviation="3"/></filter>
   <filter id={id+'-grain'}><feTurbulence type="fractalNoise" baseFrequency=".72" numOctaves="3" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncA type="linear" slope=".035"/></feComponentTransfer><feBlend in="SourceGraphic" mode="soft-light"/></filter>
   {space&&<>
    <radialGradient id={id+'-core'}><stop stopColor="#ffe7ce" stopOpacity=".75"/><stop offset=".18" stopColor="#e0b6c4" stopOpacity=".62"/><stop offset=".48" stopColor="#8c719c" stopOpacity=".35"/><stop offset="1" stopColor="#684d88" stopOpacity="0"/></radialGradient>
    <linearGradient id={id+'-band'} x1="0" y1="1" x2="1" y2="0"><stop stopColor="#375d9b" stopOpacity=".2"/><stop offset=".3" stopColor="#9e81a2" stopOpacity=".6"/><stop offset=".56" stopColor="#f1d5be" stopOpacity=".65"/><stop offset=".76" stopColor="#9c7ba8" stopOpacity=".5"/><stop offset="1" stopColor="#387eac" stopOpacity=".3"/></linearGradient>
    <filter id={id+'-nebula'} x="-25%" y="-35%" width="150%" height="170%"><feTurbulence type="fractalNoise" baseFrequency=".008 .018" numOctaves="3" seed="17" result="cloud"/><feDisplacementMap in="SourceGraphic" in2="cloud" scale="95" xChannelSelector="R" yChannelSelector="G"/><feGaussianBlur stdDeviation="12"/></filter>
    <linearGradient id={id+'-meteor'}><stop stopColor="#d5efff" stopOpacity="0"/><stop offset="1" stopColor="#fff4e6" stopOpacity=".9"/></linearGradient>
   </>}
  </defs>
  <path d="M0 0H1000V700H0Z" fill={url('sky')}/>
  <path d="M0 0H1000V700H0Z" fill={url('light')}/>
  {!space&&theme!=='underground'&&theme!=='room'&&<g opacity={theme==='night'?'.12':'.32'}>
   <ellipse cx="190" cy="240" rx="440" ry="115" fill={url('cloud')}/><ellipse cx="810" cy="185" rx="380" ry="88" fill={url('cloud')}/><ellipse cx="570" cy="380" rx="590" ry="70" fill={url('mist')}/>
  </g>}
  {['night','morning','rain'].includes(theme)&&<>
   <path d="M0 380H1000V700H0Z" fill={url('fade-ground')}/>
   {theme!=='night'&&terrain('M-50 603C160 589 330 612 500 598S807 579 1050 601V740H-50Z',1,.5)}
   {haze(568,.5)}
   {theme==='night'&&Array.from({length:11},(_,i)=><circle key={i} cx={55+noise(i+11)*895} cy={35+noise(i+53)*340} r={i%4===0?1.45:.8} fill="#e6dfdf" opacity={.26+noise(i+7)*.3}/>)}
   {theme==='rain'&&<g className="atmosphere-rain" stroke="#e5edf0" opacity=".17">{Array.from({length:44},(_,i)=><path key={i} d={`M${noise(i+6)*1020} ${noise(i+30)*650}l-4 18`}/>)}</g>}
  </>}
  {['coast','beach'].includes(theme)&&<>
   <path d="M0 405C300 399 720 410 1000 401V700H0Z" fill={url('water')}/>
   {haze(410,.65)}
   {terrain(theme==='beach'?'M-30 431C185 475 315 529 476 543S792 516 1050 572V740H-30Z':'M-30 590C160 552 272 556 467 602S763 633 1050 569V740H-30Z',0)}
   <path d={theme==='beach'?'M-20 463C154 499 330 567 526 572S822 559 1030 612V740H-20Z':'M-20 626C185 587 349 624 516 647S846 643 1030 609V740H-20Z'} fill={url('ground-1')} opacity=".48"/>
   <ellipse cx={theme==='beach'?270:775} cy="530" rx="330" ry="88" fill={url('mist')} opacity=".4"/>
  </>}
  {theme==='desert'&&<>
   {terrain('M-60 486C119 450 278 454 450 480S787 510 1060 458V740H-60Z',0,.74)}
   {terrain('M-60 570C199 489 408 536 624 567S895 535 1060 551V740H-60Z',1)}
   {terrain('M-60 643C211 655 346 604 547 604S838 683 1060 627V740H-60Z',2)}
   {haze(489,.45)}
   <path d="M30 654C290 650 330 612 500 620" fill="none" stroke="#ebc7a3" strokeWidth="2" opacity=".16"/>
  </>}
  {theme==='rainforest'&&<>
   <g filter={url('far')}>{terrain('M-60 418C75 358 136 438 225 394S350 434 455 393 602 433 711 371 885 437 1060 373V740H-60Z',0,.65)}</g>
   {haze(443,.8)}
   {terrain('M-60 548C94 443 158 525 278 479S414 554 534 502 690 510 782 455 934 500 1060 454V740H-60Z',1,.86)}
   {haze(530,.6)}
   {terrain('M-60 638C172 605 291 663 462 621S780 632 1060 602V740H-60Z',2)}
   <ellipse cx="690" cy="530" rx="440" ry="180" fill={url('mist')} opacity=".38"/>
  </>}
  {['mountains','snow'].includes(theme)&&<>
   <g filter={url('far')}>{terrain('M-60 485C87 472 167 291 297 346S453 449 595 351 783 262 1060 421V740H-60Z',0,.68)}</g>
   {haze(453,.62)}
   {terrain(HILLS[0],1,.78)}{haze(524,.48)}{terrain(HILLS[1],2,.7)}
   {theme==='snow'&&<path d="M-60 600C140 542 282 581 471 586S780 545 1060 614V740H-60Z" fill={url('ground-0')} opacity=".86"/>}
   {haze(616,.35)}
  </>}
  {theme==='river'&&<>
   {terrain(HILLS[1],0,.76)}{haze(528,.68)}
   {terrain('M-40 616C130 548 299 562 477 584S797 551 1040 579V740H-40Z',1)}
   <path d="M557 562C445 583 413 602 531 620S786 656 688 700H167C465 649 472 654 425 627S447 576 557 562Z" fill={url('water')}/>
   <path d="M486 617C580 628 699 644 728 662" fill="none" stroke="#d7d6c0" strokeWidth="11" opacity=".13" filter={url('soft')}/>
   {haze(578,.47)}
  </>}
  {theme==='sky'&&<>
   <path d="M0 445H1000V700H0Z" fill={url('fade-ground')} opacity=".75"/>
   {[[-40,563,370,104],[290,625,410,144],[760,542,490,120],[1040,652,430,146]].map(([x,y,rx,ry],i)=><ellipse key={i} cx={x} cy={y} rx={rx} ry={ry} fill={url('cloud')}/>)}
   <ellipse cx="610" cy="584" rx="780" ry="110" fill={url('mist')} opacity=".7"/>
  </>}
  {theme==='underground'&&<>
   <path d="M-20-20H1020V45C835 6 788 119 611 74S355 127 191 66 29 167-20 228Z" fill="#142732" opacity=".84"/>
   <path d="M-30 0C56 69 42 167 91 271S111 432 46 542L-30 700Z" fill={url('ground-2')} opacity=".66"/>
   <path d="M1040 4C930 104 990 207 921 316S932 547 1040 621Z" fill="#193b43" opacity=".7"/>
   <ellipse cx="590" cy="438" rx="355" ry="218" fill={url('mist')} opacity=".66"/>
   {terrain('M-40 645C167 603 251 654 457 636S818 610 1040 642V740H-40Z',1)}
   {haze(625,.8)}
   <g fill="#b5e2c9">{Array.from({length:14},(_,i)=><circle key={i} cx={95+noise(i+43)*790} cy={185+noise(i+64)*435} r={.8+noise(i+90)*1.7} opacity={.12+noise(i+10)*.35}/>)}</g>
   {interactive&&<g className="background-hit cave-ceiling-hit" role="button" tabIndex="0" aria-label="轻触洞顶，落下岩石碎屑" onClick={rockfall} onKeyDown={keyActivate(rockfall)}><path d="M30 0H970V128H30Z" fill="transparent"/></g>}
   {!!debris&&<g key={debris} className="cave-debris" aria-hidden="true">{Array.from({length:9},(_,i)=><path className="cave-fragment" key={i} d="M-3-2 2-4 5 0 2 4-4 2Z" fill={i%2?'#86a2a0':'#bac3af'} style={{'--fall-x':(190+noise(i+debris)*620)+'px','--fall-delay':(i*.05)+'s','--fall-drift':(noise(i+4)*50-25)+'px'}}/>)}</g>}
  </>}
  {theme==='room'&&<>
   <ellipse cx="770" cy="300" rx="580" ry="510" fill={url('mist')} opacity=".6"/>
   <path d="M0 572H1000V700H0Z" fill={url('ground-0')}/>
   <path d="M0 581H1000M0 638H1000M160 579 87 700M390 579 370 700M645 579 670 700M870 579 955 700" stroke="#5c4d47" opacity=".1" strokeWidth="2"/>
   <path d="M583 404 271 700H810L851 404Z" fill={p.light} opacity={windowOpen?'.16':'.08'} filter={url('soft')}/>
   <rect x="560" y="99" width="302" height="334" rx="10" fill={url('wood')}/>
   <rect x="574" y="112" width="274" height="302" rx="4" fill={url('glass')}/>
   <path d="M575 349C638 322 683 346 736 331S810 327 848 342V414H575Z" fill="#9cae9f" opacity=".65"/>
   <ellipse cx="710" cy="354" rx="125" ry="40" fill={url('mist')}/>
   <g className="room-window-pane pane-left"><path d="M573 112H710V414H573Z" fill="#c5d8db" fillOpacity=".16" stroke="#ddc3a0" strokeWidth="7"/><path d="M575 262H708" stroke="#ddc3a0" strokeWidth="6"/></g>
   <g className="room-window-pane pane-right"><path d="M711 112H848V414H711Z" fill="#c5d8db" fillOpacity=".2" stroke="#ddc3a0" strokeWidth="7"/><path d="M714 262H847" stroke="#ddc3a0" strokeWidth="6"/></g>
   <path d="M550 438H874" stroke="#b79170" strokeWidth="13" strokeLinecap="round"/>
   <path className="room-curtain curtain-left" d="M539 91C516 206 543 284 529 387L575 381C549 267 583 182 573 91Z" fill="#c4a5a0"/>
   <path className="room-curtain curtain-right" d="M854 91C842 179 874 269 850 384L900 389C889 279 912 195 892 91Z" fill="#c4a5a0"/>
   {interactive&&<g className="background-hit room-window-hit" role="button" tabIndex="0" aria-label={windowOpen?'关闭窗户':'打开窗户'} aria-pressed={windowOpen} onClick={()=>setWindowOpen(value=>!value)} onKeyDown={keyActivate(()=>setWindowOpen(value=>!value))}><rect x="568" y="105" width="285" height="322" rx="8" fill="transparent"/></g>}
  </>}
  {space&&<>
   <g className="galaxy-clouds" filter={url('nebula')}>
    <path d="M-160 655C175 480 485 335 1160-55" fill="none" stroke={url('band')} strokeWidth="235" opacity=".72"/>
    <ellipse cx="536" cy="342" rx="466" ry="127" transform="rotate(-31 536 342)" fill={url('core')}/>
    <ellipse cx="173" cy="475" rx="290" ry="84" transform="rotate(-29 173 475)" fill={url('core')} opacity=".5"/>
   </g>
   <g opacity=".54" filter={url('soft')} fill="#0e142b"><path d="M-100 651C157 505 322 409 427 387S573 298 721 241 927 107 1100 52L1090 92C867 158 795 259 666 289S464 429 363 445 119 581-100 684Z"/><path d="M261 501C385 408 416 371 487 325S573 283 628 224L643 250C562 320 514 349 467 393S381 453 280 516Z"/></g>
   {[0,1,2].map(layer=><g key={layer} className={'galaxy-stars galaxy-stars-'+layer} fill={layer===1?'#ffdfc2':'#dce9ff'}>{Array.from({length:thumbnail?38:150},(_,i)=>{const n=i+layer*177,x=noise(n+3)*1000,y=noise(n+187)*700;return <circle key={i} cx={x} cy={y} r={.3+noise(n+82)*(layer===2?1.15:.7)} opacity={.16+noise(n+37)*.59}/>;})}</g>)}
   <g className="galaxy-band-stars" fill="#f3e1d7">{Array.from({length:thumbnail?45:205},(_,i)=>{const x=noise(i+803)*1100-50,y=610-x*.58+(noise(i+421)-.5)*110;return <circle key={i} cx={x} cy={y} r={.3+noise(i+71)*.65} opacity={.17+noise(i+127)*.4}/>;})}</g>
   <g className="galaxy-meteors" stroke={url('meteor')} strokeWidth="1.4" strokeLinecap="round"><path className="galaxy-meteor meteor-one" d="M0 0 94 38"/><path className="galaxy-meteor meteor-two" d="M0 0 73 30"/></g>
   {!!flight&&<g key={flight} className="galaxy-flight" stroke="#dce9f5" strokeLinecap="round">{Array.from({length:18},(_,i)=>{const angle=i*Math.PI/9,x=Math.cos(angle),y=Math.sin(angle);return <path key={i} d={`M${500+x*170} ${350+y*120}l${x*90} ${y*65}`} style={{'--flight-x':x*270+'px','--flight-y':y*190+'px','--flight-delay':(i%3)*.06+'s'}}/>;})}</g>}
   {interactive&&<g className="background-hit galaxy-travel-hit" role="button" tabIndex="0" aria-label="穿行银河" onClick={travel} onKeyDown={keyActivate(travel)}><path d="M0 0H1000V700H0Z" fill="transparent"/></g>}
  </>}
  {!thumbnail&&<path d="M0 0H1000V700H0Z" fill="transparent" filter={url('grain')} pointerEvents="none"/>}
 </svg>;
});
