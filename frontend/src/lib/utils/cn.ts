import { type ClassValue, clsx } from 'clsx';

// Combines class names without relying on tailwind-merge
export function cn(...inputs: ClassValue[]) {
	return clsx(inputs);
}
