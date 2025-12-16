<script lang="ts">
import LoginForm from '$components/biz/LoginForm.svelte';
import {
	Card,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
} from '$components/ui/card';
</script>

<svelte:head>
	<title>登录 - MyApp</title>
</svelte:head>

<Card class="w-full max-w-md">
	<CardHeader class="text-center">
		<CardTitle class="text-2xl">欢迎回来</CardTitle>
		<CardDescription>请输入您的账号信息登录</CardDescription>
	</CardHeader>
	<CardContent>
		<LoginForm />
	</CardContent>
	<CardFooter class="justify-center">
		<p class="text-sm text-muted-foreground">
			还没有账号？
			<a href="/auth/register" class="text-primary hover:underline">立即注册</a>
		</p>
	</CardFooter>
</Card>
