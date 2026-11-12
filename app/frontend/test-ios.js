import { chromium, webkit, devices } from 'playwright';

(async () => {
  // Use iPhone 13/14 device profile which emulates iOS WebKit viewports and touch events
  const iPhone = devices['iPhone 13']

  // Launch Playwright's standalone WebKit engine (no Xcode required)
  const browser = await webkit.launch({ headless: false })
  const context = await browser.newContext({
    ...iPhone,
    permissions: [],
    hasTouch: true,         // Forces touch event dispatch instead of mouse clicks
    isMobile: true,         // Triggers mobile viewport and media query flags
    deviceScaleFactor: 3,
  })

  const page = await context.newPage()

  // Point to your local React dev server
  await page.goto('http://localhost:3001')

  console.log('WebKit mobile emulator running. Press Ctrl+C to close.')
})()
