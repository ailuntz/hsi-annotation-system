export function getItem<T>(key: string, defaultValue: T): T {
	if (typeof window === 'undefined') return defaultValue;

	try {
		const item = localStorage.getItem(key);
		return item ? JSON.parse(item) : defaultValue;
	} catch {
		return defaultValue;
	}
}

export function setItem<T>(key: string, value: T): void {
	if (typeof window === 'undefined') return;

	try {
		localStorage.setItem(key, JSON.stringify(value));
	} catch {
		console.error(`Failed to save ${key} to localStorage`);
	}
}

export function removeItem(key: string): void {
	if (typeof window === 'undefined') return;
	localStorage.removeItem(key);
}

export function clearStorage(): void {
	if (typeof window === 'undefined') return;
	localStorage.clear();
}
