<script lang="ts">
import PublicLayout from '$components/layout/PublicLayout.svelte';
import { Button } from '$components/ui/button';

const stats = [
	{ label: '光谱任务', value: '2.5M+', sub: '累计样本' },
	{ label: '实时推理', value: '36ms', sub: '平均延迟' },
	{ label: 'AI 协助', value: '98%', sub: '正确率' },
];

const features = [
	{
		title: '多模态协同',
		desc: '光谱 + RGB + 深度数据统一标注，跨通道一致性实时同步。',
		icon: 'M13 10V3L4 14h7v7l9-11h-7z',
	},
	{
		title: '云端加速',
		desc: '分布式缓存与 GPU 加速渲染，让 10GB 级 SPE 也能流畅预览。',
		icon: 'M12 8c-1.657 0-3 1.343-3 3m6 0a3 3 0 00-3-3m0 0V4m0 7a4 4 0 100 8 4 4 0 000-8z',
	},
	{
		title: '预设容器',
		desc: '标签/显示模式一键注入浏览器容器，支持二次微调与管理。',
		icon: 'M4 6h16M4 12h8m-8 6h16',
	},
];

const workflow = [
	{
		step: '01',
		title: '构建光谱仓库',
		desc: 'uploads/datasource 自动扫描，项目创建即同步样本。',
	},
	{
		step: '02',
		title: '在线任务协作',
		desc: '预设标签/显示模式接入工作面板，光谱曲线秒级渲染。',
	},
	{
		step: '03',
		title: '导出与追踪',
		desc: '结构化 JSON 按样本归档，便捷对接科研分析或模型训练。',
	},
];
</script>

<svelte:head>
	<title>北极星 · 专业光谱标注平台</title>
</svelte:head>

