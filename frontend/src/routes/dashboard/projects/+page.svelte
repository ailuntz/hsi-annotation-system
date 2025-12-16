<script lang="ts">
import { browser } from '$app/environment';
import ProjectExportModal, { type ProjectExportSelections } from '$components/biz/ProjectExportModal.svelte';
import ProjectFormModal from '$components/biz/ProjectFormModal.svelte';
import { Badge } from '$components/ui/badge';
import { Button } from '$components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '$components/ui/card';
import { Input } from '$components/ui/input';
import { Pagination } from '$components/ui/pagination';
import { Skeleton } from '$components/ui/skeleton';
import {
	archiveProjectEndpointApiV1ProjectsProjectIdArchivePost,
	createProjectEndpointApiV1ProjectsPost,
	deleteProjectEndpointApiV1ProjectsProjectIdDelete,
	listDataSourcesEndpointApiV1ProjectsDataSourcesGet,
	listProjectsEndpointApiV1ProjectsGet,
	restoreProjectEndpointApiV1ProjectsProjectIdRestorePost,
	updateProjectEndpointApiV1ProjectsProjectIdPatch,
	type ProjectCreate,
	type ProjectResponse,
} from '$lib/api';
import { toasts } from '$lib/stores/ui';
import { extractApiError, unwrapOrThrow } from '$lib/utils/api';
import { onMount } from 'svelte';

