import { expect, test } from "@playwright/test";

const email = process.env.E2E_EMAIL;
const otp = process.env.E2E_OTP;

test.describe("onboarding", () => {
  test.skip(!email || !otp, "Set E2E_EMAIL and E2E_OTP from a running development OTP provider.");

  test("verified user can create an IP company", async ({ page }) => {
    await page.goto("/register");
    await page.getByLabel("نام").fill("E2E User");
    await page.getByLabel("ایمیل").fill(email!);
    await page.getByLabel("رمز عبور").fill("correct-horse-battery-staple");
    await page.getByRole("button", { name: "ساخت حساب" }).click();
    await page.getByLabel("کد شش‌رقمی").fill(otp!);
    await page.getByRole("button", { name: "تأیید و ورود" }).click();
    await expect(page).toHaveURL(/\/dashboard/);
    await page.getByRole("link", { name: "ثبت شرکت" }).click();
    await page.getByLabel("نام شرکت").fill("E2E IP Company");
    await page.getByLabel("شناسهٔ URL").fill(`e2e-ip-${Date.now()}`);
    await page.getByRole("button", { name: "بعدی" }).click();
    await page.getByLabel("IP سازمان").check();
    await page.getByLabel("CIDR مجاز").fill("192.168.10.0/24");
    await page.getByRole("button", { name: "بعدی" }).click();
    await page.getByRole("button", { name: "ثبت شرکت" }).click();
    await expect(page).toHaveURL(/\/c\/.*\/admin/);
  });
});
