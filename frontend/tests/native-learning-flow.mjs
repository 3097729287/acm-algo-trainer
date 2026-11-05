import assert from 'node:assert/strict';
import { resolve } from 'node:path';

export async function exerciseNativePlanning(page, output) {
  const snapshot = () => page.evaluate(async () => {
    const result = await window.__TAURI__.core.invoke('api_request', { request: {
      version: 1, id: crypto.randomUUID(), method: 'GET', path: 'learning-summary', query: {},
    } });
    if (!result.ok) throw new Error(result.error.message);
    return result.data;
  });
  await page.getByRole('button', { name: '返回主界面', exact: true }).first().click();
  const nav = page.locator('.sidebar').getByRole('button', { name: '任务', exact: true });
  await nav.click();
  const board = page.locator('[data-section=tasks]');
  await board.locator('.task-mainline-heading').waitFor();
  await board.getByRole('button', { name: '可用时间', exact: true }).click();
  const time = page.getByRole('dialog', { name: '可用时间', exact: true });
  await time.getByRole('spinbutton', { name: '平日可用时间', exact: true }).fill('90');
  await time.getByRole('spinbutton', { name: '周末可用时间', exact: true }).fill('120');
  await time.getByRole('button', { name: '按这个安排', exact: true }).click();
  await time.waitFor({ state: 'detached' });
  let state = await snapshot();
  assert.deepEqual(state.plan.tracks, ['io-basics']);
  assert.equal(state.config.weekdayMinutes, 90);
  assert.ok(state.plan.days.every(day => day.used <= day.minutes));
  await board.getByRole('button', { name: '完成并继续', exact: true }).click();
  await page.waitForFunction(() => document.querySelector('.task-now [role=progressbar]')?.getAttribute('aria-valuenow') === '1');
  const quiz = page.getByRole('dialog', { name: '原理检查', exact: true });
  await quiz.getByRole('button', { name: '字符 a+b', exact: true }).click();
  await quiz.getByRole('alert').waitFor();
  state = await snapshot();
  assert.equal(state.topics.find(topic => topic.id === 'io-basics').level, 1);
  await quiz.getByRole('button', { name: 'a+b 的值', exact: true }).click();
  await quiz.waitFor({ state: 'detached' });
  // Completing a check can open the next original practice task.
  await page.waitForFunction(() => Boolean(document.querySelector('.study-workspace,.study-browser')) || document.querySelector('.task-now [role=progressbar]')?.getAttribute('aria-valuenow') === '2');
  const back = page.getByRole('button', { name: '返回主界面', exact: true }).first();
  if (await back.isVisible()) await back.click();
  await nav.click();
  state = await snapshot();
  assert.equal(state.topics.find(topic => topic.id === 'io-basics').level, 2);
  assert.equal(state.topics.find(topic => topic.id === 'io-basics').independent, 0);
  await board.getByRole('button', { name: '可用时间', exact: true }).click();
  await time.getByRole('spinbutton', { name: '平日可用时间', exact: true }).fill('150');
  await time.getByRole('button', { name: '取消', exact: true }).click();
  assert.equal((await snapshot()).config.weekdayMinutes, 90);
  await board.getByRole('button', { name: '更换主线', exact: true }).click();
  const mainline = page.getByRole('dialog', { name: '更换主线', exact: true });
  const currentTitle = state.availableTopics.find(topic => topic.id === 'io-basics').title;
  const nextTitle = state.availableTopics.find(topic => topic.id === 'binary-search').title;
  await mainline.getByRole('checkbox', { name: currentTitle, exact: true }).uncheck();
  await mainline.getByRole('checkbox', { name: nextTitle, exact: true }).check();
  await mainline.getByRole('combobox').selectOption('topic');
  await mainline.getByLabel('训练目标', { exact: true }).fill('本地测试：二分边界');
  await mainline.getByRole('button', { name: '更换并更新安排', exact: true }).click();
  await mainline.waitFor({ state: 'detached' });
  state = await snapshot();
  assert.deepEqual(state.plan.tracks, ['binary-search']);
  assert.ok(state.history.length >= 2);
  const savedPlanId = state.plan.id;
  await board.getByRole('tab', { name: '历史记录', exact: true }).click();
  await board.getByRole('button', { name: /采纳重新规划/ }).first().click();
  await board.locator('.task-history-article .summary-week').waitFor();
  assert.deepEqual((await snapshot()).plan.tracks, ['binary-search']);
  await board.getByRole('tab', { name: '学习概览', exact: true }).click();
  await board.locator('.task-mainline-heading h2').filter({ hasText: nextTitle }).waitFor();
  const geometry = await page.evaluate(() => {
    const bar = document.querySelector('.main-area > .task-flow-bar');
    const workspace = document.querySelector('.workspace-area[data-page=tasks]');
    const board = workspace.querySelector('[data-section=tasks]');
    return { barHeight: bar?.getBoundingClientRect().height || 0, workspaceWidth: workspace.getBoundingClientRect().width, boardWidth: board.getBoundingClientRect().width };
  });
  assert.ok(geometry.barHeight < 100, 'Continuation stays a compact row');
  assert.ok(geometry.boardWidth >= geometry.workspaceWidth - 2, 'Continuation cannot take a column from the main task content');
  await page.screenshot({ path: resolve(output, 'react-tasks-wide.png') });
  await page.reload();
  await nav.waitFor();
  await nav.click();
  await board.locator('.task-mainline-heading h2').filter({ hasText: nextTitle }).waitFor();
  state = await snapshot();
  assert.equal(state.plan.id, savedPlanId);
  assert.equal(state.topics.find(topic => topic.id === 'io-basics').level, 2);
  return { configured: true, readingStage: 1, conceptStage: 2, independentSolved: 0,
    cancellationPreserved: true, mainlineChanged: true, historyPreserved: true,
    recoveredAfterReload: true, weeklyBudgetShared: true };
}
