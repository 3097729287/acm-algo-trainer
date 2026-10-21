export async function openSettings(page, name) {
  await page.locator('.sidebar').getByRole('button', { name: '设置', exact: true }).click();
  await page.locator('.settings-page').waitFor();
  const back = page.locator('.settings-back');
  if (await back.isVisible()) await back.click();
  if (name) await page.getByRole('tab', { name, exact: true }).click();
}
