const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: true
  });

  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  // 监控所有API请求
  page.on('request', req => {
    if (req.url().includes('/api/')) {
      console.log('  [REQ] ' + req.method() + ' ' + req.url());
    }
  });
  page.on('response', resp => {
    if (resp.url().includes('/api/')) {
      console.log('  [RES] ' + resp.status() + ' ' + resp.request().method() + ' ' + resp.url());
    }
  });
  page.on('console', msg => console.log('  [CONSOLE]', msg.type(), msg.text()));

  // Step 1: 登录页
  console.log('=== 打开登录页 ===');
  await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle' });

  // Step 2: 用 type 逐个输入（触发 Vue v-model）
  console.log('=== 输入凭据 ===');
  const usernameInput = page.locator('input[placeholder="请输入用户名"]');
  const passwordInput = page.locator('input[placeholder="请输入密码"]');

  await usernameInput.click();
  await usernameInput.fill('admin');
  await page.waitForTimeout(300);

  await passwordInput.click();
  await passwordInput.fill('admin123');
  await page.waitForTimeout(300);

  // Step 3: 点击登录按钮
  console.log('=== 点击登录 ===');
  const loginBtn = page.locator('button:has-text("登录")');

  // 同时监听导航
  const navPromise = page.waitForURL(url => url.pathname !== '/login', { timeout: 15000 }).catch(() => null);
  await loginBtn.click();

  // Step 4: 等待导航或检查当前URL
  await page.waitForTimeout(3000);
  console.log('当前 URL:', page.url());

  // 如果还在login页面，检查错误信息
  if (page.url().includes('login')) {
    const errorText = await page.textContent('.el-message--error, .el-form-item__error').catch(() => '');
    console.log('错误提示:', errorText);
    const pageText = await page.textContent('body');
    console.log('页面文本前500字:', pageText.substring(0, 500));
    // 截图看状态
    await page.screenshot({ path: 'C:/Users/22397/Desktop/login_error.png', fullPage: true });
    console.log('截图: login_error.png');
  }

  // 强制跳转到admin appointments看看
  console.log('=== 强制跳转 /admin/appointments ===');
  await page.goto('http://localhost:5173/admin/appointments', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);
  console.log('跳转后 URL:', page.url());

  // 如果被重定向回login，说明token没存上。手动set token
  if (page.url().includes('login')) {
    console.log('被路由守卫拦截，手动注入token...');
    // 先直接调API登录拿token
    const resp = await page.evaluate(async () => {
      const res = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'admin', password: 'admin123' })
      });
      return res.json();
    });
    console.log('API登录结果:', JSON.stringify(resp).substring(0, 200));
    if (resp.access_token) {
      await page.evaluate((token) => {
        localStorage.setItem('token', token);
      }, resp.access_token);
      console.log('Token已注入localStorage');
      // 重新访问
      await page.goto('http://localhost:5173/admin/appointments', { waitUntil: 'networkidle' });
      await page.waitForTimeout(3000);
      console.log('注入后 URL:', page.url());
    }
  }

  // Step 5: 检查表格
  console.log('=== 检查预约数据 ===');
  await page.screenshot({ path: 'C:/Users/22397/Desktop/appointments_v3.png', fullPage: true });

  const pageText = await page.textContent('body');
  console.log('有"预约记录":', pageText.includes('预约记录'));
  console.log('有"testuser":', pageText.includes('testuser'));
  console.log('有"李四"假数据:', pageText.includes('李四'));
  console.log('有"王五"假数据:', pageText.includes('王五'));

  // 表格内容
  const cells = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('.el-table__body-wrapper td, table td')).map(td => td.textContent?.trim().substring(0, 40));
  });
  console.log('表格单元格:', cells);

  // Step 6: 确认/取消操作
  console.log('=== 测试操作按钮 ===');
  const confirmBtns = page.locator('button', { hasText: '确认' });
  console.log('确认按钮数量:', await confirmBtns.count());
  if (await confirmBtns.count() > 0) {
    // 找表格操作列的确认按钮
    const opBtns = page.locator('.el-table__body-wrapper button:has-text("确认")');
    console.log('操作列确认按钮:', await opBtns.count());
    if (await opBtns.count() > 0) {
      await opBtns.first().click();
      await page.waitForTimeout(1000);
      await page.screenshot({ path: 'C:/Users/22397/Desktop/confirm_dialog.png', fullPage: true });
    }
  }

  await browser.close();
  console.log('\n=== 验证结束 ===');
})().catch(e => {
  console.error('失败:', e.message);
  process.exit(1);
});
