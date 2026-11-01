import {
 Award,BookCheck,BookMarked,BookOpen,Brain,CalendarCheck2,CalendarDays,Castle,
 CheckCheck,Compass,Cpu,Crown,Files,Flag,FlagTriangleRight,Flame,Footprints,
 Gem,Gift,GraduationCap,Infinity,Layers,Leaf,LibraryBig,ListChecks,Mountain,
 Network,Orbit,Pickaxe,ScrollText,ShieldCheck,Sprout,Swords,Timer,
 TreeDeciduous,Trophy,UserRoundCheck,RotateCcw,Braces,Languages,Hourglass,Clock3,Hash,Sticker,Palette,Undo2,Map,Sparkles,Swords as DuelSwords,MessageCircle,
} from 'lucide-react';

// Stable achievement IDs describe the action being celebrated.
const SYMBOLS={
 'moment-rebound':['rotate',RotateCcw],'moment-semicolon':['braces',Braces],
 'moment-polyglot':['languages',Languages],'moment-photo-finish':['hourglass',Hourglass],
 'moment-clock':['clock',Clock3],'moment-42':['answer',Hash],
 'moment-gallery':['stickers',Sticker],'moment-rainbow':['palette',Palette],
 'moment-upside-down':['rotate',RotateCcw],'moment-returned':['undo',Undo2],
 'moment-wiki-trip':['map',Map],'moment-duel-tie':['sparkles',Sparkles],
 'moment-duel-rebound':['duel',DuelSwords],'moment-prophet':['message',MessageCircle],
 'official-1':['sprout',Sprout],'official-10':['checks',CheckCheck],
 'official-25':['files',Files],'official-50':['books',BookOpen],
 'official-100':['library',LibraryBig],'official-200':['layers',Layers],
 'official-300':['bookmarked',BookMarked],'official-500':['book-check',BookCheck],
 'official-750':['shield',ShieldCheck],'official-1000':['graduation',GraduationCap],
 'official-1500':['trophy',Trophy],'official-2000':['crown',Crown],
 'difficulty-1500':['footprints',Footprints],'difficulty-1800':['pickaxe',Pickaxe],
 'difficulty-2100':['mountain',Mountain],'difficulty-2400':['gem',Gem],
 'difficulty-2700':['swords',Swords],'difficulty-3000':['castle',Castle],
 'difficulty-3300':['crown',Crown],'difficulty-3600':['summit-flag',FlagTriangleRight],
 'independent-5':['user-check',UserRoundCheck],'independent-25':['brain',Brain],
 'independent-100':['compass',Compass],'independent-300':['cpu',Cpu],
 'independent-1000':['graduation',GraduationCap],
 'contest-1':['flag',Flag],'contest-5':['timer',Timer],
 'streak-3':['flame',Flame],'streak-7':['calendar-check',CalendarCheck2],
 'streak-30':['calendar',CalendarDays],'streak-90':['tree',TreeDeciduous],
 'streak-180':['leaf',Leaf],'streak-365':['orbit',Orbit],
 'streak-730':['infinity',Infinity],'platforms-2':['network',Network],
 'missions-1':['gift',Gift],'missions-10':['list-checks',ListChecks],
 'missions-50':['scroll',ScrollText],
};

export default function AchievementIcon({achievement}) {
 const [symbol,Icon]=SYMBOLS[achievement.id]||['award',Award],kind=String(achievement.id||'').split('-')[0];
 return <Icon className={`achievement-icon achievement-icon-${kind}`} size={36} strokeWidth={1.7} data-achievement-symbol={symbol} aria-hidden="true"/>;
}
