<script lang="ts">
import { Button } from '$components/ui/button';
import { Checkbox } from '$components/ui/checkbox';
import { Modal } from '$components/ui/modal';
import type { ProjectResponse } from '$lib/api';
import { createEventDispatcher } from 'svelte';

export type ProjectExportSelections = {
	includeProjectMeta: boolean;
	includeSampleMeta: boolean;
	includeAnnotationBundle: boolean;
};

let {
	open = $bindable(false),
	project = null,
}: {
	open?: boolean;
	project?: ProjectResponse | null;
} = $props();

const dispatch = createEventDispatcher<{
	close: void;
	confirm: { selections: ProjectExportSelections };
}>();

let includeProjectMeta = $state(true);
let includeSampleMeta = $state(true);
let includeAnnotationBundle = $state(true);

function resetSelections() {
	includeProjectMeta = true;
	includeSampleMeta = true;
	includeAnnotationBundle = true;
}

$effect(() => {
	if (open) {
		resetSelections();
	}
});

function handleClose() {
	dispatch('close');
}

function handleConfirm() {
	const selections: ProjectExportSelections = {
		includeProjectMeta,
		includeSampleMeta,
		includeAnnotationBundle,
	};
	dispatch('confirm', { selections });
}
</script>

<Modal
	bind:open
	title="导出项目标注"
	onclose={handleClose}
	class="max-w-xl"
>
	{#if project}
		<div class="space-y-5">
			<div class="rounded-lg border p-4 text-sm">
				<p class="font-semibold">{project.name}</p>
				<p class="text-xs text-muted-foreground">项目 ID：{project.project_id}</p>
			</div>

			<div class="space-y-4">
				<section class="rounded-lg border p-4">
					<div class="flex items-center justify-between gap-3">
						<div>
							<p class="font-medium">项目基本信息</p>
							<p class="text-xs text-muted-foreground">包含名称、优先级、完成率、创建/更新时间</p>
						</div>
						<Checkbox bind:checked={includeProjectMeta} />
					</div>
				</section>

				<section class="rounded-lg border p-4 space-y-2">
					<div class="flex items-center justify-between gap-3">
						<div>
							<p class="font-medium">样本基本信息</p>
							<p class="text-xs text-muted-foreground">sample_id、类型、文件列表等</p>
						</div>
						<Checkbox bind:checked={includeSampleMeta} />
					</div>
					<p class="text-xs text-muted-foreground">
						固定包含字段：status / is_annotated / last_annotated_by
					</p>
				</section>

				<section class="rounded-lg border p-4">
					<div class="flex items-center justify-between gap-3">
						<div>
							<p class="font-medium">标注详情</p>
							<p class="text-xs text-muted-foreground">annotation_detail + annotation_detail_mode + annotation_spectrum</p>
						</div>
						<Checkbox bind:checked={includeAnnotationBundle} />
					</div>
				</section>
			</div>

			<div class="flex justify-end gap-2">
				<Button type="button" variant="outline" onclick={handleClose}>
					取消
				</Button>
				<Button type="button" onclick={handleConfirm}>
					导出 JSON
				</Button>
			</div>
		</div>
	{:else}
		<div class="text-center text-sm text-muted-foreground">
			请选择项目后再导出
		</div>
	{/if}
</Modal>
