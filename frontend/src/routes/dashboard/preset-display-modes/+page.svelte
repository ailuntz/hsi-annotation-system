<script lang="ts">
import SpectralModeFormModal from '$components/biz/SpectralModeFormModal.svelte';
import { Button } from '$components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '$components/ui/card';
import { Input } from '$components/ui/input';
import { Pagination } from '$components/ui/pagination';
import { Skeleton } from '$components/ui/skeleton';
import {
	createSpectralModeEndpointApiV1SpectralModesPost,
	deleteSpectralModeEndpointApiV1SpectralModesModeIdDelete,
	listSpectralModesEndpointApiV1SpectralModesGet,
	updateSpectralModeEndpointApiV1SpectralModesModeIdPatch,
	type SpectralModeResponse,
} from '$lib/api';
import { toasts } from '$lib/stores/ui';
import { extractApiError, unwrapOrThrow } from '$lib/utils/api';
import { onMount } from 'svelte';

const pageSize = 6;

type ModeFormPayload = {
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

let modes = $state<SpectralModeResponse[]>([]);
let loading = $state(true);
let currentPage = $state(1);
let totalPages = $state(1);
let total = $state(0);
let searchTerm = $state('');
let modalOpen = $state(false);
let editingMode = $state<SpectralModeResponse | null>(null);

onMount(() => {
	fetchModes();
});

async function fetchModes() {
	loading = true;
	try {
		const { data, error } = await listSpectralModesEndpointApiV1SpectralModesGet({
			query: {
				page: currentPage,
				page_size: pageSize,
				search: searchTerm.trim() || undefined,
			},
		});
		if (data) {
			modes = data.items;
			total = data.total;
			totalPages = data.total_pages;
		} else if (error) {
			throw error;
		}
	} catch (error) {
		toasts.add({
			message: extractApiError(error, '获取显示模式失败'),
			type: 'error',
		});
	} finally {
		loading = false;
	}
}

function openCreateModal() {
	editingMode = null;
	modalOpen = true;
}

function openEditModal(mode: SpectralModeResponse) {
	editingMode = mode;
	modalOpen = true;
}

function handleModalClose() {
	modalOpen = false;
	editingMode = null;
}

function validatePayload(body: ModeFormPayload['body']) {
	const channels = [body.r_channel, body.g_channel, body.b_channel];
	const gains = [body.r_gain, body.g_gain, body.b_gain];
	if (!body.name.trim()) {
		throw new Error('请输入模式名称');
	}
	if (channels.some((value) => value < 0)) {
		throw new Error('通道号必须为非负整数');
	}
	if (gains.some((value) => value < -4096 || value > 4096)) {
		throw new Error('增益范围需在 -4096 至 4096 之间');
	}
}

async function handleSubmit(event: CustomEvent<ModeFormPayload>) {
	const { body, modeId } = event.detail;
	try {
		validatePayload(body);
		if (modeId) {
			const result = await updateSpectralModeEndpointApiV1SpectralModesModeIdPatch({
				path: { mode_id: modeId },
				body,
			});
			unwrapOrThrow(result, '更新失败');
			toasts.add({ message: '更新成功', type: 'success' });
		} else {
			const result = await createSpectralModeEndpointApiV1SpectralModesPost({
				body,
			});
			unwrapOrThrow(result, '创建失败');
			toasts.add({ message: '创建成功', type: 'success' });
		}
		modalOpen = false;
		editingMode = null;
		fetchModes();
	} catch (error) {
		toasts.add({ message: extractApiError(error, '保存失败'), type: 'error' });
	}
}

async function handleDelete(mode: SpectralModeResponse) {
	if (!confirm(`确定删除「${mode.name}」吗？`)) return;
	try {
		const result = await deleteSpectralModeEndpointApiV1SpectralModesModeIdDelete({
			path: { mode_id: mode.id },
		});
		unwrapOrThrow(result, '删除失败');
		toasts.add({ message: '已删除', type: 'success' });
		fetchModes();
	} catch (error) {
		toasts.add({ message: extractApiError(error, '删除失败'), type: 'error' });
	}
}

function handlePageChange(page: number) {
	currentPage = page;
	fetchModes();
}

function handleSearch(event: Event) {
	event.preventDefault();
	currentPage = 1;
	fetchModes();
}

function formatDate(value: string) {
	const date = new Date(value);
	if (Number.isNaN(date.getTime())) return '';
	return date.toLocaleString('zh-CN', { hour12: false });
}
</script>

<svelte:head>
	<title>预设显示模式 - HSI Annotation</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex flex-wrap items-center justify-between gap-4">
		<div>
			<h1 class="text-3xl font-bold">预设显示模式</h1>
			<p class="text-muted-foreground">保存常用通道 / 增益组合，快速切换显示模式</p>
		</div>
		<Button onclick={openCreateModal}>
			<svg class="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
			</svg>
			新建显示模式
		</Button>
	</div>

	<Card>
		<CardHeader class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
			<CardTitle>模式列表 ({total})</CardTitle>
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
								<Skeleton class="h-6 w-44" />
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
			{:else if modes.length === 0}
				<div class="flex flex-col items-center justify-center gap-3 py-10 text-center text-muted-foreground">
					<svg class="h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
					</svg>
					<p>暂时没有光谱显示模式，点击右上角按钮新建</p>
				</div>
			{:else}
				<div class="grid gap-4 md:grid-cols-2">
					{#each modes as mode (mode.id)}
						<Card class="flex flex-col justify-between">
							<CardHeader class="space-y-2">
								<div class="flex items-start justify-between gap-4">
									<div>
										<CardTitle class="text-xl">{mode.name}</CardTitle>
										<p class="text-sm text-muted-foreground">
											更新于 {formatDate(mode.updated_at)}
										</p>
									</div>
									<div class="flex gap-2">
										<Button variant="ghost" size="icon" onclick={() => openEditModal(mode)} aria-label="编辑">
											<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 4H6a2 2 0 00-2 2v12a2 2 0 002 2h12a2 2 0 002-2v-5M18.5 2.5a2.121 2.121 0 113 3L12 15l-4 1 1-4L18.5 2.5z" />
											</svg>
										</Button>
										<Button
											variant="ghost"
											size="icon"
											class="text-destructive hover:text-destructive"
											onclick={() => handleDelete(mode)}
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
								<div class="space-y-2 text-sm">
									<div class="flex flex-wrap gap-2">
										<span class="rounded-md bg-muted px-2 py-1">R 通道 {mode.r_channel}</span>
										<span class="rounded-md bg-muted px-2 py-1">G 通道 {mode.g_channel}</span>
										<span class="rounded-md bg-muted px-2 py-1">B 通道 {mode.b_channel}</span>
									</div>
									<div class="flex flex-wrap gap-2">
										<span class="rounded-md bg-muted px-2 py-1">R 增益 {mode.r_gain}</span>
										<span class="rounded-md bg-muted px-2 py-1">G 增益 {mode.g_gain}</span>
										<span class="rounded-md bg-muted px-2 py-1">B 增益 {mode.b_gain}</span>
									</div>
									<div class="flex flex-wrap gap-2">
										<span class="rounded-md bg-muted px-2 py-1">算法 {mode.gain_algorithm}</span>
										{#if mode.dark_calibration}
											<span class="rounded-md bg-amber-100 px-2 py-1 text-amber-900">暗场校准</span>
										{/if}
										{#if mode.white_calibration}
											<span class="rounded-md bg-blue-100 px-2 py-1 text-blue-900">白板校准</span>
										{/if}
									</div>
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

<SpectralModeFormModal
	bind:open={modalOpen}
	mode={editingMode}
	on:submit={handleSubmit}
	on:close={handleModalClose}
/>
