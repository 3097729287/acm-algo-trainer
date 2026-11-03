import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const out='../.backups/next-152/course-directory-ui';await mkdir(out,{recursive:true});
const vite=await createServer({cacheDir:out+'/vite',server:{host:'127.0.0.1',port:0,watch:null}});await vite.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1720,height:1000}}),errors=[];page.on('pageerror',issue=>errors.push(issue.message));page.setDefaultTimeout(8000);
try{
 await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/course-directory-fixture.html`);await page.locator('.lectures-list>button').first().waitFor();
 assert.equal(await page.locator('.lectures-list>button').count(),23);
 const catalog=await page.locator('.lectures-list').boundingBox();assert(catalog.width>1600,'The course list occupies the available page width');
 const first=await page.locator('.lectures-list>button').nth(0).boundingBox(),second=await page.locator('.lectures-list>button').nth(1).boundingBox();assert(Math.abs(first.y-second.y)<1&&second.x>first.x+first.width,'Courses flow across columns instead of an unused detail pane');
 await page.screenshot({path:out+'/catalog-wide.png'});
 // Geometry checks the actual transformed SVG path, including its direction.
 const ring=await page.locator('.profile-xp-ring').first().evaluate(svg=>{const circle=svg.querySelector('.profile-xp-value'),matrix=circle.getScreenCTM(),screen=length=>{const p=circle.getPointAtLength(length);return new DOMPoint(p.x,p.y).matrixTransform(matrix);},a=screen(0),b=screen(circle.getTotalLength()/4),rect=svg.getBoundingClientRect();return {a:{x:a.x,y:a.y},b:{x:b.x,y:b.y},cx:rect.x+rect.width/2,cy:rect.y+rect.height/2,progress:svg.getAttribute('aria-valuenow'),stroke:getComputedStyle(circle).stroke};});
 assert(Math.abs(ring.a.x-ring.cx)<1&&ring.a.y>ring.cy,'XP starts at the bottom');assert(ring.b.x<ring.cx&&Math.abs(ring.b.y-ring.cy)<1,'The first quarter proceeds up the left side');assert.equal(ring.progress,'25');
 await page.locator('.lectures-list>button').first().click();await page.locator('.lecture-markdown').waitFor();const toggle=page.getByRole('button',{name:'讲解目录',exact:true});
 assert.equal(await toggle.getAttribute('aria-expanded'),'false');assert.equal(await page.locator('.lectures-list').count(),0);await toggle.click();await page.locator('.lectures-list').waitFor();
 assert.equal(await page.locator('.lectures-list>button').count(),23);assert.equal(await page.locator('.lectures-list [aria-current=page]').count(),1);
 await page.locator('.lectures-list>button').nth(1).click();await page.waitForFunction(()=>courseFixture.calls.at(-1)?.kind==='replace');assert.equal(await toggle.getAttribute('aria-expanded'),'true');
 assert.equal((await page.evaluate(()=>courseFixture.calls.filter(call=>call.kind==='open'))).length,1,'Directory navigation reuses the current reader');await page.screenshot({path:out+'/reader-directory-wide.png'});
 await toggle.click();assert.equal(await page.locator('.lectures-list').count(),0);
 await page.setViewportSize({width:540,height:900});await toggle.click();await page.locator('.lectures-list').waitFor();
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);await page.screenshot({path:out+'/reader-directory-narrow.png'});await toggle.click();
 assert.deepEqual(errors,[]);await writeFile(out+'/result.json',JSON.stringify({ok:true,courseCount:23,catalogWidth:catalog.width,ring,errors},null,2));console.log('PASS full-width 23-course catalog, collapsible fullscreen directory, in-place navigation, narrow layout and bottom-to-left XP progress.');
}catch(issue){await page.screenshot({path:out+'/failure.png'});throw issue;}finally{await browser.close();await vite.close();}
