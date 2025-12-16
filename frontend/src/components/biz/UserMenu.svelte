<script lang="ts">
import { goto } from '$app/navigation';
import { Avatar } from '$components/ui/avatar';
import { Button } from '$components/ui/button';
import { auth, currentUser } from '$lib/stores/auth';

let open = false;

function toggleMenu() {
	open = !open;
}

function closeMenu() {
	open = false;
}

function handleLogout() {
	auth.logout();
	goto('/auth/login');
}
</script>

<div class="relative">
	<button
		class="flex items-center gap-2 rounded-full"
		onclick={toggleMenu}
		aria-expanded={open}
	>
		<Avatar
			src={$currentUser?.avatar || '/favicon.svg'}
			alt="用户头像"
			fallback={$currentUser?.full_name || $currentUser?.email || 'U'}
		/>
	</button>

	{#if open}
		<button class="fixed inset-0 z-40" onclick={closeMenu} aria-label="Close menu"></button>

		<div class="absolute right-0 z-50 mt-2 w-56 rounded-md border bg-popover p-1 shadow-lg">
			<div class="px-3 py-2">
				<p class="text-sm font-medium">{$currentUser?.full_name || '用户'}</p>
				<p class="text-xs text-muted-foreground">{$currentUser?.email}</p>
			</div>

			<div class="my-1 h-px bg-border"></div>

			<a
				href="/dashboard/profile"
				class="flex w-full items-center rounded-sm px-3 py-2 text-sm hover:bg-accent"
				onclick={closeMenu}
			>
				个人资料
			</a>
			<a
				href="/dashboard/settings"
				class="flex w-full items-center rounded-sm px-3 py-2 text-sm hover:bg-accent"
				onclick={closeMenu}
			>
				设置
			</a>

			<div class="my-1 h-px bg-border"></div>

			<button
				class="flex w-full items-center rounded-sm px-3 py-2 text-sm text-destructive hover:bg-accent"
				onclick={handleLogout}
			>
				退出登录
			</button>
		</div>
	{/if}
</div>
