export async function openSettings(page, name) {
  await page.locator('.sidebar').getByRole('button', { name: '设置', exact: true }).click();
  await page.locator('.settings-page').waitFor();
  if (!(await page.locator('.settings-home-grid').count())) await page.keyboard.press('Escape');
  if (name) await page.getByRole('tab', { name, exact: true }).click();
}
