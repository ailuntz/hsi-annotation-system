<script lang="ts">
import { page } from '$app/stores';
import { Button } from '$components/ui/button';
</script>

<svelte:head>
	<title>错误 - {$page.status}</title>
</svelte:head>

<div class="flex min-h-screen flex-col items-center justify-center">
	<h1 class="text-6xl font-bold">{$page.status}</h1>
	<p class="mt-4 text-xl text-muted-foreground">
		{$page.error?.message || '页面未找到'}
	</p>
	<a href="/" class="mt-8">
		<Button>返回首页</Button>
	</a>
</div>
