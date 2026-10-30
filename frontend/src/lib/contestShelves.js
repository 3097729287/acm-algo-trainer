import {normalizePlatform,rowPlatform} from './platformRegistry.js';
import {catalogSegments} from './contestCatalog.js';

export function isXcpc(row) {
  return catalogSegments(row)[0] === 'XCPC';
}
export function contestKind(row) {
  const name = `${row.contest || row.name || ''} ${row.contestFullName || ''} ${row.examStage || ''}`;
  if (/热身|warm.?up/i.test(name)) return 'warmup';
  if (/网络|预选|online|qualification/i.test(name)) return 'online';
  if (/邀请|invitational/i.test(name)) return 'invitational';
  if (/省赛|省.*程序设计/.test(name)) return 'provincial';
  if (/分区|subregional/i.test(name)) return 'subregional';
  if (/总决赛|world finals/i.test(name)) return 'finals';
  if (/决赛|final/i.test(name)) return 'final';
  if (/初赛|preliminary/i.test(name)) return 'preliminary';
  if (/区域|regional/i.test(name)) return 'regional';
  if (/教育|educational/i.test(name)) return 'educational';
  if (/入门|基础|小白|ABC/i.test(name)) return 'beginner';
  if (/周赛|weekly/i.test(name)) return 'weekly';
  return 'other';
}
export const CONTEST_KINDS = [['invitational','邀请赛'],['provincial','省赛'],['online','网络赛'],['subregional','分区赛'],['regional','区域赛'],['finals','总决赛'],['final','决赛'],['preliminary','初赛'],['warmup','热身赛'],['educational','教育赛'],['beginner','入门赛'],['weekly','周赛'],['other','其他']];
export function matchesShelf(row, shelf = 'all') {
  if (!shelf || shelf === 'all') return true;
  if (shelf === 'xcpc' || shelf === 'XCPC' || shelf === 'ACM') return isXcpc(row);
  if (shelf === 'lanqiao') return /^蓝桥杯/.test(row.series || row.contest || row.name || '');
  return !isXcpc(row) && rowPlatform(row) === normalizePlatform(shelf);
}
