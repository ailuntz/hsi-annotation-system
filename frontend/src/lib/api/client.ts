import { goto } from '$app/navigation';
import { browser } from '$app/environment';
import { client } from './generated';

// API 基础 URL：生产环境从环境变量获取，开发环境使用相对路径（通过 Vite 代理）
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Share the generated client so SDK functions use the same config/interceptors
client.setConfig({
	baseUrl: API_BASE_URL,
});

// Add auth token interceptor
client.interceptors.request.use((request) => {
	if (browser) {
		const token = localStorage.getItem('access_token');
		if (token) {
			request.headers.set('Authorization', `Bearer ${token}`);
		}
	}
	return request;
});

// 标记是否正在处理 401 跳转，防止重复跳转
let isRedirectingToLogin = false;

// Add response interceptor for error handling
client.interceptors.response.use((response, request) => {
	// 仅在浏览器环境处理 401
	if (!browser) return response;

	// 检查是否为 401 且不是认证相关的请求
	const isAuthEndpoint = request.url.includes('/api/v1/auth/login') ||
		request.url.includes('/api/v1/auth/register');

	if (response.status === 401 && !isAuthEndpoint && !isRedirectingToLogin) {
		isRedirectingToLogin = true;
		localStorage.removeItem('access_token');
		localStorage.removeItem('user');

		// 使用 SvelteKit 的 goto 进行导航，避免页面刷新
		goto('/auth/login').finally(() => {
			isRedirectingToLogin = false;
		});
	}
	return response;
});

export const apiClient = client;
