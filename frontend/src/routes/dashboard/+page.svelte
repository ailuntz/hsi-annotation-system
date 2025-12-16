<script lang="ts">
import { goto } from '$app/navigation';
import { Button } from '$components/ui/button';
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '$components/ui/card';
import { Skeleton } from '$components/ui/skeleton';
import {
	listDataSourcesEndpointApiV1ProjectsDataSourcesGet,
	listLabelGroupsEndpointApiV1LabelGroupsGet,
	listProjectsEndpointApiV1ProjectsGet,
	listSpectralModesEndpointApiV1SpectralModesGet,
	readCurrentUserApiV1UsersMeGet,
	type DataSourceInfo,
	type ProjectResponse,
} from '$lib/api';
import { toasts } from '$lib/stores/ui';
import { extractApiError } from '$lib/utils/api';
import { auth, currentUser, isLoading } from '$lib/stores/auth';
import { onMount } from 'svelte';

type MetricState = {
	activeProjects: number;
	archivedProjects: number;
	totalSamples: number;
	pendingSamples: number;
	annotatedEstimate: number;
	avgCompletion: number;
};

const MAX_PROJECT_FETCH = 100;

let dashboardLoading = $state(true);
let metrics = $state<MetricState>({
	activeProjects: 0,
	archivedProjects: 0,
	totalSamples: 0,
	pendingSamples: 0,
	annotatedEstimate: 0,
	avgCompletion: 0,
});
let topProjects = $state<ProjectResponse[]>([]);
let dataSources = $state<DataSourceInfo[]>([]);
let labelGroupCount = $state(0);
let spectralModeCount = $state(0);

const quickLinks = [
	{
		label: '管理项目',
		description: '创建或编辑标注项目',
		href: '/dashboard/projects',
	},
	{
		label: '在线任务',
		description: '进入标注工作台',
		href: '/dashboard/online-tasks',
	},
	{
		label: '预置标签组',
		description: '维护标签模板',
		href: '/dashboard/preset-labels',
	},
	{
		label: '预置显示模式',
		description: '配置光谱显示方案',
		href: '/dashboard/preset-display-modes',
	},
];

onMount(async () => {
	const token = auth.initialize();
	if (token && !$currentUser) {
		await fetchUserProfile();
	} else {
		auth.setLoading(false);
	}
	fetchDashboardData();
});

async function fetchUserProfile() {
	try {
		const { data, error } = await readCurrentUserApiV1UsersMeGet();
		if (data) {
			auth.setUser(data);
		} else if (error) {
			auth.logout();
		}
	} catch (error) {
		console.error('获取用户信息失败', error);
	} finally {
		auth.setLoading(false);
	}
}

async function fetchDashboardData() {
	dashboardLoading = true;
	try {
		const [activeRes, archivedRes, labelsRes, modesRes, dsRes] = await Promise.all([
			listProjectsEndpointApiV1ProjectsGet({
				query: { page: 1, page_size: MAX_PROJECT_FETCH, archived: false },
			}),
			listProjectsEndpointApiV1ProjectsGet({
				query: { page: 1, page_size: MAX_PROJECT_FETCH, archived: true },
			}),
			listLabelGroupsEndpointApiV1LabelGroupsGet(),
			listSpectralModesEndpointApiV1SpectralModesGet(),
			listDataSourcesEndpointApiV1ProjectsDataSourcesGet(),
		]);

		if (activeRes.error) throw activeRes.error;
		if (archivedRes.error) throw archivedRes.error;

		const activeItems = activeRes.data?.items ?? [];
		const archivedTotal = archivedRes.data?.total ?? 0;
		const totalSamples = activeItems.reduce((sum, item) => sum + (item.total_samples ?? 0), 0);
		const pendingSamples = activeItems.reduce(
			(sum, item) => sum + (item.available_samples ?? 0),
			0,
		);
		const annotatedEstimate = activeItems.reduce((sum, item) => {
			const rate = item.completion_rate ?? 0;
			const total = item.total_samples ?? 0;
			return sum + Math.round((rate / 100) * total);
		}, 0);
		const avgCompletion =
			activeItems.length === 0
				? 0
				: activeItems.reduce((sum, item) => sum + (item.completion_rate ?? 0), 0) /
				  activeItems.length;

		metrics = {
			activeProjects: activeRes.data?.total ?? 0,
			archivedProjects: archivedTotal,
			totalSamples,
			pendingSamples,
			annotatedEstimate,
			avgCompletion,
		};

		topProjects = activeItems
			.slice()
			.sort((a, b) => (b.completion_rate ?? 0) - (a.completion_rate ?? 0))
			.slice(0, 5);

		labelGroupCount = labelsRes.data?.items?.length ?? 0;
		spectralModeCount = modesRes.data?.items?.length ?? 0;
		dataSources = dsRes.data ?? [];
	} catch (error) {
		toasts.add({ message: extractApiError(error, '获取仪表盘数据失败'), type: 'error' });
	} finally {
		dashboardLoading = false;
	}
}

