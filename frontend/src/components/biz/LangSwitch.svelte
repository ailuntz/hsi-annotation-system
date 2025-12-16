<script lang="ts">
import { Button } from '$components/ui/button';
import { locale } from '$lib/stores/ui';

function switchLang() {
	locale.update((current) => (current === 'zh' ? 'en' : 'zh'));
}
</script>

<Button variant="ghost" size="sm" onclick={switchLang}>
	{$locale === 'zh' ? 'EN' : '中文'}
</Button>
