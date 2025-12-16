<script lang="ts">
import { Badge } from '$components/ui/badge';
import { Button } from '$components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '$components/ui/card';
import { Checkbox } from '$components/ui/checkbox';
import TodoFormModal from '$components/biz/TodoFormModal.svelte';
import { Pagination } from '$components/ui/pagination';
import { Skeleton } from '$components/ui/skeleton';
import {
	createNewTodoApiV1TodosPost,
	deleteExistingTodoApiV1TodosTodoIdDelete,
	listTodosApiV1TodosGet,
	toggleTodoStatusApiV1TodosTodoIdTogglePost,
	updateExistingTodoApiV1TodosTodoIdPatch,
	type TodoResponse,
} from '$lib/api';
import { toasts } from '$lib/stores/ui';
import { extractApiError, unwrapOrThrow } from '$lib/utils/api';
import { onMount } from 'svelte';

let todos = $state<TodoResponse[]>([]);
let loading = $state(true);
let currentPage = $state(1);
let totalPages = $state(1);
let total = $state(0);
let filter = $state('');

// Modal state
let showModal = $state(false);
let editingTodo = $state<TodoResponse | null>(null);

const priorityColors: Record<number, 'secondary' | 'default' | 'destructive'> =
	{
		0: 'secondary',
		1: 'default',
		2: 'destructive',
	};

const priorityLabels: Record<number, string> = {
	0: '低',
	1: '中',
	2: '高',
};

onMount(() => {
	fetchTodos();
});

async function fetchTodos() {
	loading = true;
	try {
		const completed =
			filter === 'completed' ? true : filter === 'pending' ? false : undefined;
		const { data, error } = await listTodosApiV1TodosGet({
			query: {
				page: currentPage,
				page_size: 10,
				completed,
			},
		});

		if (data) {
			todos = data.items;
			total = data.total;
			totalPages = data.total_pages;
		} else if (error) {
			throw error;
		}
	} catch (error) {
		toasts.add({
			message: extractApiError(error, '获取待办事项失败'),
			type: 'error',
		});
	} finally {
		loading = false;
	}
}

function openCreateModal() {
	editingTodo = null;
	showModal = true;
}

function openEditModal(todo: TodoResponse) {
	editingTodo = todo;
	showModal = true;
}

type TodoFormPayload = {
	body: {
		title: string;
		description: string | null;
		priority: number;
	};
	todoId?: number;
};

async function handleSubmit(event: CustomEvent<TodoFormPayload>) {
	const { body, todoId } = event.detail;
	if (!body.title.trim()) {
		toasts.add({ message: '请输入标题', type: 'error' });
		return;
	}

	try {
		if (todoId) {
			const result = await updateExistingTodoApiV1TodosTodoIdPatch({
				path: { todo_id: todoId },
				body,
			});
			unwrapOrThrow(result, '更新失败');
			toasts.add({ message: '更新成功', type: 'success' });
		} else {
			const result = await createNewTodoApiV1TodosPost({
				body,
			});
			unwrapOrThrow(result, '创建失败');
			toasts.add({ message: '创建成功', type: 'success' });
		}
		showModal = false;
		editingTodo = null;
		fetchTodos();
	} catch (error) {
		toasts.add({ message: extractApiError(error, '操作失败'), type: 'error' });
	}
}

async function toggleTodo(todo: TodoResponse) {
	try {
		const result = await toggleTodoStatusApiV1TodosTodoIdTogglePost({
			path: { todo_id: todo.id },
		});
		const updated = unwrapOrThrow(result, '操作失败');
		todos = todos.map((item) => (item.id === updated.id ? updated : item));
	} catch (error) {
		toasts.add({ message: extractApiError(error, '操作失败'), type: 'error' });
	}
}

async function deleteTodo(todo: TodoResponse) {
	if (!confirm('确定要删除这个待办事项吗？')) return;

	try {
		const result = await deleteExistingTodoApiV1TodosTodoIdDelete({
			path: { todo_id: todo.id },
		});
		unwrapOrThrow(result, '删除失败');
		toasts.add({ message: '删除成功', type: 'success' });
		fetchTodos();
	} catch (error) {
		toasts.add({ message: extractApiError(error, '删除失败'), type: 'error' });
	}
}

function handlePageChange(event: CustomEvent<number>) {
	currentPage = event.detail;
	fetchTodos();
}

function handleFilterChange() {
	currentPage = 1;
	fetchTodos();
}

function handleClose() {
	showModal = false;
	editingTodo = null;
}

$effect(() => {
	if (!showModal) {
		editingTodo = null;
	}
});
</script>

<svelte:head>
	<title>待办事项 - MyApp</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-3xl font-bold">待办事项</h1>
			<p class="text-muted-foreground">管理待办事项</p>
		</div>
		<Button onclick={openCreateModal}>
			<svg class="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
			</svg>
			新建待办
		</Button>
	</div>

	<Card>
		<CardHeader>
			<div class="flex items-center justify-between">
				<CardTitle>任务列表 ({total})</CardTitle>
				<select
					bind:value={filter}
					onchange={handleFilterChange}
					class="rounded-md border border-input bg-background px-3 py-1 text-sm"
				>
					<option value="">全部</option>
					<option value="pending">未完成</option>
					<option value="completed">已完成</option>
				</select>
			</div>
		</CardHeader>
		<CardContent>
			{#if loading}
				<div class="space-y-3">
					{#each Array(5) as _}
						<div class="flex items-center gap-4 rounded-lg border p-4">
							<Skeleton class="h-4 w-4" />
							<Skeleton class="h-4 flex-1" />
							<Skeleton class="h-6 w-12" />
						</div>
					{/each}
				</div>
			{:else if todos.length === 0}
				<div class="py-12 text-center text-muted-foreground">
					<svg class="mx-auto h-12 w-12 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
					</svg>
					<p class="mt-4">暂无待办事项</p>
					<Button variant="outline" class="mt-4" onclick={openCreateModal}>创建第一个待办</Button>
				</div>
			{:else}
				<div class="space-y-2">
					{#each todos as todo (todo.id)}
						<div
							class="flex items-center gap-4 rounded-lg border p-4 transition-colors hover:bg-muted/50"
							class:opacity-60={todo.completed}
						>
							<Checkbox
								checked={todo.completed}
								onclick={() => toggleTodo(todo)}
							/>
							<div class="flex-1 min-w-0">
								<p class="font-medium" class:line-through={todo.completed}>
									{todo.title}
								</p>
							{#if todo.description}
									<p class="text-sm text-muted-foreground truncate">
										{todo.description}
									</p>
								{/if}
							</div>
							<Badge variant={priorityColors[todo.priority ?? 0]}>
								{priorityLabels[todo.priority ?? 0]}
							</Badge>
							<div class="flex gap-1">
								<Button variant="ghost" size="icon" onclick={() => openEditModal(todo)}>
									<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
									</svg>
								</Button>
								<Button variant="ghost" size="icon" onclick={() => deleteTodo(todo)}>
									<svg class="h-4 w-4 text-destructive" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
									</svg>
								</Button>
							</div>
						</div>
					{/each}
				</div>

				{#if totalPages > 1}
					<div class="mt-6 flex justify-center">
						<Pagination {currentPage} {totalPages} onchange={(page) => { currentPage = page; fetchTodos(); }} />
					</div>
				{/if}
			{/if}
		</CardContent>
	</Card>
</div>

<!-- Create/Edit Modal -->
<TodoFormModal
	bind:open={showModal}
	todo={editingTodo}
	on:submit={handleSubmit}
	on:close={handleClose}
/>
