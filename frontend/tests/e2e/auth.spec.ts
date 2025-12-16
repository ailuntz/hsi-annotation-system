import { expect, test } from '@playwright/test';

test.describe('Authentication', () => {
	test('should display login page', async ({ page }) => {
		await page.goto('/auth/login');
		await expect(page.getByRole('heading', { name: '欢迎回来' })).toBeVisible();
		await expect(page.getByLabel('邮箱')).toBeVisible();
		await expect(page.getByLabel('密码')).toBeVisible();
	});

	test('should display register page', async ({ page }) => {
		await page.goto('/auth/register');
		await expect(page.getByRole('heading', { name: '创建账号' })).toBeVisible();
		await expect(page.getByLabel('邮箱')).toBeVisible();
		await expect(page.getByLabel('密码', { exact: true })).toBeVisible();
		await expect(page.getByLabel('确认密码')).toBeVisible();
	});

	test('should navigate from login to register', async ({ page }) => {
		await page.goto('/auth/login');
		await page.click('text=立即注册');
		await expect(page).toHaveURL('/auth/register');
	});

	test('should navigate from register to login', async ({ page }) => {
		await page.goto('/auth/register');
		await page.click('text=立即登录');
		await expect(page).toHaveURL('/auth/login');
	});

	test('should show validation errors on empty login', async ({ page }) => {
		await page.goto('/auth/login');
		await page.click('button[type="submit"]');
		await expect(page.getByText('请输入有效的邮箱地址')).toBeVisible();
	});
});
