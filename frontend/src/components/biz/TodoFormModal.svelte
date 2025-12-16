<script lang="ts">
import { Button } from '$components/ui/button';
import { Input } from '$components/ui/input';
import { Modal } from '$components/ui/modal';
import { Select } from '$components/ui/select';
import type { TodoResponse } from '$lib/api';
import { createEventDispatcher } from 'svelte';

type TodoFormBody = {
	title: string;
	description: string | null;
	priority: number;
};

type SubmitDetail = {
	body: TodoFormBody;
	todoId?: number;
};

const priorityOptions = [
	{ value: '0', label: '低优先级' },
	{ value: '1', label: '中优先级' },
	{ value: '2', label: '高优先级' },
];

let { open = $bindable(false), todo = null } = $props<{
	open?: boolean;
	todo?: TodoResponse | null;
}>();

const dispatch = createEventDispatcher<{
	close: void;
	submit: SubmitDetail;
}>();

let title = $state('');
let description = $state('');
let priority = $state('0');

$effect(() => {
	if (open) {
		title = todo?.title ?? '';
		description = todo?.description ?? '';
		priority = (todo?.priority ?? 0).toString();
	}
});

function handleSubmit(event: Event) {
	event.preventDefault();
	const body: TodoFormBody = {
		title: title.trim(),
		description: description.trim() ? description : null,
		priority: Number.parseInt(priority, 10) || 0,
	};
	dispatch('submit', { body, todoId: todo?.id });
}

function handleClose() {
	dispatch('close');
}
</script>

<Modal bind:open title={todo ? '编辑待办' : '新建待办'}>
	<form onsubmit={handleSubmit} class="space-y-4">
		<div class="space-y-2">
			<label for="title" class="text-sm font-medium">标题</label>
			<Input id="title" bind:value={title} placeholder="输入待办事项标题" />
		</div>

		<div class="space-y-2">
			<label for="description" class="text-sm font-medium">描述（可选）</label>
			<textarea
				id="description"
				bind:value={description}
				placeholder="输入详细描述"
				rows="3"
				class="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
			></textarea>
		</div>

		<div class="space-y-2">
			<label for="priority" class="text-sm font-medium">优先级</label>
			<Select id="priority" bind:value={priority} options={priorityOptions} />
		</div>

		<div class="flex justify-end gap-2 pt-4">
			<Button variant="outline" type="button" onclick={handleClose}>
				取消
			</Button>
			<Button type="submit">
				{todo ? '保存' : '创建'}
			</Button>
		</div>
	</form>
</Modal>
