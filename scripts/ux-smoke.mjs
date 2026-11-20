import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium } from 'playwright';

const origin = 'http://127.0.0.1:4321';
const base = `${origin}/representation-psychology/`;
const server = spawn('npm', ['run', 'preview', '--', '--host', '127.0.0.1'], {
  stdio: 'inherit',
  env: process.env,
});

async function waitForServer() {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    try {
      const response = await fetch(base);
      if (response.ok) return;
    } catch {
      // Astro preview is still starting.
    }
    await delay(1000);
  }
  throw new Error('Astro preview did not become available');
}

async function assertNoHorizontalOverflow(page, route, width) {
  await page.setViewportSize({ width, height: 850 });
  await page.goto(new URL(route, base).href);
  const dimensions = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    document: document.documentElement.scrollWidth,
  }));
  assert.ok(
    dimensions.document <= dimensions.viewport + 1,
    `Horizontal overflow at ${width}px on ${route}: ${JSON.stringify(dimensions)}`,
  );
}

let browser;
try {
  await waitForServer();
  browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  // Keyboard entry point and responsive navigation.
  await page.goto(base);
  await page.keyboard.press('Tab');
  assert.ok(
    await page.evaluate(() => document.activeElement?.classList.contains('skip-link')),
    'The first keyboard stop should be the skip-to-content link',
  );
  await page.setViewportSize({ width: 375, height: 812 });
  const menu = page.locator('[data-nav-toggle]');
  await menu.click();
  assert.equal(await menu.getAttribute('aria-expanded'), 'true');
  assert.ok(await page.locator('#site-nav').isVisible(), 'Mobile navigation should open');

  // Desktop catalog table and mobile cards.
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(new URL('catalog/', base).href);
  assert.ok(await page.locator('.catalog-table-wrap:not(.catalog-table--compare-wrap)').isVisible());
  assert.ok(!(await page.locator('.catalog-cards').isVisible()));

  await page.setViewportSize({ width: 375, height: 812 });
  assert.ok(await page.locator('.catalog-cards').isVisible());
  const compareChecks = page.locator('.catalog-cards input[type="checkbox"]');
  assert.ok((await compareChecks.count()) >= 2, 'At least two mobile catalogue cards should be available for comparison');
  await compareChecks.nth(0).check();
  await compareChecks.nth(1).check();
  assert.ok(
    await page.locator('.catalog-table--compare').isVisible(),
    'The comparison table must remain visible on narrow screens',
  );

  // Detail navigation must preserve the full return chain:
  // catalogue -> work -> scene -> work -> catalogue.
  await page.goto(new URL('catalog/', base).href);
  await page.locator('.catalog-card h3 a').first().click();
  await page.waitForURL(/\/work\/[^/]+\/$/);
  await page.locator('a[data-return]').first().click();
  await page.waitForURL(/\/scene\/[^/]+\/$/);
  await page.locator('a[data-back]').click();
  await page.waitForURL(/\/work\/[^/]+\/$/);
  const parentReturn = await page.locator('a[data-back]').getAttribute('href');
  assert.ok(parentReturn?.includes('/catalog/'), `Work page should retain its catalogue parent, got ${parentReturn}`);
  await page.locator('a[data-back]').click();
  await page.waitForURL(/\/catalog\//);

  // Reduced-motion preference is respected by global styles.
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto(base);
  const scrollBehavior = await page.evaluate(() => getComputedStyle(document.documentElement).scrollBehavior);
  assert.equal(scrollBehavior, 'auto');

  // Check common routes at phone, tablet and desktop widths.
  for (const route of ['', 'catalog/', 'infographics/', 'codebook/', 'method/']) {
    for (const width of [375, 768, 1440]) {
      await assertNoHorizontalOverflow(page, route, width);
    }
  }

  console.log('UX smoke tests passed: keyboard entry, mobile nav, responsive catalogue/comparison, return chain, reduced motion, and viewport overflow.');
} finally {
  await browser?.close();
  server.kill('SIGTERM');
}
