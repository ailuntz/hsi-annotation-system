<script lang="ts">
import { Button } from '$components/ui/button';
import { Input } from '$components/ui/input';
import { Modal } from '$components/ui/modal';
import type { LabelGroupResponse } from '$lib/api';
import { createEventDispatcher } from 'svelte';

type LabelItem = {
	name: string;
	color: string;
	order_index: number;
};

type SubmitDetail = {
	body: {
		name: string;
		labels: LabelItem[];
	};
	groupId?: number;
};

let { open = $bindable(false), group = null } = $props<{
	open?: boolean;
	group?: LabelGroupResponse | null;
}>();

const dispatch = createEventDispatcher<{
	close: void;
	submit: SubmitDetail;
}>();

let name = $state('');
let labels = $state<LabelItem[]>([]);

function randomColor() {
	return `#${Math.floor(Math.random() * 0xffffff)
		.toString(16)
		.padStart(6, '0')
		.toUpperCase()}`;
}

function resetForm() {
	name = group?.name ?? '';
	if (group?.labels?.length) {
		labels = group.labels.map((label: LabelGroupResponse['labels'][number], idx: number): LabelItem => ({
			name: label.name,
			color: label.color,
			order_index: label.order_index ?? idx,
		}));
	} else {
		labels = [
			{
				name: '',
				color: randomColor(),
				order_index: 0,
			},
		];
	}
}

$effect(() => {
	if (open) {
		resetForm();
	}
});

function addLabel() {
	labels = [
		...labels,
		{
			name: '',
			color: randomColor(),
			order_index: labels.length,
		},
	];
}

function updateLabel(index: number, field: keyof LabelItem, value: string) {
	labels = labels.map((item, idx) =>
		idx === index
			? {
					...item,
					[field]: field === 'color' ? value.toUpperCase() : value,
					order_index: idx,
			  }
			: item,
	);
}

function removeLabel(index: number) {
	if (labels.length === 1) {
		labels = [
			{
				name: '',
				color: randomColor(),
				order_index: 0,
			},
		];
		return;
	}
	labels = labels
		.filter((_, idx) => idx !== index)
		.map((item, idx) => ({
			...item,
			order_index: idx,
		}));
}

function handleSubmit(event: Event) {
	event.preventDefault();
	const prepared = labels.map((item, idx) => ({
		name: item.name.trim(),
		color: item.color || randomColor(),
		order_index: idx,
	}));
	dispatch('submit', {
		body: {
			name: name.trim(),
			labels: prepared,
		},
		groupId: group?.id,
	});
}

function handleClose() {
	dispatch('close');
}
</script>

<Modal bind:open title={group ? '编辑标签组' : '新建标签组'} onclose={handleClose} class="max-w-2xl">
	<form class="space-y-6" onsubmit={handleSubmit}>
		<div class="space-y-2">
			<label class="text-sm font-medium" for="group-name">标签组名称</label>
			<Input id="group-name" bind:value={name} placeholder="输入标签组名称" />
		</div>

		<div class="space-y-3">
			<div class="flex items-center justify-between">
				<div>
					<p class="text-sm font-medium">标签种类</p>
					<p class="text-xs text-muted-foreground">每个标签都需要名称和颜色</p>
				</div>
				<Button type="button" variant="outline" onclick={addLabel}>
					<svg class="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
					</svg>
					新增标签
				</Button>
			</div>

			<div class="space-y-4 max-h-[55vh] overflow-y-auto pr-1">
				{#each labels as label, index (index)}
					<div class="grid gap-3 rounded-lg border p-4 md:grid-cols-[1fr_140px_40px] md:items-center">
						<div class="space-y-2">
							<label class="text-xs text-muted-foreground" for={`label-name-${index}`}>名称</label>
							<Input
								id={`label-name-${index}`}
								value={label.name}
								oninput={(event) => updateLabel(index, 'name', event.currentTarget.value)}
								placeholder="例如：目标/背景"
							/>
						</div>
						<div class="space-y-2">
							<label class="text-xs text-muted-foreground" for={`label-color-${index}`}>颜色</label>
							<input
								type="color"
								id={`label-color-${index}`}
								value={label.color}
								onchange={(event) => updateLabel(index, 'color', event.currentTarget.value)}
								class="h-10 w-full cursor-pointer rounded-md border border-input bg-background"
							/>
						</div>
						<div class="flex items-end justify-end">
							<Button
								type="button"
								variant="ghost"
								size="icon"
								class="text-muted-foreground hover:text-destructive"
								onclick={() => removeLabel(index)}
								aria-label="移除"
							>
								<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
								</svg>
							</Button>
						</div>
					</div>
				{/each}
			</div>
		</div>

		<div class="flex justify-end gap-2">
			<Button type="button" variant="outline" onclick={handleClose}>取消</Button>
			<Button type="submit">{group ? '保存' : '创建'}</Button>
		</div>
	</form>
</Modal>
