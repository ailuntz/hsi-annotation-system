<script lang="ts">
import { Button } from '$components/ui/button';
import { Input } from '$components/ui/input';
import { Modal } from '$components/ui/modal';
import { Checkbox } from '$components/ui/checkbox';
import type { SpectralModeResponse } from '$lib/api';
import { createEventDispatcher } from 'svelte';

const GAIN_ALGORITHMS = [
	{ label: 'Percentile + Gamma', value: 'percentile-gamma' },
	{ label: 'Percentile', value: 'percentile' },
	{ label: 'Gamma', value: 'gamma' },
	{ label: 'Linear', value: 'linear' },
	{ label: 'Log', value: 'log' },
	{ label: 'Histogram', value: 'histogram' },
	{ label: 'Raw', value: 'raw' },
];

type SubmitDetail = {
	body: {
		name: string;
		r_channel: number;
		g_channel: number;
		b_channel: number;
		r_gain: number;
		g_gain: number;
		b_gain: number;
		gain_algorithm: string;
		dark_calibration: boolean;
		white_calibration: boolean;
	};
	modeId?: number;
};

let { open = $bindable(false), mode = null } = $props<{
	open?: boolean;
	mode?: SpectralModeResponse | null;
}>();

const dispatch = createEventDispatcher<{
	close: void;
	submit: SubmitDetail;
}>();

let name = $state('');
let rChannel = $state('0');
let gChannel = $state('0');
let bChannel = $state('0');
let rGain = $state('1');
let gGain = $state('1');
let bGain = $state('1');
let gainAlgorithm = $state('linear');
let darkCalibration = $state(false);
let whiteCalibration = $state(false);

function resetForm() {
	name = mode?.name ?? '';
	rChannel = (mode?.r_channel ?? 0).toString();
	gChannel = (mode?.g_channel ?? 0).toString();
	bChannel = (mode?.b_channel ?? 0).toString();
	rGain = (mode?.r_gain ?? 1).toString();
	gGain = (mode?.g_gain ?? 1).toString();
	bGain = (mode?.b_gain ?? 1).toString();
	gainAlgorithm = mode?.gain_algorithm ?? 'linear';
	darkCalibration = mode?.dark_calibration ?? false;
	whiteCalibration = mode?.white_calibration ?? false;
}

$effect(() => {
	if (open) {
		resetForm();
	}
});

function parseNumber(value: string, fallback: number) {
	const num = Number(value);
	return Number.isFinite(num) ? num : fallback;
}

function handleSubmit(event: Event) {
	event.preventDefault();
	dispatch('submit', {
		body: {
			name: name.trim(),
			r_channel: parseNumber(rChannel, 0),
			g_channel: parseNumber(gChannel, 0),
			b_channel: parseNumber(bChannel, 0),
			r_gain: parseNumber(rGain, 1),
			g_gain: parseNumber(gGain, 1),
			b_gain: parseNumber(bGain, 1),
			gain_algorithm: gainAlgorithm.trim() || 'linear',
			dark_calibration: darkCalibration,
			white_calibration: whiteCalibration,
		},
		modeId: mode?.id,
	});
}

function handleClose() {
	dispatch('close');
}
</script>

<Modal bind:open title={mode ? '编辑显示模式' : '新建显示模式'} onclose={handleClose} class="max-w-3xl">
	<form class="space-y-6" onsubmit={handleSubmit}>
		<div class="grid gap-4 md:grid-cols-2">
			<div class="space-y-2">
				<label for="mode-name" class="text-sm font-medium">模式名称</label>
				<Input id="mode-name" bind:value={name} placeholder="例如：植被增强" />
			</div>
			<div class="space-y-2">
				<label for="gain-algorithm" class="text-sm font-medium">增益算法</label>
				<select
					id="gain-algorithm"
					class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
					bind:value={gainAlgorithm}
				>
					{#each GAIN_ALGORITHMS as item}
						<option value={item.value}>{item.label}</option>
					{/each}
				</select>
			</div>
		</div>

		<div class="grid gap-4 md:grid-cols-3">
			<div class="space-y-2">
				<label for="r-channel" class="text-sm font-medium">R 通道</label>
				<Input id="r-channel" type="number" bind:value={rChannel} min="0" />
			</div>
			<div class="space-y-2">
				<label for="g-channel" class="text-sm font-medium">G 通道</label>
				<Input id="g-channel" type="number" bind:value={gChannel} min="0" />
			</div>
			<div class="space-y-2">
				<label for="b-channel" class="text-sm font-medium">B 通道</label>
				<Input id="b-channel" type="number" bind:value={bChannel} min="0" />
			</div>
		</div>

		<div class="grid gap-4 md:grid-cols-3">
			<div class="space-y-2">
				<label for="r-gain" class="text-sm font-medium">
					R 增益
					<span class="text-xs text-muted-foreground">(-4096~4096)</span>
				</label>
				<Input id="r-gain" type="number" step="1" min="-4096" max="4096" bind:value={rGain} />
			</div>
			<div class="space-y-2">
				<label for="g-gain" class="text-sm font-medium">
					G 增益
					<span class="text-xs text-muted-foreground">(-4096~4096)</span>
				</label>
				<Input id="g-gain" type="number" step="1" min="-4096" max="4096" bind:value={gGain} />
			</div>
			<div class="space-y-2">
				<label for="b-gain" class="text-sm font-medium">
					B 增益
					<span class="text-xs text-muted-foreground">(-4096~4096)</span>
				</label>
				<Input id="b-gain" type="number" step="1" min="-4096" max="4096" bind:value={bGain} />
			</div>
		</div>

		<div class="grid gap-4 md:grid-cols-2">
			<label class="flex items-center gap-3 text-sm font-medium">
				<Checkbox bind:checked={darkCalibration} />
				<span>暗场校准</span>
			</label>
			<label class="flex items-center gap-3 text-sm font-medium">
				<Checkbox bind:checked={whiteCalibration} />
				<span>白板校准</span>
			</label>
		</div>

		<div class="flex justify-end gap-2">
			<Button type="button" variant="outline" onclick={handleClose}>取消</Button>
			<Button type="submit">{mode ? '保存' : '创建'}</Button>
		</div>
	</form>
</Modal>
