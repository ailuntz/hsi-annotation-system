<script lang="ts">
import { Button } from '$components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '$components/ui/card';
import { Input } from '$components/ui/input';
import { Checkbox } from '$components/ui/checkbox';
import { toasts } from '$lib/stores/ui';
import { onMount } from 'svelte';

const STORAGE_KEY = 'hsi-fixed-preferences';

type TaskType = 'online' | 'offline';

type FixedPreferences = {
	tagFontSize: number;
	tagBackgroundColor: string;
	backgroundRecent: string[];
	tagTextColorOnlineMode: 'follow' | 'custom';
	tagTextColorOnlineCustom: string;
	tagTextColorOffline: string;
	lockCanvas: boolean;
	hideLabels: boolean;
	labelAbove: boolean;
	borderWidth: number;
	controlPointSize: number;
};

const defaultPreferences: FixedPreferences = {
	tagFontSize: 16,
	tagBackgroundColor: '#ffffff',
	backgroundRecent: [],
	tagTextColorOnlineMode: 'follow',
	tagTextColorOnlineCustom: '#ff7a18',
	tagTextColorOffline: '#ffffff',
	lockCanvas: false,
	hideLabels: false,
	labelAbove: true,
	borderWidth: 2,
	controlPointSize: 6,
};

const quickBackgrounds = [
	{ label: '白', value: '#ffffff' },
	{ label: '黑', value: '#000000' },
	{ label: '透明', value: 'transparent' },
];

let preferences = $state<FixedPreferences>({ ...defaultPreferences });
let previewTaskType = $state<TaskType>('online');
let ready = $state(false);
let dirty = $state(false);

function cloneWithDefaults(value: Partial<FixedPreferences> | null | undefined): FixedPreferences {
	const merged = { ...defaultPreferences, ...(value ?? {}) };
	if (!Array.isArray(merged.backgroundRecent)) merged.backgroundRecent = [];
	return merged;
}

onMount(() => {
	if (typeof window === 'undefined') return;
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		if (raw) {
			const parsed = JSON.parse(raw) as Partial<FixedPreferences>;
			preferences = cloneWithDefaults(parsed);
		}
	} catch {
		preferences = { ...defaultPreferences };
	}
	ready = true;
});

function updatePreference<K extends keyof FixedPreferences>(key: K, value: FixedPreferences[K]) {
	preferences = {
		...preferences,
		[key]: value,
	};
	dirty = true;
}

function updateBackgroundColor(value: string) {
	updatePreference('tagBackgroundColor', value);
	if (value !== 'transparent') {
		const normalized = value.toLowerCase();
		const filtered = preferences.backgroundRecent.filter((item) => item !== normalized);
		updatePreference('backgroundRecent', [normalized, ...filtered].slice(0, 4));
	}
}

function handleBackgroundCustom(event: Event) {
	const target = event.currentTarget as HTMLInputElement;
	if (!target.value) return;
	updateBackgroundColor(target.value);
}

function handleSave() {
	if (typeof window === 'undefined') return;
	localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
	window.dispatchEvent(new CustomEvent('hsi-fixed-preferences-change', { detail: preferences }));
	toasts.add({ message: '已保存固定参数', type: 'success' });
	dirty = false;
}

function handleReset() {
	preferences = { ...defaultPreferences, backgroundRecent: [] };
	dirty = true;
}

function getPreviewTextColor() {
	if (previewTaskType === 'online' && preferences.tagTextColorOnlineMode === 'follow') {
		return '#f43f5e';
	}
	if (previewTaskType === 'online') {
		return preferences.tagTextColorOnlineCustom;
	}
	return preferences.tagTextColorOffline;
}

const sampleLabelColor = '#f43f5e';
const sampleOutlineColor = '#22c55e';

function preventInvalidNumber(event: Event) {
	const target = event.currentTarget as HTMLInputElement;
	const value = Number(target.value);
	if (Number.isNaN(value)) {
		target.value = '';
	}
}
</script>

