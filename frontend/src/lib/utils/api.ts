type ApiResult<T> = {
	data?: T;
	error?: unknown;
};

export function extractApiError(error: unknown, fallback = '请求失败') {
	if (!error) return fallback;
	if (typeof error === 'string') return error;
	if (error instanceof Error) return error.message;
	if (typeof error === 'object' && error !== null) {
		if ('message' in error && typeof error.message === 'string') {
			return error.message;
		}

		const detail = (error as { detail?: unknown }).detail;
		if (typeof detail === 'string') return detail;
		if (Array.isArray(detail) && detail.length > 0) {
			const first = detail[0] as { msg?: unknown };
			if (typeof first?.msg === 'string') return first.msg;
		}
	}
	return fallback;
}

export function unwrapOrThrow<T>(result: ApiResult<T>, fallback = '请求失败'): T {
	if (result.data !== undefined) return result.data;
	throw new Error(extractApiError(result.error, fallback));
}
