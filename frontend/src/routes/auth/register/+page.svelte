<script lang="ts">
import RegisterForm from '$components/biz/RegisterForm.svelte';
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
	<title>注册 - MyApp</title>
</svelte:head>

<Card class="w-full max-w-md">
	<CardHeader class="text-center">
		<CardTitle class="text-2xl">创建账号</CardTitle>
		<CardDescription>填写以下信息注册新账号</CardDescription>
	</CardHeader>
	<CardContent>
		<RegisterForm />
	</CardContent>
	<CardFooter class="justify-center">
		<p class="text-sm text-muted-foreground">
			已有账号？
			<a href="/auth/login" class="text-primary hover:underline">立即登录</a>
		</p>
	</CardFooter>
</Card>
