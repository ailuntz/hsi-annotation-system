<script lang="ts">
import { goto } from '$app/navigation';
import { Button } from '$components/ui/button';
import { FormField, FormLabel, FormMessage } from '$components/ui/form';
import { Input } from '$components/ui/input';
import { registerApiV1AuthRegisterPost } from '$lib/api';
import { type RegisterInput, registerSchema } from '$lib/schemas/auth';
import { toasts } from '$lib/stores/ui';
import { extractApiError, unwrapOrThrow } from '$lib/utils/api';
import { createForm } from 'felte';

let loading = false;

const { form, errors } = createForm<RegisterInput>({
	validate: (values) => {
		const result = registerSchema.safeParse(values);
		if (result.success) return {};

		const errors: Record<string, string> = {};
		for (const error of result.error.errors) {
			if (error.path[0]) {
				errors[error.path[0].toString()] = error.message;
			}
		}
		return errors;
	},
	onSubmit: async (values) => {
		loading = true;
		try {
			const result = await registerApiV1AuthRegisterPost({
				body: {
					email: values.email,
					password: values.password,
					full_name: values.full_name,
				},
			});

			unwrapOrThrow(result, '注册失败');

			toasts.add({ message: '注册成功，请登录', type: 'success' });
			goto('/auth/login');
		} catch (error) {
			toasts.add({
				message: extractApiError(error, '注册失败'),
				type: 'error',
			});
		} finally {
			loading = false;
		}
	},
});
</script>

<form use:form class="space-y-4">
	<FormField>
		<FormLabel for="email">邮箱</FormLabel>
		<Input
			id="email"
			name="email"
			type="email"
			placeholder="your@email.com"
			autocomplete="email"
		/>
		<FormMessage error={$errors.email ?? undefined} />
	</FormField>

	<FormField>
		<FormLabel for="full_name">姓名（可选）</FormLabel>
		<Input
			id="full_name"
			name="full_name"
			type="text"
			placeholder="您的姓名"
			autocomplete="name"
		/>
		<FormMessage error={$errors.full_name ?? undefined} />
	</FormField>

	<FormField>
		<FormLabel for="password">密码</FormLabel>
		<Input
			id="password"
			name="password"
			type="password"
			placeholder="至少6个字符"
			autocomplete="new-password"
		/>
		<FormMessage error={$errors.password ?? undefined} />
	</FormField>

	<FormField>
		<FormLabel for="confirmPassword">确认密码</FormLabel>
		<Input
			id="confirmPassword"
			name="confirmPassword"
			type="password"
			placeholder="再次输入密码"
			autocomplete="new-password"
		/>
		<FormMessage error={$errors.confirmPassword ?? undefined} />
	</FormField>

	<Button type="submit" class="w-full" disabled={loading}>
		{loading ? '注册中...' : '注册'}
	</Button>
</form>
