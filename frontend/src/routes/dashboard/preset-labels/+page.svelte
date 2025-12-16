<script lang="ts">
import LabelGroupFormModal from '$components/biz/LabelGroupFormModal.svelte';
import { Button } from '$components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '$components/ui/card';
import { Input } from '$components/ui/input';
import { Pagination } from '$components/ui/pagination';
import { Skeleton } from '$components/ui/skeleton';
import {
	createLabelGroupEndpointApiV1LabelGroupsPost,
	deleteLabelGroupEndpointApiV1LabelGroupsGroupIdDelete,
	listLabelGroupsEndpointApiV1LabelGroupsGet,
	updateLabelGroupEndpointApiV1LabelGroupsGroupIdPatch,
	type LabelGroupResponse,
} from '$lib/api';
import { toasts } from '$lib/stores/ui';
import { extractApiError, unwrapOrThrow } from '$lib/utils/api';
import { onMount } from 'svelte';

const pageSize = 6;

type GroupFormPayload = {
	body: {
		name: string;
		labels: { name: string; color: string; order_index: number | null }[];
	};
	groupId?: number;
};

let groups = $state<LabelGroupResponse[]>([]);
let loading = $state(true);
let currentPage = $state(1);
let totalPages = $state(1);
let total = $state(0);
let searchTerm = $state('');
let modalOpen = $state(false);
let editingGroup = $state<LabelGroupResponse | null>(null);

onMount(() => {
	fetchGroups();
});

async function fetchGroups() {
	loading = true;
	try {
		const { data, error } = await listLabelGroupsEndpointApiV1LabelGroupsGet({
			query: {
				page: currentPage,
				page_size: pageSize,
				search: searchTerm.trim() || undefined,
			},
		});
		if (data) {
			groups = data.items;
			total = data.total;
			totalPages = data.total_pages;
		} else if (error) {
			throw error;
		}
	} catch (error) {
		toasts.add({
			message: extractApiError(error, '获取标签组失败'),
			type: 'error',
		});
	} finally {
		loading = false;
	}
}

function openCreateModal() {
	editingGroup = null;
	modalOpen = true;
}

function openEditModal(group: LabelGroupResponse) {
	editingGroup = group;
	modalOpen = true;
}

function handleModalClose() {
	modalOpen = false;
	editingGroup = null;
}

async function handleSubmit(event: CustomEvent<GroupFormPayload>) {
	const { body, groupId } = event.detail;
	const trimmedName = body.name.trim();
	if (!trimmedName) {
		toasts.add({ message: '请输入标签组名称', type: 'error' });
		return;
	}

	const cleanedLabels = body.labels
		.map((label, idx) => ({
			name: label.name.trim(),
			color: label.color || '#FF0000',
			order_index: idx,
		}))
		.filter((label) => label.name.length > 0);

	if (cleanedLabels.length === 0) {
		toasts.add({ message: '至少需要一个标签种类', type: 'error' });
		return;
	}

	try {
		if (groupId) {
			const result = await updateLabelGroupEndpointApiV1LabelGroupsGroupIdPatch({
				path: { group_id: groupId },
				body: {
					name: trimmedName,
					labels: cleanedLabels,
				},
			});
			unwrapOrThrow(result, '更新失败');
			toasts.add({ message: '更新成功', type: 'success' });
		} else {
			const result = await createLabelGroupEndpointApiV1LabelGroupsPost({
				body: {
					name: trimmedName,
					labels: cleanedLabels,
				},
			});
			unwrapOrThrow(result, '创建失败');
			toasts.add({ message: '创建成功', type: 'success' });
		}
		modalOpen = false;
		editingGroup = null;
		fetchGroups();
	} catch (error) {
		toasts.add({ message: extractApiError(error, '保存失败'), type: 'error' });
	}
}

