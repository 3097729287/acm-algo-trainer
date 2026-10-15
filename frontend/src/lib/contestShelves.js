export function isXcpc(row) {
  return row.series === 'XCPC' || /ICPC|CCPC|大学生.*程序设计/i.test(row.contest || row.name || '');
}

export function matchesShelf(row, shelf = 'all') {
  if (shelf === 'all') return true;
  if (shelf === 'xcpc') return isXcpc(row);
  if (shelf === 'lanqiao') return row.series === '蓝桥杯 C/C++大学B';
  return row.platform === shelf;
}
