<script lang="ts">
import { Avatar } from '$components/ui/avatar';
import { Button } from '$components/ui/button';
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '$components/ui/card';
import { FormField, FormLabel, FormMessage } from '$components/ui/form';
import { Input } from '$components/ui/input';
import {
	updateCurrentUserApiV1UsersMePatch,
	uploadAvatarApiV1UsersMeAvatarPost,
} from '$lib/api';
import { auth, currentUser } from '$lib/stores/auth';
import { toasts } from '$lib/stores/ui';
import { extractApiError, unwrapOrThrow } from '$lib/utils/api';
import { onMount } from 'svelte';

let loading = $state(false);
let avatarLoading = $state(false);
let fullName = $state('');
let email = $state('');
let avatarUrl = $state('');
let fileInput: HTMLInputElement;

onMount(() => {
	if ($currentUser) {
		fullName = $currentUser.full_name || '';
		email = $currentUser.email;
		avatarUrl = $currentUser.avatar || '';
	}
});

$effect(() => {
	if ($currentUser) {
		fullName = $currentUser.full_name || '';
		email = $currentUser.email;
		avatarUrl = $currentUser.avatar || '';
	}
});

async function handleSubmit() {
	loading = true;
	try {
		const result = await updateCurrentUserApiV1UsersMePatch({
			body: {
				full_name: fullName,
			},
		});

		const user = unwrapOrThrow(result, '更新失败');
		auth.setUser(user);
		toasts.add({ message: '个人资料已更新', type: 'success' });
	} catch (error) {
		toasts.add({
			message: extractApiError(error, '更新失败'),
			type: 'error',
		});
	} finally {
		loading = false;
	}
}

const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];

async function validateImageFile(file: File): Promise<boolean> {
	// 1. 检查 MIME 类型
	if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
		return false;
	}

	// 2. 检查文件内容的 magic bytes
	const buffer = await file.slice(0, 12).arrayBuffer();
	const bytes = new Uint8Array(buffer);

	// JPEG: FF D8 FF
	if (bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff) {
		return true;
	}
	// PNG: 89 50 4E 47 0D 0A 1A 0A
	if (
		bytes[0] === 0x89 &&
		bytes[1] === 0x50 &&
		bytes[2] === 0x4e &&
		bytes[3] === 0x47 &&
		bytes[4] === 0x0d &&
		bytes[5] === 0x0a &&
		bytes[6] === 0x1a &&
		bytes[7] === 0x0a
	) {
		return true;
	}
	// GIF: 47 49 46 38 (GIF8)
	if (bytes[0] === 0x47 && bytes[1] === 0x49 && bytes[2] === 0x46 && bytes[3] === 0x38) {
		return true;
	}
	// WebP: RIFF....WEBP
	if (
		bytes[0] === 0x52 &&
		bytes[1] === 0x49 &&
		bytes[2] === 0x46 &&
		bytes[3] === 0x46 &&
		bytes[8] === 0x57 &&
		bytes[9] === 0x45 &&
		bytes[10] === 0x42 &&
		bytes[11] === 0x50
	) {
		return true;
	}

	return false;
}

async function handleAvatarUpload(event: Event) {
	const input = event.target as HTMLInputElement;
	const file = input.files?.[0];
	if (!file) return;

	// 检查文件大小
	if (file.size > 5 * 1024 * 1024) {
		toasts.add({ message: '文件大小不能超过 5MB', type: 'error' });
		return;
	}

	// 检查 MIME 类型
	if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
		toasts.add({ message: '不支持的文件类型，请上传 JPG、PNG、GIF 或 WebP 格式', type: 'error' });
		return;
	}

	// 验证文件内容
	const isValidImage = await validateImageFile(file);
	if (!isValidImage) {
		toasts.add({ message: '无效的图片文件', type: 'error' });
		return;
	}

	avatarLoading = true;
	try {
		const result = await uploadAvatarApiV1UsersMeAvatarPost({
			body: { file },
		});

		const user = unwrapOrThrow(result, '上传失败');
		auth.setUser(user);
		toasts.add({ message: '头像已更新', type: 'success' });
	} catch (error) {
		toasts.add({
			message: extractApiError(error, '上传失败'),
			type: 'error',
		});
	} finally {
		avatarLoading = false;
		input.value = '';
	}
}
</script>

<svelte:head>
	<title>个人资料 - MyApp</title>
</svelte:head>

<div class="space-y-6">
	<div>
		<h1 class="text-3xl font-bold">个人资料</h1>
		<p class="text-muted-foreground">管理您的个人信息</p>
	</div>

	<Card>
		<CardHeader>
			<CardTitle>基本信息</CardTitle>
			<CardDescription>更新您的个人资料信息</CardDescription>
		</CardHeader>
		<CardContent>
			<div class="flex flex-col md:flex-row gap-8">
				<!-- Avatar Section -->
				<div class="flex flex-col items-center gap-4">
					<div class="relative">
						<Avatar
							src={avatarUrl || '/favicon.svg'}
							alt="头像"
							fallback={$currentUser?.full_name || $currentUser?.email || 'U'}
							class="h-24 w-24 text-2xl"
						/>
						{#if avatarLoading}
							<div class="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full">
								<svg class="h-6 w-6 animate-spin text-white" fill="none" viewBox="0 0 24 24">
									<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
									<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
								</svg>
							</div>
						{/if}
					</div>
					<input
						bind:this={fileInput}
						type="file"
						accept="image/jpeg,image/png,image/gif,image/webp"
						class="hidden"
						onchange={handleAvatarUpload}
					/>
					<Button
						variant="outline"
						size="sm"
						onclick={() => fileInput.click()}
						disabled={avatarLoading}
					>
						更换头像
					</Button>
					<p class="text-xs text-muted-foreground text-center">
						支持 JPG、PNG、GIF、WebP<br />最大 5MB
					</p>
				</div>

				<!-- Form Section -->
				<form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }} class="space-y-4 flex-1 max-w-md">
					<FormField>
						<FormLabel for="email">邮箱</FormLabel>
						<Input id="email" type="email" value={email} disabled />
						<p class="text-xs text-muted-foreground">邮箱暂不支持修改</p>
					</FormField>

					<FormField>
						<FormLabel for="fullName">姓名</FormLabel>
						<Input id="fullName" bind:value={fullName} placeholder="您的姓名" />
					</FormField>

					<Button type="submit" disabled={loading}>
						{loading ? '保存中...' : '保存更改'}
					</Button>
				</form>
			</div>
		</CardContent>
	</Card>
</div>
