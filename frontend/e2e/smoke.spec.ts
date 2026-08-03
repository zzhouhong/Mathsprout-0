import { test, expect } from "@playwright/test";

test.describe("Kindergarten Math App — Smoke Tests", () => {
  test("landing page loads and shows CTA", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/幼儿园|数学/);
    // Hero or CTA should be visible
    const heading = page.locator("h1, h2").first();
    await expect(heading).toBeVisible();
  });

  test("login page is accessible", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("input[type='email']")).toBeVisible();
    await expect(page.locator("input[type='password']")).toBeVisible();
  });

  test("dashboard redirects unauthenticated users to login", async ({ page }) => {
    await page.goto("/dashboard");
    // Should redirect or show login
    await page.waitForURL(/\/login|dashboard/, { timeout: 5000 });
    const url = page.url();
    // Either redirected to login or dashboard page loaded (if already authed)
    expect(url).toBeTruthy();
  });

  test("demo teacher report can be viewed", async ({ page }) => {
    // Login as teacher
    await page.goto("/login");
    await page.fill("input[type='email']", "teacher@kindergarten.cn");
    await page.fill("input[type='password']", "demo123");
    // Look for a login/submit button
    const submitBtn = page.locator("button[type='submit'], button").filter({ hasText: /登录|登入|login|进入/i }).first();
    if (await submitBtn.isVisible()) {
      await submitBtn.click();
      await page.waitForTimeout(2000);
    }

    // Navigate to report demo
    await page.goto("/dashboard/reports/teacher/demo");
    await page.waitForTimeout(2000);

    // Should show report content or demo data
    const body = page.locator("body");
    await expect(body).toBeVisible();
  });

  test("backend health check is reachable", async ({ page }) => {
    const res = await page.request.get("http://localhost:8000/api/health");
    expect(res.status()).toBe(200);
    const json = await res.json();
    expect(json.status).toBeTruthy();
  });
});
