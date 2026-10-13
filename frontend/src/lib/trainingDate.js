export const TRAINING_TIME_ZONE = 'Asia/Shanghai';

const dayFormat = new Intl.DateTimeFormat('en-CA', {
  timeZone: TRAINING_TIME_ZONE, year: 'numeric', month: '2-digit', day: '2-digit',
});
const timeFormat = new Intl.DateTimeFormat('zh-CN', {
  timeZone: TRAINING_TIME_ZONE, hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
});

export function trainingDay(value = Date.now()) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const parts = Object.fromEntries(dayFormat.formatToParts(date).map(part => [part.type, part.value]));
  return `${parts.year}-${parts.month}-${parts.day}`;
}

export function trainingDateLabel(day, now = Date.now()) {
  if (!day) return '日期未知';
  return (day.slice(0, 4) === trainingDay(now).slice(0, 4) ? day.slice(5) : day).replaceAll('-', '/');
}

export function trainingTime(value) {
  return trainingDay(value) ? timeFormat.format(new Date(value)) : '—';
}