function formatNumber(value: number) {
	return value.toLocaleString('zh-CN');
}

function formatPercent(value: number) {
	return `${value.toFixed(1)}%`;
}
</script>

<svelte:head>
	<title>仪表盘 - HSI Annotation</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex flex-wrap items-center justify-between gap-4">
		<div>
			<h1 class="text-3xl font-bold">仪表盘</h1>
			<p class="text-muted-foreground">
				欢迎回来，{$currentUser?.full_name || $currentUser?.email || '标注同学'}
			</p>
		</div>
		<Button variant="outline" onclick={fetchDashboardData} disabled={dashboardLoading}>
			{dashboardLoading ? '加载中...' : '刷新数据'}
		</Button>
	</div>

	<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
		{#if $isLoading || dashboardLoading}
			{#each Array(4) as _, index (index)}
				<Card>
					<CardHeader class="pb-2">
						<Skeleton class="h-4 w-28" />
					</CardHeader>
					<CardContent>
						<Skeleton class="h-8 w-20" />
						<Skeleton class="mt-3 h-2 w-full" />
					</CardContent>
				</Card>
			{/each}
		{:else}
			<Card>
				<CardHeader class="pb-2">
					<CardDescription>活跃项目</CardDescription>
				</CardHeader>
				<CardContent>
					<div class="text-3xl font-bold">{formatNumber(metrics.activeProjects)}</div>
					<p class="text-xs text-muted-foreground mt-2">正在进行的项目数量</p>
				</CardContent>
			</Card>
			<Card>
				<CardHeader class="pb-2">
					<CardDescription>已归档</CardDescription>
				</CardHeader>
				<CardContent>
					<div class="text-3xl font-bold">{formatNumber(metrics.archivedProjects)}</div>
					<p class="text-xs text-muted-foreground mt-2">历史项目沉淀</p>
				</CardContent>
			</Card>
			<Card>
				<CardHeader class="pb-2">
					<CardDescription>待标注样本</CardDescription>
				</CardHeader>
				<CardContent>
					<div class="text-3xl font-bold">{formatNumber(metrics.pendingSamples)}</div>
					<p class="text-xs text-muted-foreground mt-2">
						覆盖 {formatNumber(metrics.totalSamples)} 个总样本
					</p>
				</CardContent>
			</Card>
			<Card>
				<CardHeader class="pb-2">
					<CardDescription>平均完成率</CardDescription>
				</CardHeader>
				<CardContent>
					<div class="text-3xl font-bold">{formatPercent(metrics.avgCompletion)}</div>
					<p class="text-xs text-muted-foreground mt-2">
						约 {formatNumber(metrics.annotatedEstimate)} 条标注已完成
					</p>
				</CardContent>
			</Card>
		{/if}
	</div>

	<div class="grid gap-4 lg:grid-cols-3">
		<Card class="lg:col-span-2">
			<CardHeader>
				<CardTitle>项目进度</CardTitle>
				<CardDescription>近期待办与高优项目优先显示</CardDescription>
			</CardHeader>
			<CardContent>
				{#if dashboardLoading}
					<div class="space-y-3">
						{#each Array(4) as _, index (index)}
							<div class="space-y-2 rounded-lg border p-3">
								<Skeleton class="h-4 w-32" />
								<Skeleton class="h-2 w-full" />
							</div>
						{/each}
					</div>
				{:else if topProjects.length === 0}
					<div class="py-10 text-center text-sm text-muted-foreground">
						暂无活跃项目，先去创建一个吧。
					</div>
				{:else}
					<div class="space-y-4">
						{#each topProjects as project (project.id)}
							<div class="rounded-xl border p-4">
								<div class="flex flex-wrap items-center justify-between gap-3">
									<div>
										<p class="text-base font-semibold">{project.name}</p>
										<p class="text-xs text-muted-foreground">
											可用样本 {project.available_samples ?? 0} / {project.total_samples ?? 0}
										</p>
									</div>
									<div class="text-sm text-muted-foreground">
										优先级：{project.priority === 'high' ? '高' : '普通'}
									</div>
								</div>
								<div class="mt-3">
									<div class="flex items-center justify-between text-xs text-muted-foreground">
										<span>完成率</span>
										<span>{project.completion_rate?.toFixed(1) ?? '0.0'}%</span>
									</div>
									<div class="mt-1 h-2 w-full rounded-full bg-muted">
										<div
											class="h-2 rounded-full bg-primary transition-all"
											style={`width: ${Math.min(project.completion_rate ?? 0, 100)}%`}
										></div>
									</div>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</CardContent>
		</Card>

		<Card>
			<CardHeader>
				<CardTitle>资源概览</CardTitle>
				<CardDescription>快速了解模版与数据源</CardDescription>
			</CardHeader>
			<CardContent class="space-y-5">
				<div class="rounded-lg border p-4">
					<p class="text-sm text-muted-foreground">标签组</p>
					<p class="text-2xl font-semibold mt-1">{labelGroupCount}</p>
					<p class="text-xs text-muted-foreground mt-1">预置标签模板</p>
				</div>
				<div class="rounded-lg border p-4">
					<p class="text-sm text-muted-foreground">显示模式</p>
					<p class="text-2xl font-semibold mt-1">{spectralModeCount}</p>
					<p class="text-xs text-muted-foreground mt-1">光谱显示方案</p>
				</div>
				<div>
					<p class="text-sm font-medium mb-2">数据源</p>
					{#if dataSources.length === 0}
						<p class="text-xs text-muted-foreground">暂无上传数据集</p>
					{:else}
						<ul class="space-y-2 text-sm">
							{#each dataSources.slice(0, 3) as source}
								<li class="rounded-lg border p-3">
									<div class="flex items-center justify-between">
										<span class="font-medium">{source.name}</span>
										<span class="text-xs text-muted-foreground">{source.total_samples} 样本</span>
									</div>
									<p class="text-xs text-muted-foreground mt-1">
										{source.total_files} 个文件
									</p>
								</li>
							{/each}
						</ul>
					{/if}
				</div>
			</CardContent>
		</Card>
	</div>

	<div class="grid gap-4 lg:grid-cols-3">
		<Card class="lg:col-span-2">
			<CardHeader>
				<CardTitle>常用入口</CardTitle>
				<CardDescription>覆盖项目、标注与配置</CardDescription>
			</CardHeader>
			<CardContent class="grid gap-4 md:grid-cols-2">
				{#each quickLinks as link}
					<div class="rounded-xl border p-4">
						<p class="font-semibold">{link.label}</p>
						<p class="text-sm text-muted-foreground mt-1">{link.description}</p>
						<Button class="mt-3 w-full" variant="secondary" onclick={() => goto(link.href)}>
							前往
						</Button>
					</div>
				{/each}
			</CardContent>
		</Card>

		<Card>
			<CardHeader>
				<CardTitle>系统说明</CardTitle>
				<CardDescription>保持优秀的标注节奏</CardDescription>
			</CardHeader>
			<CardContent class="space-y-3 text-sm text-muted-foreground">
				<p>· 优先处理高优项目，保证关键样本及时完成</p>
				<p>· 标签组与显示模式可提前预设，进入任务后直接复用</p>
				<p>· 数据源上传支持整包拖拽，统一在项目中选择</p>
				<p>· 导出项目可获取完整 JSON，方便备份与分析</p>
			</CardContent>
		</Card>
	</div>
</div>
