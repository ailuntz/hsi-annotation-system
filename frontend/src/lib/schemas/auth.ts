import { z } from 'zod';

export const loginSchema = z.object({
	email: z.string().email('请输入有效的邮箱地址'),
	password: z.string().min(6, '密码至少6个字符'),
});

export const registerSchema = z
	.object({
		email: z.string().email('请输入有效的邮箱地址'),
		full_name: z.string().min(2, '姓名至少2个字符').optional(),
		password: z.string().min(6, '密码至少6个字符'),
		confirmPassword: z.string().min(6, '密码至少6个字符'),
	})
	.refine((data) => data.password === data.confirmPassword, {
		message: '两次密码不一致',
		path: ['confirmPassword'],
	});

export type LoginInput = z.infer<typeof loginSchema>;
export type RegisterInput = z.infer<typeof registerSchema>;
