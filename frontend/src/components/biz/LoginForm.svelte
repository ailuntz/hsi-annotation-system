<script lang="ts">
import { goto } from '$app/navigation';
import { Button } from '$components/ui/button';
import { FormField, FormLabel, FormMessage } from '$components/ui/form';
import { Input } from '$components/ui/input';
import {
	loginForAccessTokenApiV1AuthLoginPost,
	readCurrentUserApiV1UsersMeGet,
} from '$lib/api';
import { type LoginInput, loginSchema } from '$lib/schemas/auth';
import { auth } from '$lib/stores/auth';
import { toasts } from '$lib/stores/ui';
import { extractApiError, unwrapOrThrow } from '$lib/utils/api';
import { createForm } from 'felte';

let loading = false;

const { form, errors, data } = createForm<LoginInput>({
	validate: (values) => {
		const result = loginSchema.safeParse(values);
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
			const result = await loginForAccessTokenApiV1AuthLoginPost({
				body: {
					username: values.email,
					password: values.password,
				},
			});

			const data = unwrapOrThrow(result, '登录失败');
			auth.setToken(data.access_token);

			// Fetch user info
			const userResult = await readCurrentUserApiV1UsersMeGet();
			if (userResult.data) {
				auth.setUser(userResult.data);
			}

			toasts.add({ message: '登录成功', type: 'success' });
			goto('/dashboard');
		} catch (error) {
			toasts.add({
				message: extractApiError(error, '登录失败'),
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
		<FormLabel for="password">密码</FormLabel>
		<Input
			id="password"
			name="password"
			type="password"
			placeholder="输入密码"
			autocomplete="current-password"
		/>
		<FormMessage error={$errors.password ?? undefined} />
	</FormField>

	<Button type="submit" class="w-full" disabled={loading}>
		{loading ? '登录中...' : '登录'}
	</Button>
</form>
