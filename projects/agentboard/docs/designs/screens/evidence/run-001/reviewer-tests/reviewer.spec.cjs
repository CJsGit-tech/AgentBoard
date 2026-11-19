const {test,expect}=require('/Users/cjhuang/Desktop/Projects/AgentBoard/projects/agentboard/frontend/node_modules/@playwright/test');
const nav=(p,name)=>p.getByRole('navigation',{name:'Project navigation'}).getByRole('link',{name,exact:true});
test('reviewer: failed document draft stays on navigation cancellation and adds no revision',async({page})=>{
 await page.goto('/#/documents/doc-mcp');await page.getByRole('button',{name:'Edit document',exact:true}).click();
 await page.getByLabel('Document content',{exact:true}).fill('Retain this failed draft');await page.getByLabel('Fail next save').check();await page.getByRole('button',{name:'Save document',exact:true}).click();
 const dialog=page.waitForEvent('dialog');const clicked=nav(page,'Tickets').click();await (await dialog).dismiss();await clicked;
 await expect(page.getByLabel('Document content',{exact:true})).toHaveValue('Retain this failed draft');
 const discard=page.waitForEvent('dialog');const cancel=page.getByRole('button',{name:'Cancel editing',exact:true}).click();await (await discard).accept();await cancel;
 await page.getByRole('button',{name:'Revision history',exact:true}).click();await expect(page.locator('.revision-list li')).toHaveCount(4);await expect(page.locator('.revision-list')).not.toContainText('Version 5');
});
test('reviewer: relation dedupe and project switch do not leak linked documents',async({page})=>{
 await page.goto('/#/tickets/8f24c9e7');await page.getByLabel('Link document',{exact:true}).selectOption('doc-mcp');await page.getByLabel('Document relationship',{exact:true}).selectOption('Context');await page.getByRole('button',{name:'Link',exact:true}).click();await expect(page.locator('.document-link')).toHaveCount(1);
 await page.getByLabel('Select project',{exact:true}).selectOption('fieldnotes');await nav(page,'Roles').click();await expect(page.getByRole('heading',{name:'Researcher',exact:true})).toBeVisible();await expect(page.locator('.role-grid')).not.toContainText('Backend');
 await nav(page,'Documents').click();await expect(page.getByRole('heading',{name:'No documents found',exact:true})).toBeVisible();await page.getByLabel('Select project',{exact:true}).selectOption('agentboard');await nav(page,'Documents').click();await expect(page.locator('tbody tr')).toHaveCount(2);
});
test('reviewer: native modal prevents page focus, returns focus and primary focus is visibly internal',async({page})=>{
 await page.goto('/#/projects');await page.getByRole('button',{name:'New project',exact:true}).click();const modal=page.getByRole('dialog');await expect(modal).toBeVisible();
 await modal.getByRole('button',{name:'Create project',exact:true}).focus();await page.keyboard.press('Tab');expect(await modal.evaluate(e=>document.activeElement===document.body||e.contains(document.activeElement))).toBe(true);await page.locator('.page-header .primary').focus();await expect(page.locator('.page-header .primary')).not.toBeFocused();
 await modal.getByRole('button',{name:'Create project',exact:true}).focus();const s=await modal.getByRole('button',{name:'Create project',exact:true}).evaluate(e=>{const s=getComputedStyle(e);return{shadow:s.boxShadow,background:s.backgroundColor,outline:s.outlineStyle}});expect(s.outline).toBe('none');expect(s.shadow).toContain('inset');expect(s.shadow).not.toContain(s.background);
 await page.keyboard.press('Escape');await expect(modal).toHaveCount(0);await expect(page.getByRole('button',{name:'New project',exact:true})).toBeFocused();
});
test('reviewer: activity disconnection buffers once, reconnects and retains only matching events',async({page})=>{
 await page.goto('/#/activity');await page.getByLabel('Preview state',{exact:true}).selectOption('Disconnected');await expect(page.locator('.live-state')).toContainText('Disconnected');const count=await page.locator('.activity-feed li').count();
 await page.getByRole('button',{name:'Simulate incoming event',exact:true}).click();await expect(page.locator('.activity-feed li')).toHaveCount(count);await page.getByRole('button',{name:'Reconnect',exact:true}).click();await expect(page.getByLabel('Preview state',{exact:true})).toHaveValue('Ready');await expect(page.locator('.activity-feed li')).toHaveCount(count+1);await page.getByRole('button',{name:'Replay last event',exact:true}).click();await expect(page.locator('.activity-feed li')).toHaveCount(count+1);
 await page.getByLabel('Filter activity by agent').selectOption('Claude');await page.getByLabel('Filter activity by type').selectOption('Tool call');await expect(page.locator('.activity-feed')).not.toContainText('Me');await expect(page.locator('.activity-feed')).not.toContainText('Expired example event');
});
test('reviewer: failed document draft is protected when browser Back is used',async({page})=>{
 await page.goto('/#/documents');await page.getByRole('link',{name:'MCP ticket tool contract',exact:true}).click();await page.getByRole('button',{name:'Edit document',exact:true}).click();await page.getByLabel('Document content',{exact:true}).fill('Draft protected from browser history');await page.getByLabel('Fail next save').check();await page.getByRole('button',{name:'Save document',exact:true}).click();page.on('dialog',dialog=>dialog.dismiss());await page.goBack();await expect(page.getByLabel('Document content',{exact:true})).toHaveValue('Draft protected from browser history');
});