<PublicLayout>
	<section class="relative overflow-hidden bg-slate-950 text-white">
		<div class="orbit orbit-one"></div>
		<div class="orbit orbit-two"></div>
		<div class="shooting-star"></div>
		<div class="container mx-auto flex min-h-[80vh] flex-col items-center justify-center px-6 py-24 text-center">
			<p class="text-sm uppercase tracking-[0.4em] text-cyan-200">北 极 星 · POLARIS</p>
			<h1 class="mt-6 text-4xl font-black leading-tight sm:text-6xl">
				专业光谱标注平台
				<span class="block bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-600 bg-clip-text text-transparent">
					让科研工作流炫酷又高效
				</span>
			</h1>
			<p class="mx-auto mt-6 max-w-3xl text-lg text-slate-300">
				定制化的预设容器、实时光谱渲染与在线任务协作，让你的 hsi 标注体验如极光般流畅。
			</p>
			<div class="mt-10 flex flex-wrap items-center justify-center gap-4">
				<a href="/dashboard">
					<Button size="lg">进入控制台</Button>
				</a>
				<a href="/dashboard/online-tasks">
					<Button size="lg" variant="outline">立即体验标注</Button>
				</a>
			</div>
			<div class="mt-16 grid gap-6 sm:grid-cols-3">
				{#each stats as item}
					<div class="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur">
						<p class="text-3xl font-bold text-cyan-300 animate-pulse-slow">{item.value}</p>
						<p class="text-sm text-slate-200">{item.label}</p>
						<p class="text-xs text-slate-400">{item.sub}</p>
					</div>
				{/each}
			</div>
		</div>
	</section>

	<section class="container mx-auto px-6 py-20">
		<div class="mx-auto max-w-2xl text-center">
			<p class="text-sm font-semibold tracking-[0.3em] text-cyan-600">FEATURES</p>
			<h2 class="mt-3 text-3xl font-bold">聚焦真实光谱工作流</h2>
			<p class="mt-4 text-muted-foreground">
				以科研与工业数据为核心，北极星用轻量的界面承载复杂任务，为深度学习/遥感团队打造顺手的极客座舱。
			</p>
		</div>
		<div class="mt-12 grid gap-8 md:grid-cols-3">
			{#each features as feature}
				<div class="group relative overflow-hidden rounded-2xl border border-transparent bg-gradient-to-b from-slate-900 to-slate-800 p-6 text-white shadow-[0_20px_60px_rgba(15,23,42,0.4)] transition hover:-translate-y-2 hover:border-cyan-500">
					<div class="absolute inset-0 bg-gradient-to-r from-cyan-500/10 via-indigo-500/10 to-transparent opacity-0 blur-2xl transition group-hover:opacity-100"></div>
					<div class="flex h-12 w-12 items-center justify-center rounded-xl bg-white/10">
						<svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={feature.icon} />
						</svg>
					</div>
					<h3 class="mt-5 text-xl font-semibold">{feature.title}</h3>
					<p class="mt-3 text-sm text-slate-300">{feature.desc}</p>
				</div>
			{/each}
		</div>
	</section>

	<section class="bg-slate-900/60 py-20 text-white">
		<div class="container mx-auto px-6">
			<div class="flex flex-col gap-10 lg:flex-row lg:items-center">
				<div class="flex-1">
					<p class="text-sm uppercase tracking-[0.4em] text-cyan-400">WORKFLOW</p>
					<h2 class="mt-4 text-3xl font-bold">数据到标注的极速闭环</h2>
					<p class="mt-3 text-slate-300">
						全链路统一在一个平台中：样本扫描、容器选择、在线标注、导出与复盘。GPU 加速、现代浏览器渲染与结构化导出保证可控性与高颜值并存。
					</p>
				</div>
				<div class="flex-1 space-y-6">
					{#each workflow as step (step.step)}
						<div class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
							<div class="text-sm font-semibold text-cyan-300">{step.step}</div>
							<h3 class="mt-2 text-xl font-semibold">{step.title}</h3>
							<p class="text-sm text-slate-200">{step.desc}</p>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</section>

	<section class="container mx-auto px-6 py-20">
		<div class="grid gap-8 lg:grid-cols-2">
			<div class="rounded-3xl border border-slate-200 bg-white p-8 shadow-xl">
				<p class="text-sm uppercase tracking-[0.4em] text-slate-500">INSIGHT</p>
				<h3 class="mt-4 text-2xl font-bold">实时监控与导出沉淀</h3>
				<ul class="mt-6 space-y-4 text-sm text-slate-600">
					<li>· 仪表盘呈现项目进度，支持一键刷新。</li>
					<li>· 在线任务直接调用预设容器，切换样本时自动补齐缺失标签。</li>
					<li>· 项目导出 JSON 以样本为单位分组，便于训练管线消费。</li>
				</ul>
				<div class="mt-8 rounded-2xl bg-slate-900 p-6 text-white">
					<p class="text-xs uppercase tracking-[0.4em] text-cyan-400">数据快照</p>
					<p class="mt-4 text-4xl font-black text-cyan-300">7.3 TB</p>
					<p class="text-sm text-slate-200">当前在线样本存储</p>
				</div>
			</div>
			<div class="rounded-3xl border border-slate-200 bg-slate-50 p-8">
				<h3 class="text-2xl font-bold">准备好点亮下一段光谱征程了吗？</h3>
				<p class="mt-4 text-muted-foreground">
					北极星现已支持 env_ml、env_web、以及本地 backend 三大环境。用 docker cp 触达容器，设置 PYTHONPATH 即可串联科研项目。
				</p>
				<div class="mt-8 space-y-3 text-sm text-slate-600">
					<p>· env_ml：pytorch/pytorch:2.5.1-cuda12.1，端口 3000~3002</p>
					<p>· env_web：fastapi 轻量镜像，端口 3003~3005</p>
					<p>· backend：Python 3.10.19 (conda)，全套测试链</p>
				</div>
				<div class="mt-10 flex flex-wrap gap-4">
					<a href="/auth/login">
						<Button size="lg">立刻登录</Button>
					</a>
					<a href="/dashboard/projects">
						<Button size="lg" variant="outline">创建项目</Button>
					</a>
				</div>
			</div>
		</div>
	</section>
</PublicLayout>

<style>
:global(body) {
	background-color: #0f172a;
}

@keyframes orbitSpin {
	from {
		transform: rotate(0deg);
	}
	to {
		transform: rotate(360deg);
	}
}

@keyframes glowPulse {
	0% {
		opacity: 0.3;
	}
	50% {
		opacity: 0.8;
	}
	100% {
		opacity: 0.3;
	}
}

@keyframes shooting {
	0% {
		transform: translate(-10vw, -10vh);
		opacity: 0;
	}
	30% {
		opacity: 1;
	}
	70% {
		opacity: 1;
	}
	100% {
		transform: translate(60vw, 40vh);
		opacity: 0;
	}
}

.orbit {
	position: absolute;
	border-radius: 9999px;
	filter: blur(2px);
	opacity: 0.3;
	animation: orbitSpin 30s linear infinite;
}

.orbit-one {
	width: 40rem;
	height: 40rem;
	border: 1px solid rgba(59, 130, 246, 0.4);
	top: -10rem;
	right: -20rem;
}

.orbit-two {
	width: 26rem;
	height: 26rem;
	border: 1px solid rgba(165, 243, 252, 0.4);
	bottom: -8rem;
	left: -12rem;
	animation-duration: 22s;
}

.shooting-star {
	position: absolute;
	top: 20%;
	left: 5%;
	width: 1.5rem;
	height: 1.5rem;
	background: radial-gradient(circle, rgba(248, 250, 252, 0.9), transparent 70%);
	border-radius: 9999px;
	filter: blur(0.5px);
	animation: shooting 10s linear infinite;
}

.animate-pulse-slow {
	animation: glowPulse 4s ease-in-out infinite;
}
</style>
