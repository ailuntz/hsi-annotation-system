/// <reference types="@sveltejs/kit" />

declare global {
	namespace App {
		interface Error {
			message: string;
			code?: string;
		}
		interface Locals {
			user?: {
				id: number;
				email: string;
				full_name?: string;
			};
		}
		interface PageData {}
		interface PageState {}
		interface Platform {}
	}
}

export {};
