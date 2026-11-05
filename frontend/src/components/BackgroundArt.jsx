import {memo,useEffect,useId,useRef,useState} from 'react';
import './BackgroundArt.css';

// Independently shaded, opaque ground keeps a clear edge against the sky.
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
const OBSERVATION_STARS=[{x:157,y:508},{x:309,y:398},{x:449,y:367},{x:604,y:252},{x:728,y:206},{x:873,y:93}];
const limit=(value,min,max)=>Math.min(max,Math.max(min,value));

export default memo(function BackgroundArt({item,thumbnail=false,interactive=!thumbnail,demo=0}){
 const id='atmos-'+useId().replaceAll(':',''),theme=item?.theme||item?.shape?.replace('background-','')||'morning',p=PALETTES[theme]||PALETTES.morning;
 const ref=useRef(null),timers=useRef(new Set()),fallSequence=useRef(0),drag=useRef(null),cameraRef=useRef({x:0,y:0,zoom:1.08}),[windowOpen,setWindowOpen]=useState(false),[debris,setDebris]=useState([]),[camera,setCamera]=useState(cameraRef.current),[dragging,setDragging]=useState(false),[focusedStar,setFocusedStar]=useState(null);
 const url=name=>`url(#${id}-${name})`,space=theme==='galaxy';
 useEffect(()=>()=>{for(const timer of timers.current)clearTimeout(timer);},[]);
 useEffect(()=>{
  if(!space||!interactive)return;
  const svg=ref.current,surface=svg.closest('.sticker-surface')||svg.parentElement;let frame=0;
  const move=event=>{if(frame||drag.current)return;const x=event.clientX,y=event.clientY;frame=requestAnimationFrame(()=>{frame=0;const b=svg.getBoundingClientRect();svg.style.setProperty('--space-x',((x-b.left)/b.width-.5)*10+'px');svg.style.setProperty('--space-y',((y-b.top)/b.height-.5)*8+'px');});};
  const leave=()=>{svg.style.setProperty('--space-x','0px');svg.style.setProperty('--space-y','0px');};
  surface.addEventListener('pointermove',move,{passive:true});surface.addEventListener('pointerleave',leave);
  return()=>{cancelAnimationFrame(frame);surface.removeEventListener('pointermove',move);surface.removeEventListener('pointerleave',leave);};
 },[space,interactive]);
 const rockfall=(side='ceiling',event)=>{
  const point=ref.current?.createSVGPoint();if(point&&event?.clientX!=null){point.x=event.clientX;point.y=event.clientY;}
  const local=point&&event?.clientX!=null?point.matrixTransform(ref.current.getScreenCTM().inverse()):null;
  const x=side==='left'?limit(local?.x??65,24,120):side==='right'?limit(local?.x??935,880,976):limit(local?.x??500,145,855);
  const y=side==='ceiling'?limit(local?.y??105,30,165):limit(local?.y??300,140,485),key=++fallSequence.current;
  setDebris(previous=>[...previous.slice(-5),{key,side,x,y}]);
  const timer=setTimeout(()=>{setDebris(previous=>previous.filter(fall=>fall.key!==key));timers.current.delete(timer);},2100);timers.current.add(timer);
 };
 const moveCamera=value=>{cameraRef.current=value;setCamera(value);};
 const focusStar=index=>{const star=OBSERVATION_STARS[index];setFocusedStar(index);moveCamera({x:limit((500-star.x)*.18,-58,58),y:limit((350-star.y)*.18,-40,40),zoom:1.16});};
 const resetCamera=()=>{setFocusedStar(null);moveCamera({x:0,y:0,zoom:1.08});};
 const startPan=event=>{if(event.button!==0)return;event.stopPropagation();event.preventDefault();event.currentTarget.setPointerCapture(event.pointerId);drag.current={x:event.clientX,y:event.clientY,camera:cameraRef.current,moved:false,star:event.target.closest('[data-observation-star]')?.dataset.observationStar};setDragging(true);};
 const pan=event=>{if(!drag.current)return;const b=ref.current.getBoundingClientRect(),dx=event.clientX-drag.current.x,dy=event.clientY-drag.current.y;if(Math.hypot(dx,dy)>4)drag.current.moved=true;moveCamera({...drag.current.camera,x:limit(drag.current.camera.x+dx/b.width*1000,-58,58),y:limit(drag.current.camera.y+dy/b.height*700,-40,40)});if(drag.current.moved)setFocusedStar(null);};
 const finishPan=event=>{if(!drag.current)return;const current=drag.current;drag.current=null;setDragging(false);if(!current.moved&&current.star!=null)focusStar(Number(current.star));if(event.currentTarget.hasPointerCapture(event.pointerId))event.currentTarget.releasePointerCapture(event.pointerId);};
 const cameraKey=event=>{if(['Home','Escape'].includes(event.key)){event.preventDefault();resetCamera();}else if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key)){event.preventDefault();setFocusedStar(null);moveCamera({...cameraRef.current,x:limit(cameraRef.current.x+(event.key==='ArrowLeft'?16:event.key==='ArrowRight'?-16:0),-58,58),y:limit(cameraRef.current.y+(event.key==='ArrowUp'?12:event.key==='ArrowDown'?-12:0),-40,40)});}};
 useEffect(()=>{if(!demo)return;if(theme==='underground')rockfall(demo%2?'left':'right');if(theme==='room')setWindowOpen(value=>!value);if(space)focusStar((demo-1)%OBSERVATION_STARS.length);},[demo,theme]);
 const keyActivate=action=>event=>{if(['Enter',' '].includes(event.key)){event.preventDefault();action();}};
 const terrain=(path,index,opacity=1)=><path key={index} d={path} fill={url('ground-'+index)} opacity={opacity}/>;
 const haze=(y,opacity=.35)=> <ellipse cx="510" cy={y} rx="690" ry="40" fill={url('mist')} opacity={opacity}/>;
 return <svg ref={ref} className={'scene-background-art atmosphere-art'+(thumbnail?' scene-background-thumbnail':'')} data-background-theme={theme} data-background-version="atmosphere-v3" data-window-open={windowOpen} data-dragging={dragging} data-focused-star={focusedStar??''} viewBox="0 0 1000 700" preserveAspectRatio="none" aria-hidden={interactive?undefined:true}>
  <defs>
   <Gradient id={id+'-sky'} colours={p.sky}/>
   {[p.land,p.land,[p.land[1],p.land[2]]].map((colours,index)=><Gradient key={index} id={id+'-ground-'+index} colours={colours}/>)}
   <Gradient id={id+'-water'} colours={theme==='beach'?['#b4b5c3','#758f9f','#496f87']:['#aec9c4','#699eac','#386c89']}/>
   <Gradient id={id+'-snow-light'} colours={['#f6ebe4','#e6e9eb','#bdcedd']}/>
   <Gradient id={id+'-snow-shadow'} colours={['#91adc6','#a9bdce','#d0dbe2']}/>
   <Gradient id={id+'-cloud-body'} colours={['#f8e9e0','#e9e3e7','#bcc9da','#90abc7']}/>
   <Gradient id={id+'-cloud-shadow'} colours={['#d5d7e4','#b9c7db','#8da8c6']}/>
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
    <radialGradient id={id+'-star-glow'}><stop stopColor="#fff3df" stopOpacity=".65"/><stop offset=".18" stopColor="#e6d5f4" stopOpacity=".22"/><stop offset="1" stopColor="#b8b9ed" stopOpacity="0"/></radialGradient>
   </>}
  </defs>
  <path d="M0 0H1000V700H0Z" fill={url('sky')}/>
  <path d="M0 0H1000V700H0Z" fill={url('light')}/>
  {!space&&theme!=='underground'&&theme!=='room'&&<g opacity={theme==='night'?'.12':'.32'}>
   <ellipse cx="190" cy="240" rx="440" ry="115" fill={url('cloud')}/><ellipse cx="810" cy="185" rx="380" ry="88" fill={url('cloud')}/><ellipse cx="570" cy="380" rx="590" ry="70" fill={url('mist')}/>
  </g>}
  {['night','morning','rain'].includes(theme)&&<>
   {haze(510,.38)}
   {terrain(theme==='morning'?'M-30 520C170 501 342 534 545 514S844 501 1030 520V740H-30Z':theme==='rain'?'M-30 534C219 518 371 541 558 528S856 526 1030 533V740H-30Z':'M-30 524C235 514 352 533 573 521S830 515 1030 525V740H-30Z',0)}
   {terrain('M-30 638C213 610 381 646 567 625S864 621 1030 642V740H-30Z',1,.45)}
   {theme==='night'&&Array.from({length:11},(_,i)=><circle key={i} cx={55+noise(i+11)*895} cy={35+noise(i+53)*340} r={i%4===0?1.45:.8} fill="#e6dfdf" opacity={.26+noise(i+7)*.3}/>)}
   {theme==='rain'&&<g className="atmosphere-rain" stroke="#e5edf0" opacity=".17">{Array.from({length:44},(_,i)=><path key={i} d={`M${noise(i+6)*1020} ${noise(i+30)*650}l-4 18`}/>)}</g>}
  </>}
  {['coast','beach'].includes(theme)&&<>
   <path d="M0 405C300 399 720 410 1000 401V700H0Z" fill={url('water')}/>
   {haze(399,.22)}
   {terrain(theme==='beach'?'M-30 431C185 475 315 529 476 543S792 516 1050 572V740H-30Z':'M-30 590C160 552 272 556 467 602S763 633 1050 569V740H-30Z',0)}
   <path d={theme==='beach'?'M-20 463C154 499 330 567 526 572S822 559 1030 612V740H-20Z':'M-20 626C185 587 349 624 516 647S846 643 1030 609V740H-20Z'} fill={url('ground-1')} opacity=".48"/>
   <ellipse cx={theme==='beach'?270:775} cy="530" rx="330" ry="88" fill={url('mist')} opacity=".4"/>
  </>}
  {theme==='desert'&&<>
   {terrain('M-60 486C119 450 278 454 450 480S787 510 1060 458V740H-60Z',0)}
   {terrain('M-60 570C199 489 408 536 624 567S895 535 1060 551V740H-60Z',1)}
   {terrain('M-60 643C211 655 346 604 547 604S838 683 1060 627V740H-60Z',2)}
   <path d="M30 654C290 650 330 612 500 620" fill="none" stroke="#ebc7a3" strokeWidth="2" opacity=".16"/>
  </>}
  {theme==='rainforest'&&<>
   <g filter={url('far')} opacity=".3" fill="#315e53">{Array.from({length:18},(_,i)=>{const x=i*61-10,w=7+noise(i+51)*10;return <path key={i} d={`M${x} 135Q${x-8} 340 ${x-3} 552h${w+12}Q${x+w-3} 335 ${x+w} 135Z`}/>;})}</g>
   <path d="M-20 0H1020V113Q947 188 883 129Q823 207 757 138Q698 182 637 117Q567 164 502 112Q423 187 360 131Q283 203 216 142Q140 214 68 151Q15 189-20 141Z" fill={url('ground-1')} opacity=".83"/>
   <ellipse cx="535" cy="349" rx="405" ry="207" fill={url('mist')} opacity=".48"/>
   <g fill="#28564c">{[[67,25],[205,17],[791,20],[934,29]].map(([x,w],i)=><path key={x} d={`M${x} 85Q${x-14} 295 ${x-5} 550l-28 37 57-16 22 14-21-38Q${x+w-7} 290 ${x+w} 85Z`} opacity={i%2?'.54':'.8'}/>)}</g>
   {terrain('M-30 548C147 533 268 568 445 552S785 529 1030 555V740H-30Z',1)}
   <path d="M520 550C420 577 366 613 409 700H598C504 626 494 587 563 551Z" fill="#789582" opacity=".21"/>
   <g fill={url('ground-2')}>{[[67,651,1],[172,698,.8],[854,688,1.1],[957,623,.8]].map(([x,y,s])=><g key={x} transform={`translate(${x} ${y}) scale(${s})`}><path d="M0 4Q-20-69-79-85Q-41-90-5-47Q-7-110-32-135Q14-114 14-55Q37-102 80-102Q35-79 15-18Q63-54 107-40Q56-26 0 4Z"/><path d="M0 4Q9-62-11-109" fill="none" stroke="#547a61" strokeWidth="2"/></g>)}</g>
   <path d="M-20 685Q151 650 298 690T621 681T1020 678V720H-20Z" fill={url('ground-2')}/>
  </>}
  {theme==='mountains'&&<>
   <g filter={url('far')}>{terrain('M-60 485C87 472 167 291 297 346S453 449 595 351 783 262 1060 421V740H-60Z',0)}</g>
   {haze(453,.62)}
   {terrain(HILLS[0],1)}{haze(524,.3)}{terrain(HILLS[1],2)}
  </>}
  {theme==='snow'&&<>
   <path d="M-30 510C73 482 128 419 214 404S321 288 394 262C430 242 465 262 489 300S549 359 584 373C641 392 665 448 737 458S896 409 1030 464V740H-30Z" fill={url('snow-light')}/>
   <path d="M398 262C385 328 421 359 397 408S358 475 388 537L666 589C608 513 581 449 544 403S459 348 454 289Q429 254 398 262Z" fill={url('snow-shadow')}/>
   <path d="M190 412C285 420 337 362 391 348M396 412C443 437 457 476 491 493M476 333C498 377 545 379 566 414" fill="none" stroke="#f6f0ed" strokeWidth="6" opacity=".55"/>
   <path d="M-30 569C138 539 266 565 413 558S660 506 799 536 934 552 1030 530V740H-30Z" fill={url('snow-light')}/>
   <path d="M-30 655C166 573 367 609 503 619S804 590 1030 625V740H-30Z" fill={url('ground-0')}/>
   <path d="M73 670C218 637 350 654 441 642M612 588C723 566 811 577 899 583" fill="none" stroke="#f6efeb" strokeWidth="3" opacity=".55"/>
  </>}
  {theme==='river'&&<>
   {terrain(HILLS[1],0)}{haze(528,.4)}
   {terrain('M-40 616C130 548 299 562 477 584S797 551 1040 579V740H-40Z',1)}
   <path d="M557 562C445 583 413 602 531 620S786 656 688 700H167C465 649 472 654 425 627S447 576 557 562Z" fill={url('water')}/>
   <path d="M486 617C580 628 699 644 728 662" fill="none" stroke="#d7d6c0" strokeWidth="11" opacity=".13" filter={url('soft')}/>
  </>}
  {theme==='sky'&&<>
   <g filter={url('far')}><path d="M-40 489Q27 430 110 458Q160 397 237 433Q295 381 354 422Q425 402 474 453Q528 415 586 442Q661 388 732 435Q818 395 884 444Q958 424 1040 480V740H-40Z" fill={url('cloud-shadow')}/></g>
   <path d="M-40 596Q-5 506 80 524Q100 448 178 474Q234 420 294 469Q353 452 383 505Q431 477 483 515Q541 475 598 521Q629 475 691 487Q741 416 810 463Q871 441 905 496Q979 460 1040 541V740H-40Z" fill={url('cloud-body')}/>
   <g fill={url('cloud')}><ellipse cx="167" cy="490" rx="180" ry="69"/><ellipse cx="787" cy="479" rx="184" ry="78"/><ellipse cx="425" cy="556" rx="211" ry="65"/></g>
   <path d="M-40 687Q22 608 109 630Q172 557 249 610Q332 550 408 613Q478 583 526 627Q589 589 655 626Q707 558 791 596Q858 563 906 619Q980 572 1040 633V740H-40Z" fill={url('cloud-body')}/>
   <path d="M39 612Q109 590 160 614M257 571Q306 560 339 584M691 594Q744 566 784 586M835 503Q866 493 891 513" fill="none" stroke="#fff0e5" strokeWidth="9" strokeLinecap="round" opacity=".38" filter={url('far')}/>
  </>}
  {theme==='underground'&&<>
   <path d="M-30-20H1030V700H-30ZM105 610Q71 419 141 260Q236 115 449 127Q676 82 839 225Q950 349 904 610Z" fill="#16303b" fillRule="evenodd" opacity=".63"/>
   <path d="M-30-20H1030V700H-30ZM71 613 64 484 85 375 72 298 121 184 182 132 296 80 421 91 547 56 688 84 810 130 887 218 920 347 906 461 942 614Z" fill={url('ground-2')} fillRule="evenodd"/>
   <path d="M-10 240 65 271 93 208 132 159 234 105 340 116 433 82 544 99 641 64 769 120 864 197 919 293 1010 255M-10 394 65 417 83 350M916 391 1010 368" fill="none" stroke="#65908c" strokeWidth="4" opacity=".18"/>
   <path d="M217 101 238 162 259 107M665 83 682 137 702 93M793 130 811 180 827 154" fill="#284950"/>
   <ellipse cx="542" cy="424" rx="320" ry="190" fill={url('mist')} opacity=".45"/>
   {terrain('M-40 610 82 591 172 606 273 594 392 612 493 601 642 610 788 592 899 606 1040 590V740H-40Z',1)}
   <path d="M352 626Q518 609 676 631L713 658Q510 680 314 653Z" fill="#72a8a2" opacity=".2"/>
   <g fill="#26494d"><path d="M16 625 52 590 88 608 111 636ZM842 639 884 614 925 634ZM218 670 239 648 270 654 281 680Z"/></g>
   <g fill="#b5e2c9">{Array.from({length:14},(_,i)=><circle key={i} cx={95+noise(i+43)*790} cy={185+noise(i+64)*435} r={.8+noise(i+90)*1.7} opacity={.12+noise(i+10)*.35}/>)}</g>
   {interactive&&[['left','轻触左侧洞壁，左侧落石','M0 140H140L105 570H0Z'],['right','轻触右侧洞壁，右侧落石','M860 140H1000V570H905Z'],['ceiling','轻触洞顶，落下岩石碎屑','M140 0H860V166H140Z']].map(([side,label,path])=><g key={side} className={'background-hit cave-'+side+'-hit'} role="button" tabIndex="0" aria-label={label} onClick={event=>rockfall(side,event)} onKeyDown={keyActivate(()=>rockfall(side))}><path d={path} fill="transparent"/></g>)}
   {debris.map(fall=><g key={fall.key} className="cave-debris" data-fall-side={fall.side} data-origin-x={fall.x} aria-hidden="true">{Array.from({length:8},(_,i)=><path className="cave-fragment" key={i} d="M-3-2 2-4 5 0 2 4-4 2Z" fill={i%2?'#6a8c89':'#a4b5a6'} style={{'--fall-x':(fall.x+(noise(i+fall.key)*24-12))+'px','--fall-y':fall.y+'px','--fall-end-y':(604+noise(i+6)*19)+'px','--fall-delay':(i*.035)+'s','--fall-drift':((fall.side==='left'?1:fall.side==='right'?-1:0)*(18+noise(i+4)*28)+(noise(i+15)-.5)*12)+'px'}}/>)}<ellipse className="cave-impact" cx={fall.x+(fall.side==='left'?28:fall.side==='right'?-28:0)} cy="615" rx="28" ry="5" fill={url('mist')}/></g>)}
  </>}
  {theme==='room'&&<>
   <ellipse cx="770" cy="300" rx="580" ry="510" fill={url('mist')} opacity=".6"/>
   <path d="M0 572H1000V700H0Z" fill={url('ground-0')}/>
   <path d="M0 581H1000M0 638H1000M160 579 87 700M390 579 370 700M645 579 670 700M870 579 955 700" stroke="#5c4d47" opacity=".1" strokeWidth="2"/>
   <path d="M691 407 459 700H859L889 407Z" fill={p.light} opacity={windowOpen?'.16':'.08'} filter={url('soft')}/>
   <rect x="683" y="177" width="214" height="250" rx="5" fill={url('wood')}/>
   <rect className="room-window-aperture" x="694" y="188" width="192" height="226" rx="2" fill={url('glass')}/>
   <path d="M694 357C739 337 776 361 813 349S861 347 886 358V414H694Z" fill="#9cae9f"/>
   <ellipse cx="790" cy="366" rx="91" ry="29" fill={url('mist')}/>
   <g transform="translate(694 188)"><g className="room-window-pane pane-left"><path d="M0 0H96V226H0Z" fill="#c5d8db" fillOpacity=".16" stroke="#ddc3a0" strokeWidth="5"/><path d="M0 113H96" stroke="#ddc3a0" strokeWidth="4"/></g></g>
   <g transform="translate(886 188)"><g className="room-window-pane pane-right"><path d="M-96 0H0V226H-96Z" fill="#c5d8db" fillOpacity=".16" stroke="#ddc3a0" strokeWidth="5"/><path d="M-96 113H0" stroke="#ddc3a0" strokeWidth="4"/></g></g>
   <path d="M675 431H905" stroke="#b79170" strokeWidth="9" strokeLinecap="round"/>
   <path className="room-curtain curtain-left" d="M665 173C655 249 674 323 657 399L691 396C678 323 696 242 691 173Z" fill="#c4a5a0"/>
   <path className="room-curtain curtain-right" d="M889 173C884 242 902 323 889 396L923 399C906 323 925 249 915 173Z" fill="#c4a5a0"/>
   <path d="M657 172H923" stroke="#977563" strokeWidth="5" strokeLinecap="round"/>
   {interactive&&<g className="background-hit room-window-hit" role="button" tabIndex="0" aria-label={windowOpen?'关闭窗户':'打开窗户'} aria-pressed={windowOpen} onClick={()=>setWindowOpen(value=>!value)} onKeyDown={keyActivate(()=>setWindowOpen(value=>!value))}><rect x="680" y="180" width="220" height="247" rx="8" fill="transparent"/></g>}
  </>}
  {space&&<>
   <g className="galaxy-camera" style={{transform:`translate(${camera.x}px,${camera.y}px) translate(500px,350px) scale(${camera.zoom}) translate(-500px,-350px)`}}>
   <g className="galaxy-clouds" filter={url('nebula')}>
    <path d="M-160 655C175 480 485 335 1160-55" fill="none" stroke={url('band')} strokeWidth="235" opacity=".72"/>
    <ellipse cx="536" cy="342" rx="466" ry="127" transform="rotate(-31 536 342)" fill={url('core')}/>
    <ellipse cx="173" cy="475" rx="290" ry="84" transform="rotate(-29 173 475)" fill={url('core')} opacity=".5"/>
   </g>
   <g opacity=".54" filter={url('soft')} fill="#0e142b"><path d="M-100 651C157 505 322 409 427 387S573 298 721 241 927 107 1100 52L1090 92C867 158 795 259 666 289S464 429 363 445 119 581-100 684Z"/><path d="M261 501C385 408 416 371 487 325S573 283 628 224L643 250C562 320 514 349 467 393S381 453 280 516Z"/></g>
   {[0,1,2].map(layer=><g key={layer} className={'galaxy-stars galaxy-stars-'+layer} fill={layer===1?'#ffdfc2':'#dce9ff'}>{Array.from({length:thumbnail?38:150},(_,i)=>{const n=i+layer*177,x=noise(n+3)*1000,y=noise(n+187)*700;return <circle key={i} cx={x} cy={y} r={.3+noise(n+82)*(layer===2?1.15:.7)} opacity={.16+noise(n+37)*.59}/>;})}</g>)}
   <g className="galaxy-band-stars" fill="#f3e1d7">{Array.from({length:thumbnail?45:205},(_,i)=>{const x=noise(i+803)*1100-50,y=610-x*.58+(noise(i+421)-.5)*110;return <circle key={i} cx={x} cy={y} r={.3+noise(i+71)*.65} opacity={.17+noise(i+127)*.4}/>;})}</g>
   <g className="galaxy-meteors" stroke={url('meteor')} strokeWidth="1.4" strokeLinecap="round"><path className="galaxy-meteor meteor-one" d="M0 0 94 38"/><path className="galaxy-meteor meteor-two" d="M0 0 73 30"/></g>
   {OBSERVATION_STARS.map((star,index)=><g key={index} className="galaxy-observation-star"><ellipse cx={star.x} cy={star.y} rx={focusedStar===index?40:13} ry={focusedStar===index?40:13} fill={url('star-glow')}/><circle cx={star.x} cy={star.y} r={index%2?1.6:2} fill="#fff0df"/>{focusedStar===index&&<path d={`M${star.x-7} ${star.y}h14M${star.x} ${star.y-7}v14`} stroke="#e8deeb" strokeWidth=".6" opacity=".55"/>}</g>)}
   </g>
   {interactive&&<g className="background-hit galaxy-observe-hit" role="group" tabIndex="0" aria-label="探索银河：拖动平移，点亮星凝视，双击或 Home 复位" onPointerDown={startPan} onPointerMove={pan} onPointerUp={finishPan} onPointerCancel={()=>{drag.current=null;setDragging(false);}} onDoubleClick={resetCamera} onKeyDown={cameraKey}>
    <path d="M0 0H1000V700H0Z" fill="transparent"/>
    {OBSERVATION_STARS.map((star,index)=><g key={index} role="button" tabIndex="0" aria-label={'凝视第 '+(index+1)+' 颗亮星'} aria-pressed={focusedStar===index} data-observation-star={index} onKeyDown={keyActivate(()=>focusStar(index))}><circle cx={500+(star.x-500)*camera.zoom+camera.x} cy={350+(star.y-350)*camera.zoom+camera.y} r="15" fill="transparent"/></g>)}
   </g>}
  </>}
  {!thumbnail&&<path d="M0 0H1000V700H0Z" fill="transparent" filter={url('grain')} pointerEvents="none"/>}
 </svg>;
});
