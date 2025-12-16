<script lang="ts">
import { page } from '$app/stores';
import { sidebarOpen } from '$lib/stores/ui';
import { cn } from '$lib/utils/cn';

const navItems = [
	{ href: '/dashboard', label: '仪表盘', icon: 'home' },
	{ href: '/dashboard/todos', label: '待办事项', icon: 'todo' },
	{ href: '/dashboard/preset-labels', label: '预设标注组', icon: 'tag' },
	{ href: '/dashboard/preset-display-modes', label: '预设显示模式', icon: 'spectral' },
	{ href: '/dashboard/fixed-preferences', label: '固定参数', icon: 'prefs' },
	{ href: '/dashboard/projects', label: '在线项目', icon: 'projects' },
	{ href: '/dashboard/online-tasks', label: '在线任务', icon: 'tasks' },
	{ href: '/dashboard/profile', label: '个人资料', icon: 'user' },
	{ href: '/dashboard/settings', label: '设置', icon: 'settings' },
];

let currentPath = $derived($page.url.pathname);
</script>

<aside
	class={cn(
		'fixed inset-y-0 left-0 z-50 w-64 transform border-r bg-background transition-transform duration-200 lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 lg:inset-y-auto',
		$sidebarOpen ? 'translate-x-0' : '-translate-x-full',
	)}
>
	<div class="flex h-14 items-center border-b px-4">
		<a href="/dashboard" class="flex items-center gap-2 font-semibold">
			<span class="text-xl">光谱标注平台</span>
		</a>
	</div>

	<nav class="flex flex-col gap-1 p-4">
		{#each navItems as item}
			<a
				href={item.href}
				class={cn(
					'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
					currentPath === item.href
						? 'bg-accent text-accent-foreground'
						: 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
				)}
			>
				{#if item.icon === 'home'}
					<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
					</svg>
				{:else if item.icon === 'todo'}
					<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
					</svg>
				{:else if item.icon === 'user'}
					<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
					</svg>
				{:else if item.icon === 'tag'}
					<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h6l7 7-6 6-7-7V7z" />
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7l-4 4 7 7" />
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 10h.01" />
					</svg>
				{:else if item.icon === 'spectral'}
					<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3l8 6-8 12-8-12 8-6z" />
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v18" />
					</svg>
				{:else if item.icon === 'projects'}
					<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7h18M3 12h18M3 17h18" />
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7v10M12 7v10M17 7v10" />
					</svg>
				{:else if item.icon === 'tasks'}
					<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5h12M9 12h12M9 19h12M5 5h.01M5 12h.01M5 19h.01" />
					</svg>
				{:else if item.icon === 'prefs'}
					<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7h16M4 12h10M4 17h6" />
						<circle cx="16" cy="12" r="1.5" />
						<circle cx="20" cy="17" r="1.5" />
						<circle cx="8" cy="7" r="1.5" />
					</svg>
				{:else if item.icon === 'settings'}
					<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
					</svg>
				{/if}
				{item.label}
			</a>
		{/each}
	</nav>
</aside>

<!-- Backdrop for mobile -->
{#if $sidebarOpen}
	<button
		class="fixed inset-0 z-40 bg-black/50 lg:hidden"
		onclick={() => sidebarOpen.set(false)}
		aria-label="Close sidebar"
	></button>
{/if}
