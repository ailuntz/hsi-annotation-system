import { expect, test } from '@playwright/test';

test.describe('Todos', () => {
	// Helper to create user via API and login via UI
	async function loginUser(page: any, email: string, password: string) {
		// Register via API directly (bypass frontend form issues)
		await page.request.post('http://localhost:8000/api/v1/auth/register', {
			data: { email, password },
		});

		// Login via UI
		await page.goto('/auth/login');
		await page.getByLabel('邮箱').fill(email);
		await page.getByLabel('密码').fill(password);
		await page.getByRole('button', { name: '登录' }).click();

		// Wait for dashboard
		await page.waitForURL('**/dashboard**', { timeout: 15000 });
	}

	test('should display todos page', async ({ page }) => {
		const email = `todo_display_${Date.now()}@test.com`;
		await loginUser(page, email, 'password123');

		await page.goto('/dashboard/todos');
		await expect(page.getByRole('heading', { name: '待办事项' })).toBeVisible();
		await expect(page.getByRole('button', { name: '新建待办' })).toBeVisible();
	});

	test('should show empty state when no todos', async ({ page }) => {
		const email = `todo_empty_${Date.now()}@test.com`;
		await loginUser(page, email, 'password123');

		await page.goto('/dashboard/todos');
		await expect(page.getByText('暂无待办事项')).toBeVisible({
			timeout: 10000,
		});
	});

	test('should create a new todo', async ({ page }) => {
		const email = `todo_create_${Date.now()}@test.com`;
		await loginUser(page, email, 'password123');

		await page.goto('/dashboard/todos');

		// Click new todo button
		await page.getByRole('button', { name: '新建待办' }).click();

		// Wait for modal
		await expect(page.getByLabel('标题')).toBeVisible();

		// Fill the form
		await page.getByLabel('标题').fill('Test Todo Item');
		await page.getByLabel('描述（可选）').fill('This is a test description');

		// Submit (use exact match to avoid "创建第一个待办" button)
		await page.getByRole('button', { name: '创建', exact: true }).click();

		// Verify the todo appears in the list
		await expect(page.getByText('Test Todo Item')).toBeVisible({
			timeout: 10000,
		});
	});

	test('should toggle todo completion', async ({ page }) => {
		const email = `todo_toggle_${Date.now()}@test.com`;
		await loginUser(page, email, 'password123');

		await page.goto('/dashboard/todos');

		// Create a todo first
		await page.getByRole('button', { name: '新建待办' }).click();
		await expect(page.getByLabel('标题')).toBeVisible();
		await page.getByLabel('标题').fill('Toggle Test');
		await page.getByRole('button', { name: '创建', exact: true }).click();

		// Wait for todo to appear
		await expect(page.getByText('Toggle Test')).toBeVisible({ timeout: 10000 });

		// Click the checkbox to toggle
		await page.getByRole('checkbox').click();

		// The todo text should have line-through style (completed)
		await expect(page.locator('.line-through')).toBeVisible({ timeout: 5000 });
	});

	test('should delete a todo', async ({ page }) => {
		const email = `todo_delete_${Date.now()}@test.com`;
		await loginUser(page, email, 'password123');

		await page.goto('/dashboard/todos');

		// Create a todo first
		await page.getByRole('button', { name: '新建待办' }).click();
		await expect(page.getByLabel('标题')).toBeVisible();
		await page.getByLabel('标题').fill('To Be Deleted');
		await page.getByRole('button', { name: '创建', exact: true }).click();

		// Wait for todo to appear
		await expect(page.getByText('To Be Deleted')).toBeVisible({
			timeout: 10000,
		});

		// Handle the confirm dialog
		page.on('dialog', (dialog) => dialog.accept());

		// Click delete button (trash icon with destructive class)
		await page.locator('button:has(svg.text-destructive)').click();

		// Verify the todo is deleted
		await expect(page.getByText('To Be Deleted')).not.toBeVisible({
			timeout: 10000,
		});
	});

	test('should navigate to todos from sidebar', async ({ page }) => {
		const email = `todo_nav_${Date.now()}@test.com`;
		await loginUser(page, email, 'password123');

		// Click on todos link in sidebar
		await page.getByRole('link', { name: '待办事项' }).click();

		await expect(page).toHaveURL(/.*\/dashboard\/todos/);
		await expect(page.getByRole('heading', { name: '待办事项' })).toBeVisible();
	});
});
