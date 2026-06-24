const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: true
  });

  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  // Step 1: 打开登录页
  console.log('=== Step 1: 打开登录页 ===');
  await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle' });
  console.log('页面标题:', await page.title());

  // Step 2: 输入账号密码登录
  console.log('=== Step 2: 登录 ===');
  await page.fill('input[placeholder*="用户"]', 'admin');
  await page.fill('input[placeholder*="密码"]', 'admin123');
  await page.click('button:has-text("登录")');
  await page.waitForURL('**/admin/**', { timeout: 10000 });
  console.log('登录后 URL:', page.url());

  // Step 3: 进入预约管理页
  console.log('=== Step 3: 进入预约管理页 ===');
  await page.goto('http://localhost:5173/admin/appointments', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  // Step 4: 检查表格数据
  console.log('=== Step 4: 检查表格数据 ===');
  const rows = await page.evaluate(() => {
    const trs = document.querySelectorAll('table tbody tr');
    return Array.from(trs).map(r =>
      Array.from(r.querySelectorAll('td'), td => td.textContent?.trim()).join(' | ')
    );
  });
  console.log('表格行数:', rows.length);
  rows.forEach((r, i) => console.log('  行' + (i + 1) + ':', r));

  // 关键验证：检查页面内容
  const pageText = await page.textContent('body');
  const hasRealData = pageText.includes('testuser') || pageText.includes('验证测试患者');
  const hasFakeData = pageText.includes('李四') || pageText.includes('王五');

  console.log('---');
  console.log('✅ 有真实数据(testuser/验证测试患者):', hasRealData);
  console.log('❌ 假数据兜底(李四/王五):', hasFakeData);

  if (hasRealData && !hasFakeData) {
    console.log('✅ 验证通过：管理后台预约列表从真实接口加载');
  } else if (!hasRealData && hasFakeData) {
    console.log('❌ 验证失败：仍在展示硬编码假数据');
  } else if (!hasRealData && !hasFakeData) {
    console.log('⚠️ 表为空：数据库无预约记录或API请求失败');
  }

  // Step 5: 截图
  await page.screenshot({ path: 'C:/Users/22397/Desktop/appointments_page.png', fullPage: true });
  console.log('=== 截图已保存到桌面 ===');

  // Step 6: 尝试确认操作
  console.log('=== Step 6: 确认/取消操作测试 ===');
  const confirmBtn = page.locator('button:has-text("确认")').first();
  if (await confirmBtn.isVisible()) {
    console.log('找到确认按钮，测试点击...');
    await confirmBtn.click();
    await page.waitForTimeout(1000);
    const confirmDialog = page.locator('.el-message-box__btns button:has-text("确认")').first();
    if (await confirmDialog.isVisible({ timeout: 2000 }).catch(() => false)) {
      await confirmDialog.click();
      await page.waitForTimeout(2000);
      console.log('✅ 确认操作完成');
    }
  } else {
    console.log('⚠️ 没有可确认的预约（所有预约已处理）');
  }

  // 操作后截图
  await page.screenshot({ path: 'C:/Users/22397/Desktop/appointments_after.png', fullPage: true });

  await browser.close();
  console.log('=== 验证完成 ===');
})().catch(e => {
  console.error('验证失败:', e.message);
  process.exit(1);
});
