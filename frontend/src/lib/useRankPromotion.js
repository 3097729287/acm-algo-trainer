import {useCallback, useEffect, useRef, useState} from 'react';
import {acknowledgeRankPromotion, emptyRankPromotion, observeRankPromotion, rankPromotionKey, restoreRankPromotion} from './rankPromotions.js';

const editing = target => target?.closest?.('input,textarea,select,.cm-editor,[contenteditable=true]');
const otherDialog = () => Boolean(document.querySelector('dialog[open],[aria-modal=true],[data-popconfirm]'));
function read(owner) {
  try {return restoreRankPromotion(JSON.parse(localStorage.getItem(rankPromotionKey(owner))), owner);}
  catch {return emptyRankPromotion(owner);}
}
export default function useRankPromotion({owner, growth, ready, blocked = false}) {
  const [stored, setStored] = useState(() => read(owner)), [playing, setPlaying] = useState(null), [wake, setWake] = useState(0);
  const scope = useRef(owner), current = useRef(stored), quiet = useRef(0), composing = useRef(false);
  const state = stored.owner === owner ? stored : read(owner);
  const observed = observeRankPromotion(state, growth, owner);
  current.current = observed;
  const save = useCallback(value => {
    current.current = value; setStored(value);
    if (value.owner) try {localStorage.setItem(rankPromotionKey(value.owner), JSON.stringify({...value, authority: null}));} catch { /* Current-session presentation still works. */ }
  }, []);
  useEffect(() => {
    if (scope.current !== owner) {scope.current = owner; quiet.current = 0; composing.current = false; setPlaying(null);}
    if (observed !== stored) save(observed);
  }, [owner, observed, stored, save]);
  useEffect(() => {
    const update = () => setWake(value => value + 1);
    const input = event => {if (editing(event.target)) quiet.current = performance.now();};
    const start = event => {if (editing(event.target)) {composing.current = true; input(event);}};
    const end = event => {composing.current = false; input(event);};
    document.addEventListener('input', input, true); document.addEventListener('keydown', input, true);
    document.addEventListener('compositionstart', start, true); document.addEventListener('compositionend', end, true);
    document.addEventListener('focusin', update);
    document.addEventListener('visibilitychange', update); window.addEventListener('focus', update); window.addEventListener('blur', update);
    return () => {
      document.removeEventListener('input', input, true); document.removeEventListener('keydown', input, true);
      document.removeEventListener('compositionstart', start, true); document.removeEventListener('compositionend', end, true);
      document.removeEventListener('focusin', update);
      document.removeEventListener('visibilitychange', update); window.removeEventListener('focus', update); window.removeEventListener('blur', update);
    };
  }, []);
  useEffect(() => {
    if (!observed.pending || playing || blocked) return;
    const timer = setInterval(() => {
      if (!document.hidden && document.hasFocus() && !otherDialog() && !composing.current && performance.now() - quiet.current >= 800)
        setWake(value => value + 1);
    }, 250);
    return () => clearInterval(timer);
  }, [Boolean(observed.pending), Boolean(playing), blocked]);
  const confirmed = observed.authority?.owner === owner;
  const visible = Boolean(owner && ready && confirmed && !blocked && !document.hidden && document.hasFocus() && !otherDialog());
  useEffect(() => {
    if (playing && (!visible || playing.owner !== owner || observed.rank === null || observed.rank < playing.to)) {setPlaying(null); return;}
    if (!playing && visible && observed.pending && !composing.current && performance.now() - quiet.current >= 800)
      setPlaying({...observed.pending, owner});
  }, [owner, ready, blocked, observed, playing, visible, wake]);
  const presented = useCallback(id => {
    if (scope.current === owner && !document.hidden && document.hasFocus()) save(acknowledgeRankPromotion(current.current, id));
  }, [owner, save]);
  const close = useCallback(id => {
    if (scope.current === owner) save(acknowledgeRankPromotion(current.current, id));
    setPlaying(null);
  }, [owner, save]);
  return {notice: visible && playing?.owner === owner ? playing : null, pending: Boolean(confirmed && observed.pending), presented, close};
}
