export async function openSettings(page, name) {
  await page.locator('.sidebar').getByRole('button', { name: '设置', exact: true }).click();
  await page.locator('.settings-page').waitFor();
  if (!(await page.locator('.settings-home-grid').count())) await page.keyboard.press('Escape');
  if (name) await page.getByRole('tab', { name, exact: true }).click();
}

export async function setTheme(page,theme) {
  if(!['light','dark'].includes(theme))throw new Error('Unknown theme');
  const toggle=page.getByRole('button',{name:'切换深浅主题',exact:true});
  await toggle.waitFor();
  if(await page.locator('html').getAttribute('data-theme')!==theme)await toggle.click();
  await page.waitForFunction(value=>document.documentElement.dataset.theme===value,theme);
}
