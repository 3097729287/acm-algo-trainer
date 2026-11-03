export async function openSettings(page, name) {
  await page.locator('.sidebar').getByRole('button', { name: '设置', exact: true }).click();
  await page.locator('.settings-page').waitFor();
  // Settings Back now returns one level, including nested categories/themes.
  // Reach the home grid through the same real button before choosing a tab.
  for (let depth = 0; depth < 4 && !(await page.locator('.settings-home-grid').count()); depth++) {
    await page.locator('.settings-return-button').click();
  }
  await page.locator('.settings-home-grid').waitFor();
  // Scene centres have their own playful interactions. Open the category
  // through its actual label, leaving those interactions available to users.
  if (name) await page.getByRole('tab', { name, exact: true }).locator('.settings-tile-label').click();
}

export async function setTheme(page,theme) {
  if(!['light','dark'].includes(theme))throw new Error('Unknown theme');
  const toggle=page.getByRole('button',{name:'切换深浅主题',exact:true});
  await toggle.waitFor();
  if(await page.locator('html').getAttribute('data-theme')!==theme)await toggle.click();
  await page.waitForFunction(value=>document.documentElement.dataset.theme===value,theme);
}
