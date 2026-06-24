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
  console.log('URL:', page.url());
  console.log('Title:', await page.title());

  // 截图看页面
  await page.screenshot({ path: 'C:/Users/22397/Desktop/step1_login.png', fullPage: true });
  console.log('截图: step1_login.png');

  // 打印所有input元素
  const inputs = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('input')).map(el => ({
      type: el.type,
      placeholder: el.placeholder,
      name: el.name,
      class: el.className,
      id: el.id
    }));
  });
  console.log('页面input:', JSON.stringify(inputs, null, 2));

  // 打印所有button
  const buttons = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('button')).map(el => ({
      text: el.textContent?.trim(),
      class: el.className
    }));
  });
  console.log('页面button:', JSON.stringify(buttons, null, 2));

  // 打印body文本前500字符
  const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 500));
  console.log('页面文本:', bodyText);

  await browser.close();
  console.log('=== 调试完成 ===');
})().catch(e => {
  console.error('失败:', e.message);
  process.exit(1);
});
