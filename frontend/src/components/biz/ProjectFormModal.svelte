<script lang="ts">
import { Button } from '$components/ui/button';
import { Input } from '$components/ui/input';
import { Modal } from '$components/ui/modal';
import { Select } from '$components/ui/select';
import type { DataSourceUploadResponse, ProjectResponse } from '$lib/api';
import { uploadDataSourceFolderEndpointApiV1ProjectsDataSourcesUploadFolderPost } from '$lib/api';
import { toasts } from '$lib/stores/ui';
import { extractApiError } from '$lib/utils/api';
import { createEventDispatcher } from 'svelte';

type Option = { value: string; label: string };

type SubmitDetail = {
	body: {
		name: string;
		priority: 'normal' | 'high';
		completion_rate: number;
		available_samples: number;
		total_samples: number;
		data_source_folder?: string;
	};
	projectId?: number;
};

let {
	open = $bindable(false),
	project = null,
	dataSourceOptions = [],
}: {
	open?: boolean;
	project?: ProjectResponse | null;
	dataSourceOptions?: Option[];
} = $props();

const dispatch = createEventDispatcher<{
	close: void;
	submit: SubmitDetail;
	datasourceUploaded: { name: string };
}>();

const priorityOptions: Option[] = [
	{ value: 'normal', label: '普通优先级' },
	{ value: 'high', label: '高优先级' },
];

let name = $state('');
let priority = $state('normal');
let dataSourceFolder = $state('');
let uploading = $state(false);
const dataSourceInputRef: { current: HTMLInputElement | null } = { current: null };

function resetForm() {
	name = project?.name ?? '';
	priority = project?.priority ?? 'normal';
	dataSourceFolder = '';
}

$effect(() => {
	if (open) {
		resetForm();
	}
});

function handleSubmit(event: Event) {
	event.preventDefault();
	const body: SubmitDetail['body'] = {
		name: name.trim(),
		priority: (priority as 'normal' | 'high') ?? 'normal',
		completion_rate: project?.completion_rate ?? 0,
		available_samples: project?.available_samples ?? 0,
		total_samples: project?.total_samples ?? 0,
	};

	if (!project) {
		if (!dataSourceFolder) {
			toasts.add({ message: '请选择数据源', type: 'error' });
			return;
		}
		body.data_source_folder = dataSourceFolder;
	}

	dispatch('submit', { body, projectId: project?.id });
}

async function handleDataSourceUpload(event: Event) {
	const input = event.currentTarget as HTMLInputElement;
	const files = input.files;
	if (!files || files.length === 0) return;
	const first = files[0] as File & { webkitRelativePath?: string };
	const rootName = first.webkitRelativePath?.split('/')[0] || first.name;
	if (!rootName) {
		toasts.add({ message: '无法获取文件夹名称', type: 'error' });
		return;
	}
	uploading = true;
	try {
		const payload = {
			folder_name: rootName,
			files: [] as File[],
			relative_paths: [] as string[],
		};
		Array.from(files).forEach((file) => {
			const rel = (file as File & { webkitRelativePath?: string }).webkitRelativePath || file.name;
			payload.files.push(file);
			payload.relative_paths.push(rel);
		});
		const result = await uploadDataSourceFolderEndpointApiV1ProjectsDataSourcesUploadFolderPost({
			body: payload,
		});
		const data = result.data as DataSourceUploadResponse | undefined;
		if (!data) {
			throw result.error ?? new Error('上传失败');
		}
		dataSourceFolder = data.name;
		dispatch('datasourceUploaded', { name: data.name });
		toasts.add({ message: '数据源上传成功', type: 'success' });
		input.value = '';
	} catch (error) {
		toasts.add({ message: extractApiError(error, '上传失败'), type: 'error' });
	} finally {
		uploading = false;
	}
}

function handleClose() {
	dispatch('close');
}
</script>

<Modal bind:open title={project ? '编辑项目' : '新建项目'} onclose={handleClose} class="max-w-3xl">
	<form class="space-y-6" onsubmit={handleSubmit}>
		<div class="grid gap-4 md:grid-cols-2">
			<div class="space-y-2">
				<label class="text-sm font-medium" for="project-name">项目名称</label>
				<Input id="project-name" bind:value={name} placeholder="输入项目名称" />
			</div>
			<div class="space-y-2">
				<label class="text-sm font-medium" for="project-priority">优先级</label>
				<Select
					id="project-priority"
					bind:value={priority}
					options={priorityOptions}
				/>
			</div>
		</div>

		{#if project}
			<div class="grid gap-4 rounded-lg border p-4 text-sm text-muted-foreground md:grid-cols-2">
				<div>
					<p>创建时间：{new Date(project.created_at).toLocaleString()}</p>
				</div>
				<div>
					<p>总样本：{project.total_samples}</p>
					<p>可用样本：{project.available_samples}</p>
					<p>完成率：{(project.completion_rate ?? 0).toFixed(1)}%</p>
				</div>
			</div>
		{:else}
			<div class="space-y-2">
				<label class="text-sm font-medium" for="data-source">数据源</label>
					<Select
						id="data-source"
						bind:value={dataSourceFolder}
						options={dataSourceOptions}
						allowEmpty={false}
						placeholder="请选择已有数据源"
				/>
				<p class="text-xs text-muted-foreground">
					选择已有数据源或直接上传一个文件夹（会完整保留目录层级，支持 PNG/JPEG 以及 HDR/SPE/figspec*）。
				</p>
				<div class="flex items-center gap-3">
					<input
						type="file"
						class="hidden"
						webkitdirectory
						multiple
						bind:this={dataSourceInputRef.current}
						onchange={handleDataSourceUpload}
					/>
					<Button
						type="button"
						variant="outline"
						disabled={uploading}
						onclick={() => dataSourceInputRef.current?.click()}
					>
						{uploading ? '上传中…' : '上传数据源'}
					</Button>
					{#if dataSourceFolder}
						<span class="text-xs text-muted-foreground">已选择：{dataSourceFolder}</span>
					{/if}
				</div>
			</div>
		{/if}

		<div class="flex justify-end gap-2">
			<Button type="button" variant="outline" onclick={handleClose}>取消</Button>
			<Button type="submit">{project ? '保存' : '创建'}</Button>
		</div>
	</form>
</Modal>
