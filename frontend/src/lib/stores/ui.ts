import { writable } from 'svelte/store';

// Theme store
type Theme = 'light' | 'dark' | 'system';

function createThemeStore() {
	const { subscribe, set } = writable<Theme>('system');

	return {
		subscribe,
		set: (theme: Theme) => {
			localStorage.setItem('theme', theme);
			set(theme);
			applyTheme(theme);
		},
		initialize: () => {
			const stored = localStorage.getItem('theme') as Theme | null;
			const theme = stored || 'system';
			set(theme);
			applyTheme(theme);
		},
	};
}

function applyTheme(theme: Theme) {
	const root = document.documentElement;
	const isDark =
		theme === 'dark' ||
		(theme === 'system' &&
			window.matchMedia('(prefers-color-scheme: dark)').matches);

	root.classList.toggle('dark', isDark);
}

export const theme = createThemeStore();

// Toast store
interface Toast {
	id: string;
	message: string;
	type: 'success' | 'error' | 'info' | 'warning';
	duration?: number;
}

function createToastStore() {
	const { subscribe, update } = writable<Toast[]>([]);

	const add = (toast: Omit<Toast, 'id'>) => {
		const id = crypto.randomUUID();
		const newToast = { ...toast, id };
		update((toasts) => [...toasts, newToast]);

		if (toast.duration !== 0) {
			setTimeout(() => {
				update((toasts) => toasts.filter((t) => t.id !== id));
			}, toast.duration || 3000);
		}

		return id;
	};

	const remove = (id: string) => {
		update((toasts) => toasts.filter((t) => t.id !== id));
	};

	return {
		subscribe,
		add,
		remove,
		success: (message: string, duration?: number) => {
			return add({ message, type: 'success', duration });
		},
		error: (message: string, duration?: number) => {
			return add({ message, type: 'error', duration });
		},
		info: (message: string, duration?: number) => {
			return add({ message, type: 'info', duration });
		},
		warning: (message: string, duration?: number) => {
			return add({ message, type: 'warning', duration });
		},
	};
}

export const toasts = createToastStore();

// Sidebar store
export const sidebarOpen = writable(true);

// Language store
export const locale = writable<string>('zh');
