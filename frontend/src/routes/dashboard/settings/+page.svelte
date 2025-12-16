<script lang="ts">
import { goto } from '$app/navigation';
import { Button } from '$components/ui/button';
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '$components/ui/card';
import { deleteCurrentUserApiV1UsersMeDelete } from '$lib/api/generated';
import { auth } from '$lib/stores/auth';
import { theme, toasts } from '$lib/stores/ui';

type Theme = 'light' | 'dark' | 'system';

let isDeleting = $state(false);
let showDeleteConfirm = $state(false);

function setTheme(t: Theme) {
	theme.set(t);
}

async function handleDeleteAccount() {
	if (!showDeleteConfirm) {
		showDeleteConfirm = true;
		return;
	}

	isDeleting = true;
	try {
		const { error } = await deleteCurrentUserApiV1UsersMeDelete();
		if (error) {
			toasts.error('删除账号失败，请稍后重试');
			return;
		}
		auth.logout();
		toasts.success('账号已删除');
		goto('/auth/login');
	} catch {
		toasts.error('删除账号失败，请稍后重试');
	} finally {
		isDeleting = false;
		showDeleteConfirm = false;
	}
}

function cancelDelete() {
	showDeleteConfirm = false;
}
</script>

<svelte:head>
	<title>设置 - MyApp</title>
</svelte:head>

<div class="space-y-6">
	<div>
		<h1 class="text-3xl font-bold">设置</h1>
		<p class="text-muted-foreground">管理您的应用设置</p>
	</div>

	<Card>
		<CardHeader>
			<CardTitle>外观</CardTitle>
			<CardDescription>自定义应用的外观主题</CardDescription>
		</CardHeader>
		<CardContent>
			<div class="flex flex-wrap gap-2">
				<Button
					variant={$theme === 'light' ? 'default' : 'outline'}
					onclick={() => setTheme('light')}
				>
					<svg class="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
					</svg>
					浅色
				</Button>
				<Button
					variant={$theme === 'dark' ? 'default' : 'outline'}
					onclick={() => setTheme('dark')}
				>
					<svg class="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
					</svg>
					深色
				</Button>
				<Button
					variant={$theme === 'system' ? 'default' : 'outline'}
					onclick={() => setTheme('system')}
				>
					<svg class="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
					</svg>
					跟随系统
				</Button>
			</div>
		</CardContent>
	</Card>

	<Card>
		<CardHeader>
			<CardTitle>通知</CardTitle>
			<CardDescription>配置通知偏好设置</CardDescription>
		</CardHeader>
		<CardContent>
			<p class="text-muted-foreground">通知设置功能即将推出...</p>
		</CardContent>
	</Card>

	<Card>
		<CardHeader>
			<CardTitle>危险区域</CardTitle>
			<CardDescription>以下操作不可撤销，请谨慎操作</CardDescription>
		</CardHeader>
		<CardContent>
			{#if showDeleteConfirm}
				<div class="space-y-3">
					<p class="text-sm text-destructive font-medium">
						确定要删除账号吗？此操作无法撤销，所有数据将被永久删除。
					</p>
					<div class="flex gap-2">
						<Button variant="destructive" onclick={handleDeleteAccount} disabled={isDeleting}>
							{isDeleting ? '删除中...' : '确认删除'}
						</Button>
						<Button variant="outline" onclick={cancelDelete} disabled={isDeleting}>
							取消
						</Button>
					</div>
				</div>
			{:else}
				<Button variant="destructive" onclick={handleDeleteAccount}>删除账号</Button>
			{/if}
		</CardContent>
	</Card>
</div>
