<script lang="ts">
import { goto } from '$app/navigation';
import { auth, isAuthenticated } from '$lib/stores/auth';
import { onMount } from 'svelte';

onMount(() => {
	const token = auth.initialize();
	if (token) {
		// If already has token, redirect to dashboard
		goto('/dashboard');
	}
});
</script>

<div class="flex min-h-screen items-center justify-center bg-muted/50">
	<slot />
</div>
