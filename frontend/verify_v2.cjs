const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: true
  });

  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  // 监听网络请求
  page.on('response', resp => {
    if (resp.url().includes('auth') || resp.url().includes('appointments')) {
      console.log(`  [API] ${resp.status()} ${resp.request().method()} ${resp.url()}`);
    }
  });

  // Step 1: 打开登录页
  console.log('=== Step 1: 打开登录页 ===');
  await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle' });

  // Step 2: 填入账号密码
  console.log('=== Step 2: 输入凭据 ===');
  await page.fill('input[placeholder="请输入用户名"]', 'admin');
  await page.fill('input[placeholder="请输入密码"]', 'admin123');

  // Step 3: 点击登录，同时等待导航
  console.log('=== Step 3: 点击登录 ===');
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle', timeout: 15000 }),
    page.click('button:has-text("登录")')
  ]);
  console.log('登录后 URL:', page.url());
  await page.screenshot({ path: 'C:/Users/22397/Desktop/step2_logged_in.png', fullPage: true });

  // Step 4: 如果登录后没自动跳转到appointments，手动跳
  if (!page.url().includes('appointments')) {
    console.log('手动跳转到预约管理页...');
    await page.goto('http://localhost:5173/admin/appointments', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);
  }
  console.log('当前 URL:', page.url());

  // Step 5: 检查页面内容
  console.log('=== Step 5: 检查表格数据 ===');
  const pageText = await page.textContent('body');

  // 检查关键信息
  const checks = {
    '预约记录标题': pageText.includes('预约记录'),
    'testuser数据': pageText.includes('testuser'),
    '验证测试患者': pageText.includes('验证测试患者'),
    '李四(假数据)': pageText.includes('李四'),
    '王五(假数据)': pageText.includes('王五'),
    '张三(假数据)': pageText.includes('张三'),
  };
  console.log(JSON.stringify(checks, null, 2));

  // 打印表格内容
  const rows = await page.evaluate(() => {
    const trs = document.querySelectorAll('.el-table__body-wrapper tbody tr');
    if (!trs.length) {
      // 尝试另一种选择器
      const trs2 = document.querySelectorAll('table tbody tr');
      return Array.from(trs2).map(r =>
        Array.from(r.querySelectorAll('td'), td => td.textContent?.trim().substring(0, 30)).join(' | ')
      );
    }
    return Array.from(trs).map(r =>
      Array.from(r.querySelectorAll('td'), td => td.textContent?.trim().substring(0, 30)).join(' | ')
    );
  });
  console.log('表格行数:', rows.length);
  if (rows.length === 0) {
    // 可能是空状态
    const empty = await page.textContent('.empty');
    console.log('空状态文本:', empty);
  }
  rows.forEach((r, i) => console.log('  行' + (i + 1) + ':', r));

  // 截图
  await page.screenshot({ path: 'C:/Users/22397/Desktop/appointments_final.png', fullPage: true });
  console.log('截图: appointments_final.png');

  // Step 6: 测试确认操作
  console.log('=== Step 6: 测试确认操作 ===');
  const confirmBtn = page.locator('.el-table__body-wrapper button', { hasText: '确认' }).first();
  if (await confirmBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
    console.log('找到确认按钮，点击...');
    await confirmBtn.click();
    await page.waitForTimeout(1500);
    // 弹窗确认
    const popupConfirm = page.locator('.el-message-box__btns .el-button--primary').first();
    if (await popupConfirm.isVisible({ timeout: 2000 }).catch(() => false)) {
      await popupConfirm.click();
      await page.waitForTimeout(2000);
      console.log('✅ 确认操作完成');
    }
  } else {
    console.log('⚠️ 无可操作的确认按钮');
  }

  await page.screenshot({ path: 'C:/Users/22397/Desktop/appointments_after_confirm.png', fullPage: true });

  await browser.close();
  console.log('\n=== 前端 GUI 验证完成 ===');
})().catch(e => {
  console.error('验证失败:', e.message);
  process.exit(1);
});
