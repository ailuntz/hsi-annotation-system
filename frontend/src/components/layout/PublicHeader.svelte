<script lang="ts">
import ThemeToggle from '$components/biz/ThemeToggle.svelte';
import { Button } from '$components/ui/button';
import { onDestroy, onMount } from 'svelte';

const brandWords = ['北极星', 'Polaris HSI', '专业光谱标注平台'];
let displayText = brandWords[0];
let wordIndex = 0;
let charIndex = 0;
let deleting = false;
let timer: ReturnType<typeof setTimeout> | null = null;

function schedule(delay: number) {
	timer = setTimeout(step, delay);
}

function step() {
	const word = brandWords[wordIndex];
	if (!deleting) {
		displayText = word.slice(0, charIndex + 1);
		charIndex += 1;
		if (charIndex === word.length) {
			deleting = true;
			return schedule(1600);
		}
		return schedule(140);
	}
	displayText = word.slice(0, Math.max(charIndex - 1, 0));
	charIndex -= 1;
	if (charIndex === 0) {
		deleting = false;
		wordIndex = (wordIndex + 1) % brandWords.length;
		return schedule(400);
	}
	return schedule(90);
}

onMount(() => {
	charIndex = 0;
	displayText = '';
	schedule(200);
});

onDestroy(() => {
	if (timer) clearTimeout(timer);
});
</script>

<header class="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
	<div class="container mx-auto flex h-14 items-center justify-between gap-4 px-4">
		<a href="/" class="flex w-48 items-center space-x-2">
			<span class="typewriter text-xl font-black">
				{displayText}
				<span class="caret"></span>
			</span>
		</a>

		<nav class="hidden flex-1 items-center justify-center space-x-6 md:flex">
			<a href="/" class="text-sm font-medium transition-colors hover:text-primary">
				首页
			</a>
			<a href="/features" class="text-sm font-medium text-muted-foreground transition-colors hover:text-primary">
				功能
			</a>
			<a href="/pricing" class="text-sm font-medium text-muted-foreground transition-colors hover:text-primary">
				价格
			</a>
		</nav>

		<div class="flex w-48 items-center justify-end space-x-4">
			<ThemeToggle />
			<a href="/auth/login">
				<Button variant="ghost" size="sm">登录</Button>
			</a>
			<a href="/auth/register">
				<Button size="sm">注册</Button>
			</a>
		</div>
	</div>
</header>

<style>
.typewriter {
	background-image: linear-gradient(120deg, #34d399, #3b82f6 45%, #a855f7);
	-webkit-background-clip: text;
	background-clip: text;
	color: transparent;
	text-transform: uppercase;
	letter-spacing: 0.08em;
}

.typewriter .caret {
	display: inline-block;
	width: 2px;
	height: 1.2em;
	margin-left: 4px;
	background-color: currentColor;
	animation: blink 1s steps(1, end) infinite;
	vertical-align: middle;
}

@keyframes blink {
	0%,
	50% {
		opacity: 1;
	}
	50%,
	100% {
		opacity: 0;
	}
}
</style>