<svelte:head>
	<title>固定参数 - HSI Annotation</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex flex-wrap items-center justify-between gap-4">
		<div>
			<h1 class="text-3xl font-bold">固定参数</h1>
			<p class="text-muted-foreground">统一定义标签样式与画布交互，保存在浏览器本地</p>
		</div>
		<div class="flex flex-wrap items-center gap-3">
			<div class="flex items-center gap-2 text-sm text-muted-foreground">
				<span>预览任务：</span>
				<select
					bind:value={previewTaskType}
					class="rounded-md border bg-transparent px-2 py-1 text-sm"
				>
					<option value="online">在线任务</option>
					<option value="offline">离线任务</option>
				</select>
			</div>
			<Button variant="outline" onclick={handleReset}>恢复默认</Button>
		</div>
	</div>

	<div class="grid gap-6 lg:grid-cols-[2fr_1fr]">
		<Card>
			<CardHeader>
				<CardTitle>标签样式</CardTitle>
			</CardHeader>
			<CardContent class="space-y-6">
				<div class="space-y-2">
					<label class="text-sm font-medium" for="tag-font-size-range">标签字体大小 ({preferences.tagFontSize}px)</label>
					<div class="flex items-center gap-4">
						<input
							type="range"
							min="10"
							max="28"
							step="1"
							id="tag-font-size-range"
							value={preferences.tagFontSize}
							oninput={(event) => {
								const target = event.currentTarget as HTMLInputElement;
								updatePreference('tagFontSize', Number(target.value));
							}}
							class="w-full"
						/>
						<Input
							type="number"
							min="10"
							max="28"
							value={preferences.tagFontSize.toString()}
							oninput={(event) => {
								preventInvalidNumber(event);
								const target = event.currentTarget as HTMLInputElement;
								updatePreference('tagFontSize', Number(target.value));
							}}
							class="w-20"
						/>
					</div>
				</div>

				<div class="space-y-3">
					<p class="text-sm font-medium">标签背景色</p>
					<div class="flex flex-wrap gap-2">
						{#each quickBackgrounds as option}
							<Button
								variant={preferences.tagBackgroundColor === option.value ? 'default' : 'outline'}
								size="sm"
								onclick={() => updateBackgroundColor(option.value)}
							>
								{option.label}
							</Button>
						{/each}
						{#each preferences.backgroundRecent as color}
							<button
								type="button"
								class="h-8 w-8 rounded border"
								style={`background:${color}`}
								onclick={() => updateBackgroundColor(color)}
								aria-label={`使用颜色 ${color}`}
							></button>
						{/each}
						<label class="flex items-center gap-2 text-sm text-muted-foreground">
							自定义
							<input type="color" value={preferences.tagBackgroundColor} oninput={handleBackgroundCustom} />
						</label>
					</div>
				</div>

				<div class="space-y-3">
					<p class="text-sm font-medium">在线任务标签文字颜色</p>
					<div class="space-y-2 rounded-md border p-3 text-sm">
						<label class="flex items-center gap-2">
							<input
								type="radio"
								name="online-text-mode"
								value="follow"
								checked={preferences.tagTextColorOnlineMode === 'follow'}
								onchange={() => updatePreference('tagTextColorOnlineMode', 'follow')}
							/>
							<span>跟随标签种类颜色</span>
						</label>
						<label class="flex items-center gap-2">
							<input
								type="radio"
								name="online-text-mode"
								value="custom"
								checked={preferences.tagTextColorOnlineMode === 'custom'}
								onchange={() => updatePreference('tagTextColorOnlineMode', 'custom')}
							/>
							<span class="flex items-center gap-2">
								使用自定义颜色
								<input
									type="color"
									value={preferences.tagTextColorOnlineCustom}
									oninput={(event) => {
										const target = event.currentTarget as HTMLInputElement;
										updatePreference('tagTextColorOnlineCustom', target.value);
									}}
									disabled={preferences.tagTextColorOnlineMode !== 'custom'}
								/>
							</span>
						</label>
					</div>
				</div>

				<div class="space-y-2">
					<label class="text-sm font-medium" for="offline-text-color">离线任务标签文字颜色</label>
					<input
						id="offline-text-color"
						type="color"
						value={preferences.tagTextColorOffline}
						oninput={(event) => {
							const target = event.currentTarget as HTMLInputElement;
							updatePreference('tagTextColorOffline', target.value);
						}}
					/>
				</div>
			</CardContent>
		</Card>

		<Card>
			<CardHeader>
				<CardTitle>实时预览</CardTitle>
			</CardHeader>
			<CardContent>
				<div class="space-y-4">
					<div
						class="rounded border p-4"
						style={`background:${preferences.tagBackgroundColor === 'transparent' ? 'transparent' : preferences.tagBackgroundColor};`}
					>
						<div
							class="inline-flex items-center gap-2 rounded px-3 py-1 text-sm font-medium"
							style={`font-size:${preferences.tagFontSize}px;color:${getPreviewTextColor()};background:${preferences.hideLabels ? 'transparent' : preferences.tagBackgroundColor === 'transparent' ? 'rgba(0,0,0,0.4)' : preferences.tagBackgroundColor};`}
						>
							<span>示例标签</span>
						</div>
					</div>

					<div class="space-y-2 text-sm">
						<div class="flex items-center gap-2">
							<Checkbox checked={preferences.lockCanvas} onclick={() => updatePreference('lockCanvas', !preferences.lockCanvas)} />
							<span>画布锁定 {preferences.lockCanvas ? '已开启' : '关闭'}</span>
						</div>
						<div class="flex items-center gap-2">
							<Checkbox checked={preferences.hideLabels} onclick={() => updatePreference('hideLabels', !preferences.hideLabels)} />
							<span>隐藏标签 {preferences.hideLabels ? '已开启' : '关闭'}</span>
						</div>
					</div>

					<div class="rounded border p-4">
						<div
							class="relative mx-auto h-32 w-48"
							style={`border:${preferences.borderWidth}px solid ${sampleOutlineColor};`}
						>
							{#if !preferences.hideLabels}
								<div
									class={`absolute left-1/2 -translate-x-1/2 px-2 py-1 text-xs font-semibold`}
									style={`top:${preferences.labelAbove ? '-2rem' : '0.5rem'};font-size:${preferences.tagFontSize}px;color:${getPreviewTextColor()};background:${preferences.tagBackgroundColor === 'transparent' ? 'rgba(255,255,255,0.2)' : preferences.tagBackgroundColor};`}
								>
									Label Preview
								</div>
							{/if}
							<div class="absolute inset-0 flex items-center justify-center text-xs text-muted-foreground">
								轮廓示例
							</div>
							{#if !preferences.hideLabels}
								<div
									class="absolute"
									style={`width:${preferences.controlPointSize}px;height:${preferences.controlPointSize}px;background:${sampleLabelColor};border-radius:9999px;top:4px;left:4px;`}
								></div>
								<div
									class="absolute"
									style={`width:${preferences.controlPointSize}px;height:${preferences.controlPointSize}px;background:${sampleLabelColor};border-radius:9999px;bottom:4px;right:4px;`}
								></div>
							{/if}
						</div>
					</div>
				</div>
			</CardContent>
		</Card>
	</div>

	<Card>
		<CardHeader>
			<CardTitle>视图控制</CardTitle>
		</CardHeader>
		<CardContent class="grid gap-6 md:grid-cols-2">
			<div class="space-y-3 rounded border p-4">
				<label class="flex items-center gap-3 text-sm">
					<span>锁定画布交互</span>
					<Checkbox checked={preferences.lockCanvas} onclick={() => updatePreference('lockCanvas', !preferences.lockCanvas)} />
				</label>
				<label class="flex items-center gap-3 text-sm">
					<span>隐藏所有标签</span>
					<Checkbox checked={preferences.hideLabels} onclick={() => updatePreference('hideLabels', !preferences.hideLabels)} />
				</label>
				<label class="flex items-center gap-3 text-sm">
					<span>标签显示在轮廓上方</span>
					<Checkbox checked={preferences.labelAbove} onclick={() => updatePreference('labelAbove', !preferences.labelAbove)} />
				</label>
			</div>

			<div class="space-y-6 rounded border p-4">
				<div class="space-y-2">
					<label class="text-sm font-medium" for="border-width-range">边框宽度 ({preferences.borderWidth}px)</label>
					<input
						type="range"
						min="1"
						max="10"
						step="1"
						id="border-width-range"
						value={preferences.borderWidth}
						oninput={(event) => {
							const target = event.currentTarget as HTMLInputElement;
							updatePreference('borderWidth', Number(target.value));
						}}
						class="w-full"
					/>
				</div>

				<div class="space-y-2">
					<label class="text-sm font-medium" for="control-point-range">控制点大小 ({preferences.controlPointSize}px)</label>
					<input
						type="range"
						min="2"
						max="16"
						step="1"
						id="control-point-range"
						value={preferences.controlPointSize}
						oninput={(event) => {
							const target = event.currentTarget as HTMLInputElement;
							updatePreference('controlPointSize', Number(target.value));
						}}
						class="w-full"
					/>
				</div>
			</div>
		</CardContent>
	</Card>

	<div class="flex justify-end">
		<Button onclick={handleSave} disabled={!dirty || !ready}>
			保存设置
		</Button>
	</div>
</div>