type ProjectFormPayload = {
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

const pageSize = 6;
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

let projects = $state<ProjectResponse[]>([]);
let loading = $state(true);
let currentPage = $state(1);
let totalPages = $state(1);
let total = $state(0);
let searchTerm = $state('');
let showArchived = $state(false);

let modalOpen = $state(false);
let editingProject = $state<ProjectResponse | null>(null);
let dataSourceOptions = $state<{ value: string; label: string }[]>([]);
let exportModalOpen = $state(false);
let exportingProject = $state<ProjectResponse | null>(null);

onMount(() => {
	fetchDataSources();
	fetchProjects();
});

async function fetchDataSources() {
	try {
		const { data, error } = await listDataSourcesEndpointApiV1ProjectsDataSourcesGet();
		if (data) {
			dataSourceOptions = data.map((item) => ({
				value: item.name,
				label: `${item.name} (${item.total_samples} 样本)`,
			}));
		} else if (error) {
			throw error;
		}
	} catch (error) {
		toasts.add({ message: extractApiError(error, '获取数据源失败'), type: 'error' });
	}
}

async function fetchProjects() {
	loading = true;
	try {
		const { data, error } = await listProjectsEndpointApiV1ProjectsGet({
			query: {
				page: currentPage,
				page_size: pageSize,
				search: searchTerm.trim() || undefined,
				archived: showArchived ? true : false,
			},
		});
		if (data) {
			projects = data.items;
			total = data.total;
			totalPages = data.total_pages;
		} else if (error) {
			throw error;
		}
	} catch (error) {
		toasts.add({ message: extractApiError(error, '获取项目失败'), type: 'error' });
	} finally {
		loading = false;
	}
}

function openCreateModal() {
	editingProject = null;
	modalOpen = true;
}

function openEditModal(project: ProjectResponse) {
	editingProject = project;
	modalOpen = true;
}

function handleModalClose() {
	modalOpen = false;
	editingProject = null;
}

function validatePayload(body: ProjectFormPayload['body']) {
	if (!body.name.trim()) {
		throw new Error('请输入项目名称');
	}
}

async function handleSubmit(event: CustomEvent<ProjectFormPayload>) {
	const { body, projectId } = event.detail;
	try {
		validatePayload(body);
		if (projectId) {
			const result = await updateProjectEndpointApiV1ProjectsProjectIdPatch({
				path: { project_id: projectId },
				body,
			});
			unwrapOrThrow(result, '更新失败');
			toasts.add({ message: '项目更新成功', type: 'success' });
		} else {
			if (!body.data_source_folder) {
				throw new Error('缺少数据源');
			}
			const createBody: ProjectCreate = {
				name: body.name,
				priority: body.priority,
				completion_rate: body.completion_rate,
				available_samples: body.available_samples,
				total_samples: body.total_samples,
				data_source_folder: body.data_source_folder,
			};
			const result = await createProjectEndpointApiV1ProjectsPost({ body: createBody });
			unwrapOrThrow(result, '创建失败');
			toasts.add({ message: '项目创建成功', type: 'success' });
			fetchDataSources();
		}
		modalOpen = false;
		editingProject = null;
		fetchProjects();
	} catch (error) {
		toasts.add({ message: extractApiError(error, '保存失败'), type: 'error' });
	}
}

function handleDataSourceUploaded() {
	fetchDataSources();
}

async function handleArchive(project: ProjectResponse) {
	try {
		const result = project.is_archived
			? await restoreProjectEndpointApiV1ProjectsProjectIdRestorePost({
					path: { project_id: project.id },
			  })
			: await archiveProjectEndpointApiV1ProjectsProjectIdArchivePost({
					path: { project_id: project.id },
			  });
		unwrapOrThrow(result, '操作失败');
		toasts.add({ message: project.is_archived ? '已恢复' : '已归档', type: 'success' });
		fetchProjects();
	} catch (error) {
		toasts.add({ message: extractApiError(error, '操作失败'), type: 'error' });
	}
}

async function handleDelete(project: ProjectResponse) {
	if (!confirm(`确定删除项目「${project.name}」？该操作不可恢复。`)) return;
	try {
		const result = await deleteProjectEndpointApiV1ProjectsProjectIdDelete({
			path: { project_id: project.id },
		});
		unwrapOrThrow(result, '删除失败');
		toasts.add({ message: '已删除项目', type: 'success' });
		fetchProjects();
	} catch (error) {
		toasts.add({ message: extractApiError(error, '删除失败'), type: 'error' });
	}
}

function handleExport(project: ProjectResponse) {
	exportingProject = project;
	exportModalOpen = true;
}

function handleExportClose() {
	exportModalOpen = false;
	exportingProject = null;
}

function sanitizeFilename(name: string) {
	return name.replace(/[\\/:*?"<>|]/g, '_') || 'project';
}

function downloadJson(data: unknown, filename: string) {
	const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
	const url = URL.createObjectURL(blob);
	const link = document.createElement('a');
	link.href = url;
	link.download = filename;
	link.click();
	URL.revokeObjectURL(url);
}

async function requestProjectExport(projectId: number, selections: ProjectExportSelections) {
	const endpoint = `${API_BASE_URL}/api/v1/projects/${projectId}/export`;
	const headers: Record<string, string> = {
		'Content-Type': 'application/json',
	};
	if (browser) {
		const token = localStorage.getItem('access_token');
		if (token) {
			headers.Authorization = `Bearer ${token}`;
		}
	}
	const response = await fetch(endpoint, {
		method: 'POST',
		headers,
		body: JSON.stringify({
			include_project_meta: selections.includeProjectMeta,
			include_sample_meta: selections.includeSampleMeta,
			include_annotation_bundle: selections.includeAnnotationBundle,
		}),
	});
	if (!response.ok) {
		let detail = '导出失败';
		try {
			const errorPayload = await response.json();
			if (typeof errorPayload?.detail === 'string') {
				detail = errorPayload.detail;
			}
		} catch {
			// ignore parse error
		}
		throw new Error(detail);
	}
	return response.json();
}

async function handleExportConfirm(event: CustomEvent<{ selections: ProjectExportSelections }>) {
	if (!exportingProject) return;
	try {
		const payload = await requestProjectExport(exportingProject.id, event.detail.selections);
		const filename = `${sanitizeFilename(exportingProject.name)}-annotations.json`;
		downloadJson(payload, filename);
		toasts.add({ message: '已导出 JSON', type: 'success' });
		handleExportClose();
	} catch (error) {
		toasts.add({ message: extractApiError(error, '导出失败'), type: 'error' });
	}
}

function handlePageChange(page: number) {
	currentPage = page;
	fetchProjects();
}

function handleSearch(event: Event) {
	event.preventDefault();
	currentPage = 1;
	fetchProjects();
}

function toggleArchived(next: boolean) {
	showArchived = next;
	currentPage = 1;
	fetchProjects();
}

function completionClass(rate: number) {
	return rate >= 100 ? 'text-green-600' : 'text-muted-foreground';
}

function priorityVariant(priority: string) {
	return priority === 'high' ? 'destructive' : 'secondary';
}
</script>

<svelte:head>
	<title>在线项目 - HSI Annotation</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex flex-wrap items-center justify-between gap-4">
		<div>
			<h1 class="text-3xl font-bold">在线项目</h1>
			<p class="text-muted-foreground">管理标注项目，快速查看进度与归档状态</p>
		</div>
		<Button onclick={openCreateModal}>
			<svg class="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
			</svg>
			新建项目
		</Button>
	</div>

	<div class="flex flex-wrap items-center gap-3">
		<div class="inline-flex rounded-md border p-1">
			<button
				class={`rounded-md px-3 py-1 text-sm ${!showArchived ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'}`}
				onclick={() => toggleArchived(false)}
				type="button"
			>
				活跃项目
			</button>
			<button
				class={`rounded-md px-3 py-1 text-sm ${showArchived ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'}`}
				onclick={() => toggleArchived(true)}
				type="button"
			>
				已归档
			</button>
		</div>

		<form class="flex w-full gap-3 md:w-auto" onsubmit={handleSearch}>
			<Input
				type="search"
				placeholder="搜索项目名称"
				bind:value={searchTerm}
				class="md:w-64"
			/>
			<Button type="submit" variant="outline">
				<svg class="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z" />
				</svg>
				搜索
			</Button>
		</form>
	</div>

	<Card>
		<CardHeader>
			<CardTitle>{showArchived ? '已归档项目' : '活跃项目'} ({total})</CardTitle>
		</CardHeader>
		<CardContent class="space-y-6">
			{#if loading}
				<div class="grid gap-4 md:grid-cols-2">
					{#each Array(4) as _, index (index)}
						<Card>
							<CardHeader>
								<Skeleton class="h-6 w-40" />
							</CardHeader>
							<CardContent>
								<div class="space-y-2">
									<Skeleton class="h-4 w-full" />
									<Skeleton class="h-4 w-3/4" />
								</div>
							</CardContent>
						</Card>
					{/each}
				</div>
			{:else if projects.length === 0}
				<div class="flex flex-col items-center justify-center gap-3 py-10 text-center text-muted-foreground">
					<svg class="h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v8m4-4H8" />
					</svg>
					<p>暂无{showArchived ? '归档' : '活跃'}项目，点击右上角按钮开始创建</p>
				</div>
			{:else}
				<div class="grid gap-4 md:grid-cols-2">
					{#each projects as project (project.id)}
						<Card class="flex flex-col justify-between">
							<CardHeader class="space-y-3">
								<div class="flex items-start justify-between gap-4">
									<div>
										<CardTitle class="text-xl">{project.name}</CardTitle>
										<p class="text-xs text-muted-foreground">
											更新于 {new Date(project.updated_at).toLocaleString('zh-CN', { hour12: false })}
										</p>
									</div>
									<Badge variant={priorityVariant(project.priority ?? 'normal')}>
										{project.priority === 'high' ? '高优先级' : '普通优先级'}
									</Badge>
								</div>
								<div class="flex flex-wrap items-center gap-3 text-sm">
									{#if project.completion_rate !== undefined}
										<span class={`text-lg font-semibold ${completionClass(project.completion_rate)}`}>
											完成率 {project.completion_rate.toFixed(1)}%
										</span>
									{:else}
										<span class={`text-lg font-semibold ${completionClass(0)}`}>
											完成率 0.0%
										</span>
									{/if}
									<span class="text-muted-foreground">
										可用样本 {project.available_samples ?? 0} / 总样本 {project.total_samples ?? 0}
									</span>
								</div>
							</CardHeader>
							<CardContent class="space-y-4">
								<div class="grid gap-3 text-sm text-muted-foreground">
									<div class="flex items-center gap-2">
										<span class="w-20 text-xs uppercase tracking-wide text-muted-foreground">样本统计</span>
										<span>{project.available_samples}/{project.total_samples}</span>
									</div>
									<div class="flex items-center gap-2">
										<span class="w-20 text-xs uppercase tracking-wide text-muted-foreground">状态</span>
										<span>{project.is_archived ? '已归档' : '活跃'}</span>
									</div>
								</div>
								<div class="flex flex-wrap gap-2">
									<Button variant="outline" size="sm" onclick={() => openEditModal(project)}>
										编辑
									</Button>
									<Button
										variant="outline"
										size="sm"
										onclick={() => handleArchive(project)}
									>
										{project.is_archived ? '取消归档' : '归档'}
									</Button>
									<Button variant="outline" size="sm" onclick={() => handleExport(project)}>
										导出
									</Button>
									<Button
										variant="destructive"
										size="sm"
										onclick={() => handleDelete(project)}
									>
										删除
									</Button>
								</div>
							</CardContent>
						</Card>
					{/each}
				</div>
				{#if totalPages > 1}
					<div class="flex justify-end">
						<Pagination bind:currentPage={currentPage} {totalPages} onchange={handlePageChange} />
					</div>
				{/if}
			{/if}
		</CardContent>
	</Card>
</div>

<ProjectFormModal
	bind:open={modalOpen}
	project={editingProject}
	dataSourceOptions={dataSourceOptions}
	on:submit={handleSubmit}
	on:close={handleModalClose}
	on:datasourceUploaded={handleDataSourceUploaded}
/>

<ProjectExportModal
	bind:open={exportModalOpen}
	project={exportingProject}
	on:close={handleExportClose}
	on:confirm={handleExportConfirm}
/>
