<script lang="ts">
import '../styles/app.css';
import { ToastContainer } from '$components/ui/toast';
import { theme } from '$lib/stores/ui';
import { onMount } from 'svelte';

onMount(() => {
	theme.initialize();
});
</script>

<slot />
<ToastContainer />
