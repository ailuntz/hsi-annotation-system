<script lang="ts">
import PublicFooter from './PublicFooter.svelte';
import PublicHeader from './PublicHeader.svelte';
</script>

<div class="flex min-h-screen flex-col">
	<PublicHeader />
	<main class="flex-1">
		<slot />
	</main>
	<PublicFooter />
</div>