async function handleDelete(group: LabelGroupResponse) {
	if (!confirm(`确定删除「${group.name}」吗？`)) return;
	try {
		const result = await deleteLabelGroupEndpointApiV1LabelGroupsGroupIdDelete({
			path: { group_id: group.id },
		});
		unwrapOrThrow(result, '删除失败');
		toasts.add({ message: '已删除', type: 'success' });
		fetchGroups();
	} catch (error) {
		toasts.add({ message: extractApiError(error, '删除失败'), type: 'error' });
	}
}

function handlePageChange(page: number) {
	currentPage = page;
	fetchGroups();
}

function handleSearch(event: Event) {
	event.preventDefault();
	currentPage = 1;
	fetchGroups();
}

function getContrast(color: string) {
	const hex = color.replace('#', '');
	if (hex.length !== 6) return '#111827';
	const r = Number.parseInt(hex.slice(0, 2), 16);
	const g = Number.parseInt(hex.slice(2, 4), 16);
	const b = Number.parseInt(hex.slice(4, 6), 16);
	const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
	return luminance > 0.6 ? '#111827' : '#ffffff';
}

function formatDate(value: string) {
	const date = new Date(value);
	if (Number.isNaN(date.getTime())) return '';
	return date.toLocaleString('zh-CN', { hour12: false });
}
</script>

<svelte:head>
	<title>预设标注组 - HSI Annotation</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex flex-wrap items-center justify-between gap-4">
		<div>
			<h1 class="text-3xl font-bold">预设标注组</h1>
			<p class="text-muted-foreground">统一维护标签预设，保持不同标注任务的一致性</p>
		</div>
		<Button onclick={openCreateModal}>
			<svg class="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
			</svg>
			新建标签组
		</Button>
	</div>

	<Card>
		<CardHeader class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
			<CardTitle>标签组列表 ({total})</CardTitle>
			<form class="flex w-full gap-3 md:w-auto" onsubmit={handleSearch}>
				<Input
					type="search"
					placeholder="按名称搜索"
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
			{:else if groups.length === 0}
				<div class="flex flex-col items-center justify-center gap-3 py-10 text-center text-muted-foreground">
					<svg class="h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2a2 2 0 012-2h2a2 2 0 012 2v2m1 4H8a2 2 0 01-2-2V7a2 2 0 012-2h3l2-2h4a2 2 0 012 2v4" />
					</svg>
					<p>暂时没有标签组，点击右上角按钮新建</p>
				</div>
			{:else}
				<div class="grid gap-4 md:grid-cols-2">
					{#each groups as group (group.id)}
						<Card class="flex flex-col justify-between">
							<CardHeader class="space-y-2">
								<div class="flex items-start justify-between gap-4">
									<div>
										<CardTitle class="text-xl">{group.name}</CardTitle>
										<p class="text-sm text-muted-foreground">
											{group.labels.length} 个标签 · 更新于 {formatDate(group.updated_at)}
										</p>
									</div>
									<div class="flex gap-2">
										<Button variant="ghost" size="icon" onclick={() => openEditModal(group)} aria-label="编辑">
											<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 4H6a2 2 0 00-2 2v12a2 2 0 002 2h12a2 2 0 002-2v-5M18.5 2.5a2.121 2.121 0 113 3L12 15l-4 1 1-4L18.5 2.5z" />
											</svg>
										</Button>
										<Button
											variant="ghost"
											size="icon"
											class="text-destructive hover:text-destructive"
											onclick={() => handleDelete(group)}
											aria-label="删除"
										>
											<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5-3h4a2 2 0 012 2v2H8V6a2 2 0 012-2z" />
											</svg>
										</Button>
									</div>
								</div>
							</CardHeader>
							<CardContent>
								<div class="flex flex-wrap gap-2">
									{#each group.labels as label (label.id)}
										<span
											class="rounded-full px-3 py-1 text-xs font-medium shadow-sm"
											style={`background-color:${label.color};color:${getContrast(label.color)};`}
										>
											{label.name}
										</span>
									{/each}
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

<LabelGroupFormModal
	bind:open={modalOpen}
	group={editingGroup}
	on:submit={handleSubmit}
	on:close={handleModalClose}
/>
