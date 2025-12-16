<script lang="ts">
import { Button } from '$components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '$components/ui/card';
import { Input } from '$components/ui/input';
import CanvasSelect from 'canvas-select';
import { onMount } from 'svelte';
import HSIRenderer from '$lib/hsi/HSIRenderer.js';
import HSIParser from '$lib/hsi/HSIParser.js';
import SpectrumExtractor from '$lib/hsi/SpectrumExtractor.js';
import SpectrumChart from '$lib/hsi/SpectrumChart.js';
import {
	listProjectsEndpointApiV1ProjectsGet,
	listProjectSamplesEndpointApiV1ProjectsProjectIdSamplesGet,
	getSampleDetailEndpointApiV1SamplesSampleIdGet,
	getSampleAssetEndpointApiV1SamplesSampleIdAssetsGet,
	replaceSampleAnnotationsEndpointApiV1SamplesSampleIdAnnotationsPut,
	updateSampleStatusEndpointApiV1SamplesSampleIdPatch,
	listLabelGroupsEndpointApiV1LabelGroupsGet,
	listSpectralModesEndpointApiV1SpectralModesGet,
	type AnnotationDetailCreate,
	type AnnotationDetailResponse,
	type AnnotationSampleDetail,
	type AnnotationSampleSummary,
	type LabelGroupResponse,
	type ProjectResponse,
	type SpectralModeResponse,
} from '$lib/api';
import { toasts } from '$lib/stores/ui';
import { extractApiError, unwrapOrThrow } from '$lib/utils/api';

type TaskType = 'online' | 'offline';
type ActiveLabel = { name: string; color: string };
type DisplayModeConfig = {
	name: string;
	r_channel: number;
	g_channel: number;
	b_channel: number;
	r_gain: number;
	g_gain: number;
	b_gain: number;
	gain_algorithm: SpectralModeResponse['gain_algorithm'];
	dark_calibration?: boolean;
	white_calibration?: boolean;
};

type FixedPreferences = {
	tagFontSize: number;
	tagBackgroundColor: string;
	backgroundRecent: string[];
	tagTextColorOnlineMode: 'follow' | 'custom';
	tagTextColorOnlineCustom: string;
	tagTextColorOffline: string;
	lockCanvas: boolean;
	hideLabels: boolean;
	labelAbove: boolean;
	borderWidth: number;
	controlPointSize: number;
};

const FIXED_PREF_KEY = 'hsi-fixed-preferences';
const IMAGE_EXTS = ['.png', '.jpg', '.jpeg'];
const HDR_EXT = '.hdr';
const SPE_EXT = '.spe';
const DARK_EXT = '.figspecblack';
const WHITE_EXT = '.figspecwhite';
const DEFAULT_LABEL_COLOR = '#ff4d4f';
const DEFAULT_FILL_ALPHA = 0.2;
const TOOL_TYPE_TO_CANVAS: Record<string, number> = {
	rect: 1,
	polygon: 2,
	point: 3,
	line: 4,
	circle: 5,
	grid: 6,
};
const CANVAS_TYPE_TO_TOOL: Record<number, string> = {
	1: 'rect',
	2: 'polygon',
	3: 'point',
	4: 'line',
	5: 'circle',
	6: 'grid',
};
const TOOL_OPTIONS = [
	{ label: '选择', type: 0 },
	{ label: '矩形', type: 1 },
	{ label: '多边形', type: 2 },
	{ label: '点', type: 3 },
		// { label: '折线', type: 4 },
	{ label: '圆', type: 5 },
];
const EMPTY_IMAGE_DATA_URL = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=';
const CHANNEL_FIELDS: Array<{ label: string; key: 'r_channel' | 'g_channel' | 'b_channel' }> = [
	{ label: 'R Channel', key: 'r_channel' },
	{ label: 'G Channel', key: 'g_channel' },
	{ label: 'B Channel', key: 'b_channel' },
];
const GAIN_FIELDS: Array<{ label: string; key: 'r_gain' | 'g_gain' | 'b_gain' }> = [
	{ label: 'R Gain', key: 'r_gain' },
	{ label: 'G Gain', key: 'g_gain' },
	{ label: 'B Gain', key: 'b_gain' },
];

let projects = $state<ProjectResponse[]>([]);
let selectedProjectId = $state<number | null>(null);
let samples = $state<AnnotationSampleSummary[]>([]);
let selectedSampleId = $state<number | null>(null);
let sampleDetail = $state<AnnotationSampleDetail | null>(null);
let loadingProjects = $state(true);
let loadingSamples = $state(false);
let loadingSampleDetail = $state(false);
let savingAnnotations = $state(false);
let markingIgnored = $state(false);

let labelGroups = $state<LabelGroupResponse[]>([]);
let labelPresetSelection = $state<string>('');
let labelPresetApplied = $state(false);
let selectedLabelName = $state<string>('');
let selectedLabelColor = $state<string>(DEFAULT_LABEL_COLOR);
let activeLabels = $state<ActiveLabel[]>([]);
let newLabelName = $state('');

let spectralModes = $state<SpectralModeResponse[]>([]);
let spectralPresetSelection = $state<string>('');
let spectralPresetApplied = $state(false);
let channelOptions = $state<Array<{ value: number; label: string }>>([]);
let spectralDataReady = $state(false);
let applyDarkCalibration = $state(false);
let applyWhiteCalibration = $state(false);
let activeDisplayMode = $state<DisplayModeConfig>({
	name: '自定义模式',
	r_channel: 0,
	g_channel: 0,
	b_channel: 0,
	r_gain: 0,
	g_gain: 0,
	b_gain: 0,
	gain_algorithm: 'linear',
});

let previewTaskType = $state<TaskType>('online');
let smoothingLevel = $state(0);
let annotationDirty = $state(false);
let activeTool = $state<number>(0);
let currentAnnotationCount = $state(0);
let canPersistAnnotations = $state(false);
let selectedDetailId = $state<string | null>(null);
let showAllSpectra = $state(false);
let currentSpectrumView: { mode: 'single' | 'multi'; data: any } | null = null;
let spectrumViewVersion = $state(0);
let anchorPicking = $state(false);

function getRandomColor() {
	const toHex = (value: number) => value.toString(16).padStart(2, '0');
	const r = Math.floor(Math.random() * 256);
	const g = Math.floor(Math.random() * 256);
	const b = Math.floor(Math.random() * 256);
	return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

function setActiveLabels(labels: ActiveLabel[]) {
	activeLabels = labels.map((label) => ({ ...label }));
	if (selectedLabelName && !activeLabels.some((item) => item.name === selectedLabelName)) {
		applySelectedLabel('');
	}
}

function channelLabelFor(value: number | null | undefined) {
	if (!Number.isFinite(value ?? NaN)) return '';
	const option = channelOptions.find((item) => item.value === Number(value));
	return option?.label ?? '';
}

function applyPresetDisplayMode(mode: SpectralModeResponse | null | undefined) {
	if (!mode) return;
	activeDisplayMode.name = mode.name ?? '预设模式';
	activeDisplayMode.r_channel = Number(mode.r_channel ?? 0);
	activeDisplayMode.g_channel = Number(mode.g_channel ?? 0);
	activeDisplayMode.b_channel = Number(mode.b_channel ?? 0);
	activeDisplayMode.r_gain = Number(mode.r_gain ?? 0);
	activeDisplayMode.g_gain = Number(mode.g_gain ?? 0);
	activeDisplayMode.b_gain = Number(mode.b_gain ?? 0);
	activeDisplayMode.gain_algorithm = (mode.gain_algorithm ??
		'linear') as DisplayModeConfig['gain_algorithm'];
	applyDarkCalibration = Boolean(mode.dark_calibration);
	applyWhiteCalibration = Boolean(mode.white_calibration);
	normalizeDisplayChannels();
	parser?.applyCalibration(applyDarkCalibration, applyWhiteCalibration);
	spectralPresetApplied = true;
}

let annotationCanvas: HTMLCanvasElement | null = null;
let spectrumCanvas: HTMLCanvasElement | null = null;
let canvasSelect: any = null;
let renderer: any = null;
let parser: any = null;
let spectrumExtractor: any = null;
let spectrumChart: any = null;
let preferences = $state<FixedPreferences | null>(null);
let cursorPosition = $state<[number, number]>([0, 0]);
let zoomRatio = $state(1);
let currentModeMemo: DisplayModeConfig | null = null;
let currentImageObjectUrl: string | null = null;

function sanitizeFilename(input: string) {
	return input.replace(/[\\/:*?"<>|]/g, '_');
}

function getExtension(path: string) {
	const idx = path.lastIndexOf('.');
	return idx >= 0 ? path.slice(idx).toLowerCase() : '';
}

function hexToRgba(hex: string, alpha = 1) {
	let sanitized = hex.replace('#', '');
	if (sanitized.length === 3) {
		sanitized = sanitized
			.split('')
			.map((char) => char + char)
			.join('');
	}
	const bigint = parseInt(sanitized, 16);
	const r = (bigint >> 16) & 255;
	const g = (bigint >> 8) & 255;
	const b = bigint & 255;
	return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function toRgba(color: string, alpha = 1) {
	if (!color) return `rgba(147, 51, 234, ${alpha})`;
	if (color.startsWith('#')) {
		return hexToRgba(color, alpha);
	}
	if (color.startsWith('rgb(')) {
		return color.replace('rgb', 'rgba').replace(')', `, ${alpha})`);
	}
	if (color.startsWith('rgba(')) {
		return color.replace(/rgba\((.+),\s*[\d.]+\)/, `rgba($1, ${alpha})`);
	}
	return color;
}

function setCanvasDrawingStyles(color: string) {
	if (!canvasSelect) return;
	canvasSelect.strokeStyle = color;
	canvasSelect.fillStyle = toRgba(color, DEFAULT_FILL_ALPHA);
}

async function fetchSampleAsset(path: string, parseAs: 'blob' | 'text' = 'blob') {
	if (!sampleDetail) throw new Error('未选择样本');
	const result = await getSampleAssetEndpointApiV1SamplesSampleIdAssetsGet({
		path: { sample_id: sampleDetail.id },
		query: { path },
		parseAs,
	});
	return unwrapOrThrow(result, '文件下载失败');
}

async function fetchAssetAsText(path: string) {
	return (await fetchSampleAsset(path, 'text')) as string;
}

async function fetchAssetAsArrayBuffer(path: string) {
	const blob = (await fetchSampleAsset(path, 'blob')) as Blob;
	return blob.arrayBuffer();
}

async function fetchAssetAsBlob(path: string) {
	return (await fetchSampleAsset(path, 'blob')) as Blob;
}

function loadPreferencesFromStorage() {
	if (typeof window === 'undefined') return null;
	try {
		const raw = window.localStorage.getItem(FIXED_PREF_KEY);
		if (!raw) return null;
		const parsed = JSON.parse(raw);
		return parsed as FixedPreferences;
	} catch {
		return null;
	}
}

function applyPreferencesToCanvas(pref: FixedPreferences) {
	if (!canvasSelect) return;
	canvasSelect.labelFont = `${pref.tagFontSize}px sans-serif`;
	canvasSelect.labelFillStyle = pref.tagBackgroundColor === 'transparent' ? 'rgba(0,0,0,0.4)' : pref.tagBackgroundColor;
	canvasSelect.textFillStyle =
		previewTaskType === 'online' && pref.tagTextColorOnlineMode === 'follow'
			? canvasSelect.textFillStyle
			: previewTaskType === 'online'
				? pref.tagTextColorOnlineCustom
				: pref.tagTextColorOffline;
	canvasSelect.hideLabel = pref.hideLabels;
	canvasSelect.labelUp = pref.labelAbove;
	canvasSelect.lineWidth = pref.borderWidth;
	canvasSelect.ctrlRadius = pref.controlPointSize / 2;
}

function handlePreferenceChange(event: CustomEvent) {
	const detail = event.detail as FixedPreferences;
	preferences = detail;
	applyPreferencesToCanvas(detail);
}

async function fetchProjects() {
	loadingProjects = true;
	try {
		const result = await listProjectsEndpointApiV1ProjectsGet({
			query: { page: 1, page_size: 50, archived: false },
		});
		const data = unwrapOrThrow(result, '获取项目失败');
		projects = data.items;
		if (selectedProjectId && !projects.some((project) => project.id === selectedProjectId)) {
			selectedProjectId = null;
			clearSampleContext({ resetSamples: true });
		}
	} catch (error) {
		toasts.add({ message: extractApiError(error, '获取项目失败'), type: 'error' });
	} finally {
		loadingProjects = false;
	}
}

async function fetchSamples() {
	if (!selectedProjectId) {
		clearSampleContext({ resetSamples: true });
		return;
	}
	loadingSamples = true;
	try {
		const result = await listProjectSamplesEndpointApiV1ProjectsProjectIdSamplesGet({
			path: { project_id: selectedProjectId },
		});
		const data = unwrapOrThrow(result, '获取样本失败');
		samples = data.items;
		clearSampleContext();
	} catch (error) {
		toasts.add({ message: extractApiError(error, '获取样本失败'), type: 'error' });
	} finally {
		loadingSamples = false;
	}
}

async function selectSample(sampleId: number) {
	selectedSampleId = sampleId;
	await fetchSampleDetail();
}

function handleProjectChange(event: Event) {
	const target = event.currentTarget as HTMLSelectElement;
	const value = target.value;
	const nextId = value ? Number(value) : null;
	const parsed = Number.isFinite(nextId ?? NaN) ? nextId : null;
	if (selectedProjectId === parsed) return;
	selectedProjectId = parsed;
	clearSampleContext({ resetSamples: true });
	if (selectedProjectId) {
		void fetchSamples();
	}
}

async function fetchSampleDetail() {
	if (!selectedSampleId) return;
	const currentRequestId = selectedSampleId;
	loadingSampleDetail = true;
	try {
		const result = await getSampleDetailEndpointApiV1SamplesSampleIdGet({
			path: { sample_id: selectedSampleId },
		});
		const data = unwrapOrThrow(result, '获取样本详情失败');
		if (currentRequestId !== selectedSampleId) {
			return;
		}
		sampleDetail = data;
		ensureLabelsFromAnnotations(data.annotations);
		await loadSampleAssets();
		annotationDirty = false;
	} catch (error) {
		toasts.add({ message: extractApiError(error, '获取样本详情失败'), type: 'error' });
	} finally {
		loadingSampleDetail = false;
	}
}

async function fetchLabelGroups() {
	try {
		const result = await listLabelGroupsEndpointApiV1LabelGroupsGet({
			query: { page: 1, page_size: 100 },
		});
		const data = unwrapOrThrow(result, '获取标签组失败');
		labelGroups = data.items;
		labelPresetSelection = '';
		labelPresetApplied = activeLabels.length > 0;
	} catch (error) {
		toasts.add({ message: extractApiError(error, '获取标签组失败'), type: 'error' });
	}
}

async function fetchSpectralModes() {
	try {
		const result = await listSpectralModesEndpointApiV1SpectralModesGet({
			query: { page: 1, page_size: 100 },
		});
		const data = unwrapOrThrow(result, '获取显示模式失败');
		spectralModes = data.items;
		spectralPresetSelection = '';
		spectralPresetApplied = false;
	} catch (error) {
		toasts.add({ message: extractApiError(error, '获取显示模式失败'), type: 'error' });
	}
}

function loadPresetIntoActiveLabels(groupId: number | null) {
	if (!groupId) {
		setActiveLabels([]);
		labelPresetApplied = false;
		return;
	}
	const preset = labelGroups.find((group) => group.id === groupId);
	if (!preset) {
		setActiveLabels([]);
		labelPresetApplied = false;
		return;
	}
	const existingNames = new Set(activeLabels.map((item) => item.name));
	const baseCount = activeLabels.length;
	const additions = preset.labels
		.filter((label) => label.name && !existingNames.has(label.name))
		.map((label) => ({
			name: label.name,
			color: label.color,
		}));
	if (additions.length > 0) {
		setActiveLabels([...activeLabels, ...additions]);
	}
	labelPresetApplied = baseCount + additions.length > 0;
}

function ensureLabelsFromAnnotations(annotations: AnnotationSampleDetail['annotations'] | undefined | null) {
	if (!annotations || annotations.length === 0) return;
	const currentNames = new Set(activeLabels.map((item) => item.name));
	const additions: ActiveLabel[] = [];
	for (const detail of annotations) {
		const name = detail.label_name?.trim();
		if (!name || currentNames.has(name)) continue;
		currentNames.add(name);
		additions.push({
			name,
			color: detail.color || getRandomColor(),
		});
	}
	if (additions.length) {
		setActiveLabels([...activeLabels, ...additions]);
	}
}

function handleAddActiveLabel() {
	const trimmed = newLabelName.trim();
	if (!trimmed) {
		toasts.add({ message: '请输入标签名称', type: 'error' });
		return;
	}
	if (activeLabels.some((item) => item.name === trimmed)) {
		toasts.add({ message: '标签已存在', type: 'info' });
		newLabelName = '';
		return;
	}
	const next = [...activeLabels, { name: trimmed, color: getRandomColor() }];
	setActiveLabels(next);
	newLabelName = '';
}

function handleRemoveActiveLabel(name: string) {
	const filtered = activeLabels.filter((item) => item.name !== name);
	setActiveLabels(filtered);
}

function handleCalibrationToggle() {
	parser?.applyCalibration(applyDarkCalibration, applyWhiteCalibration);
	if (sampleDetail?.sample_type === 'hyperspectral' && spectralDataReady) {
		void renderCurrentSpectralMode();
	}
}

function findLabelInfo(label: string) {
	if (!label) return null;
	return activeLabels.find((item) => item.name === label) ?? null;
}

function applySelectedLabel(label: string) {
	selectedLabelName = label;
	const labelInfo = findLabelInfo(label);
	selectedLabelColor = labelInfo?.color ?? DEFAULT_LABEL_COLOR;
	setCanvasDrawingStyles(selectedLabelColor);
}

function handleLabelGroupChange(event: Event) {
	const target = event.currentTarget as HTMLSelectElement;
	const value = target.value;
	if (!value) {
		labelPresetSelection = '';
		return;
	}
	const nextId = Number(value);
	if (!Number.isFinite(nextId)) {
		labelPresetSelection = '';
		return;
	}
	loadPresetIntoActiveLabels(nextId);
	labelPresetSelection = '';
	applySelectedLabel('');
}

function handlePresetModeChange(event: Event) {
	const target = event.currentTarget as HTMLSelectElement;
	const value = target.value;
	if (!value) {
		spectralPresetSelection = '';
		return;
	}
	const nextId = Number(value);
	if (!Number.isFinite(nextId)) {
		spectralPresetSelection = '';
		return;
	}
	const preset = spectralModes.find((mode) => mode.id === nextId);
	if (preset) {
		applyPresetDisplayMode(preset);
	}
	spectralPresetSelection = '';
}

function formatCoordinatePreview(detail: AnnotationDetailResponse) {
	const raw = detail.coordinates?.coor ?? detail.coordinates ?? [];
	try {
		const serialized = JSON.stringify(raw);
		return serialized.length > 120 ? `${serialized.slice(0, 117)}...` : serialized;
	} catch {
		return '';
	}
}

function refreshAnnotationCount() {
	currentAnnotationCount = canvasSelect?.dataset?.length ?? 0;
}

function setSpectrumView(view: { mode: 'single' | 'multi'; data: any } | null) {
	currentSpectrumView = view;
	spectrumViewVersion += 1;
}

function disableAnchorPicking() {
	if (!anchorPicking) return;
	anchorPicking = false;
	if (canvasSelect) {
		canvasSelect.readonly = false;
	}
}

function clearSampleContext(options?: { resetSamples?: boolean }) {
	if (options?.resetSamples) {
		samples = [];
	}
	if (currentImageObjectUrl) {
		URL.revokeObjectURL(currentImageObjectUrl);
		currentImageObjectUrl = null;
	}
	selectedSampleId = null;
	sampleDetail = null;
	annotationDirty = false;
	showAllSpectra = false;
	disableAnchorPicking();
	spectralDataReady = false;
	setSpectrumView(null);
	spectrumChart?.clear();
	canvasSelect?.setData([]);
	if (canvasSelect) {
		canvasSelect.setImage(EMPTY_IMAGE_DATA_URL);
	}
	refreshAnnotationCount();
}

function canUseSpectrumTools() {
	return Boolean(sampleDetail && sampleDetail.sample_type === 'hyperspectral' && spectralDataReady);
}

function handleAnchorToggle() {
	if (!canUseSpectrumTools()) {
		toasts.add({ message: '当前样本不支持取点光谱', type: 'info' });
		return;
	}
	if (anchorPicking) {
		disableAnchorPicking();
		return;
	}
	anchorPicking = true;
	if (canvasSelect) {
		canvasSelect.readonly = true;
	}
	showAllSpectra = false;
}

function getImagePointFromEvent(event: MouseEvent): [number, number] | null {
	if (!canvasSelect) return null;
	const scale = canvasSelect.scale || 1;
	const originX = canvasSelect.originX || 0;
	const originY = canvasSelect.originY || 0;
	const offsetX = event.offsetX;
	const offsetY = event.offsetY;
	const x = Math.round((offsetX - originX) / scale);
	const y = Math.round((offsetY - originY) / scale);
	return [x, y];
}

async function captureSpectrumAtPoint(x: number, y: number) {
	if (!spectrumExtractor || !canUseSpectrumTools()) return false;
	const dims = parser?.getDimensions?.();
	if (!dims) return false;
	const width = dims.lines ?? 0;
	const height = dims.samples ?? 0;
	if (x < 0 || x >= width || y < 0 || y >= height) {
		toasts.add({ message: '点击位置超出影像范围', type: 'info' });
		return false;
	}
	try {
		const spectrum = await spectrumExtractor.getPointSpectrum(x, y);
		if (!spectrum) return false;
		const color = DEFAULT_LABEL_COLOR;
		showSingleSpectrum(spectrum.wavelengths, spectrum.values, `Point (${x}, ${y})`, color);
		toasts.add({ message: `已提取 (${x}, ${y}) 的光谱`, type: 'success' });
		return true;
	} catch (error) {
		toasts.add({ message: extractApiError(error, '取点光谱失败'), type: 'error' });
		return false;
	}
}

async function handleAnnotationCanvasClick(event: MouseEvent) {
	if (!anchorPicking) return;
	event.preventDefault();
	event.stopPropagation();
	const point = getImagePointFromEvent(event);
	if (!point) {
		disableAnchorPicking();
		return;
	}
	const [x, y] = point;
	await captureSpectrumAtPoint(x, y);
	disableAnchorPicking();
}

$effect(() => {
	spectrumViewVersion;
	smoothingLevel;
	if (!currentSpectrumView) return;
	renderCurrentSpectrum();
});

$effect(() => {
	const mode = activeDisplayMode;
	mode.r_channel;
	mode.g_channel;
	mode.b_channel;
	mode.r_gain;
	mode.g_gain;
	mode.b_gain;
	mode.gain_algorithm;
	if (sampleDetail?.sample_type === 'hyperspectral' && spectralDataReady) {
		void renderCurrentSpectralMode();
	}
});

function showSingleSpectrum(wavelengths: number[], values: number[], label: string, color: string) {
	setSpectrumView({
		mode: 'single',
		data: { wavelengths, values, label, color },
	});
}

function showSpectrumSeries(seriesList: Array<{ wavelengths: number[]; values: number[]; label: string; color: string }>) {
	setSpectrumView({
		mode: 'multi',
		data: seriesList,
	});
}

function renderCurrentSpectrum() {
	if (!spectrumChart || !currentSpectrumView) return;
	const windowSize = smoothingLevel > 0 ? smoothingLevel * 2 + 1 : 0;
	if (currentSpectrumView.mode === 'single') {
		const { wavelengths, values, label, color } = currentSpectrumView.data;
		const displayValues = windowSize ? spectrumChart.smoothData(values, windowSize) : values;
		const suffix = windowSize ? ` (S${smoothingLevel})` : '';
		const borderColor = toRgba(color, 1);
		const backgroundColor = toRgba(color, 0.15);
		spectrumChart.renderSpectrum(wavelengths, displayValues, label + suffix, borderColor, backgroundColor);
	} else {
		const datasets = currentSpectrumView.data.map(
			(series: { wavelengths: number[]; values: number[]; label: string; color: string }) => {
				const displayValues = windowSize ? spectrumChart.smoothData(series.values, windowSize) : series.values;
				return {
					wavelengths: series.wavelengths,
					values: displayValues,
					label: series.label + (windowSize ? ` (S${smoothingLevel})` : ''),
					color: toRgba(series.color, 1),
					backgroundColor: toRgba(series.color, 0.15),
				};
			},
		);
		spectrumChart.renderSeries(datasets);
	}
}

function focusDetailById(detailId: string | null) {
	if (!canvasSelect) return;
	canvasSelect.dataset?.forEach((shape: any) => {
		shape.active = detailId ? shape.uuid === detailId : false;
	});
	canvasSelect.update?.();
}

function extractSpectrumPoints(detail: AnnotationDetailResponse) {
	const points = detail.spectra?.[0]?.points ?? [];
	if (!points.length) return null;
	const wavelengths = points.map((point: any) => Number(point.wavelength ?? point.x ?? point[0] ?? 0));
	const values = points.map((point: any) => Number(point.intensity ?? point.y ?? point[1] ?? 0));
	return { wavelengths, values };
}

function renderSelectedDetailSpectrum() {
	if (!sampleDetail || !sampleDetail.annotations?.length) {
		setSpectrumView(null);
		spectrumChart?.clear();
		return;
	}
	const target =
		sampleDetail.annotations.find((detail) => detail.detail_id === selectedDetailId) ??
		sampleDetail.annotations[0];
	selectedDetailId = target?.detail_id ?? null;
	if (!target) {
		setSpectrumView(null);
		spectrumChart?.clear();
		return;
	}
	const spectrum = extractSpectrumPoints(target);
	if (!spectrum) {
		setSpectrumView(null);
		spectrumChart?.clear();
		return;
	}
	const color = target.color || DEFAULT_LABEL_COLOR;
	showSingleSpectrum(spectrum.wavelengths, spectrum.values, target.label_name || 'Spectrum', color);
}

function renderAllDetailSpectra() {
	if (!sampleDetail || !sampleDetail.annotations?.length) return false;
	const series = sampleDetail.annotations
		.map((detail) => {
			const spectrum = extractSpectrumPoints(detail);
			if (!spectrum) return null;
			return {
				wavelengths: spectrum.wavelengths,
				values: spectrum.values,
				label: detail.label_name || 'Spectrum',
				color: detail.color || DEFAULT_LABEL_COLOR,
			};
		})
		.filter(Boolean) as Array<{ wavelengths: number[]; values: number[]; label: string; color: string }>;

	if (!series.length) {
		toasts.add({ message: '没有可展示的光谱', type: 'info' });
		showAllSpectra = false;
		return false;
	}
	showSpectrumSeries(series);
	return true;
}

function syncSelectionAfterDataLoad() {
	const annotations = sampleDetail?.annotations ?? [];
	selectedDetailId = annotations.length ? annotations[annotations.length - 1]?.detail_id ?? null : null;
	focusDetailById(selectedDetailId);
	if (showAllSpectra) {
		renderAllDetailSpectra();
	} else {
		renderSelectedDetailSpectrum();
	}
}

function handleToggleAllSpectra() {
	if (showAllSpectra) {
		showAllSpectra = false;
		renderSelectedDetailSpectrum();
		return;
	}
	if (renderAllDetailSpectra()) {
		showAllSpectra = true;
	} else {
		showAllSpectra = false;
	}
}

function applyDetailModeSnapshot(snapshot: AnnotationDetailResponse['mode_snapshot']) {
	if (!snapshot) return;
	activeDisplayMode.r_channel = Number(snapshot.r_channel ?? 0);
	activeDisplayMode.g_channel = Number(snapshot.g_channel ?? 0);
	activeDisplayMode.b_channel = Number(snapshot.b_channel ?? 0);
	activeDisplayMode.r_gain = Number(snapshot.r_gain ?? 0);
	activeDisplayMode.g_gain = Number(snapshot.g_gain ?? 0);
	activeDisplayMode.b_gain = Number(snapshot.b_gain ?? 0);
	activeDisplayMode.gain_algorithm = (snapshot.gain_algorithm ??
		'linear') as DisplayModeConfig['gain_algorithm'];
	applyDarkCalibration = Boolean(snapshot.dark_calibration);
	applyWhiteCalibration = Boolean(snapshot.white_calibration);
	normalizeDisplayChannels();
	parser?.applyCalibration(applyDarkCalibration, applyWhiteCalibration);
	if (sampleDetail?.sample_type === 'hyperspectral') {
		void renderCurrentSpectralMode();
	}
}

function handleDetailSelect(detail: AnnotationDetailResponse) {
	selectedDetailId = detail.detail_id;
	showAllSpectra = false;
	applyDetailModeSnapshot(detail.mode_snapshot);
	focusDetailById(detail.detail_id);
	const spectrum = extractSpectrumPoints(detail);
	if (spectrum) {
		const color = detail.color || DEFAULT_LABEL_COLOR;
		showSingleSpectrum(spectrum.wavelengths, spectrum.values, detail.label_name || 'Spectrum', color);
	} else {
		setSpectrumView(null);
		spectrumChart?.clear();
	}
}

async function handleDeleteDetail(detail: AnnotationDetailResponse) {
	if (!canvasSelect || !sampleDetail || savingAnnotations) return;
	(canvasSelect as any)?.deleteByUuid?.(detail.detail_id);
	refreshAnnotationCount();
	selectedDetailId = sampleDetail.annotations?.find((item) => item.detail_id !== detail.detail_id)?.detail_id ?? null;
	await persistAnnotations('标注已删除');
}

function handleShapeAdded(shape: any) {
	const color = selectedLabelColor || DEFAULT_LABEL_COLOR;
	const label = selectedLabelName || '未命名';
	shape.label = label;
	shape.strokeStyle = color;
	shape.fillStyle = toRgba(color, DEFAULT_FILL_ALPHA);
	shape.color = color;
	annotationDirty = true;
	refreshAnnotationCount();
	selectedDetailId = shape.uuid ?? null;
	showAllSpectra = false;
	void renderSpectrumForShape(shape);
}

function handleShapeDeleted() {
	annotationDirty = true;
	refreshAnnotationCount();
	showAllSpectra = false;
}

$effect(() => {
	canPersistAnnotations =
		Boolean(sampleDetail) &&
		Boolean(selectedLabelName?.trim()) &&
		activeTool !== 0 &&
		currentAnnotationCount > 0 &&
		annotationDirty &&
		!savingAnnotations;
});

async function loadSampleAssets() {
	if (!sampleDetail || !canvasSelect) return;
	disableAnchorPicking();
	applyDarkCalibration = false;
	applyWhiteCalibration = false;
	channelOptions = [];
	spectralDataReady = false;
	canvasSelect.setData([]);
	refreshAnnotationCount();
	if (sampleDetail.sample_type === 'image') {
		const imageFile = sampleDetail.source_files.find((file) => IMAGE_EXTS.includes(getExtension(file)));
		if (!imageFile) {
			toasts.add({ message: '未找到图像文件', type: 'error' });
			return;
		}
		parser = null;
		spectrumExtractor = null;
		channelOptions = [];
		showAllSpectra = false;
		setSpectrumView(null);
		spectrumChart?.clear();
		if (currentImageObjectUrl) {
			URL.revokeObjectURL(currentImageObjectUrl);
			currentImageObjectUrl = null;
		}
		const blob = await fetchAssetAsBlob(imageFile);
		currentImageObjectUrl = URL.createObjectURL(blob);
		canvasSelect.setImage(currentImageObjectUrl);
		canvasSelect.setData(convertAnnotationsToShapes(sampleDetail.annotations ?? []) as any);
		refreshAnnotationCount();
		syncSelectionAfterDataLoad();
		return;
	}
	await loadHyperspectralAssets();
	canvasSelect.setData(convertAnnotationsToShapes(sampleDetail.annotations ?? []) as any);
	refreshAnnotationCount();
	syncSelectionAfterDataLoad();
}

async function loadHyperspectralAssets() {
	if (!sampleDetail || !canvasSelect) return;
	const hdrFile = sampleDetail.source_files.find((file) => getExtension(file) === HDR_EXT);
	const speFile = sampleDetail.source_files.find((file) => getExtension(file) === SPE_EXT);
	if (!hdrFile || !speFile) {
		toasts.add({ message: '缺少 HDR 或 SPE 文件', type: 'error' });
		return;
	}
	parser = new HSIParser();
	const hdrText = await fetchAssetAsText(hdrFile);
	parser.parseHeader(hdrText);
	const fileName = speFile.split('/').pop() ?? 'sample.spe';
	const speBinaryBlob = await fetchAssetAsBlob(speFile);
	const speFileObject = new File([speBinaryBlob], fileName, { type: speBinaryBlob.type });
	const shouldStream = speFileObject.size >= (parser?.largeFileThreshold ?? 512 * 1024 * 1024);
	const speBuffer = shouldStream ? null : await speBinaryBlob.arrayBuffer();
	await parser.parseSPE(speBuffer ?? undefined, speFileObject);

	const darkFile = sampleDetail.source_files.find((file) => getExtension(file) === DARK_EXT);
	const whiteFile = sampleDetail.source_files.find((file) => getExtension(file) === WHITE_EXT);
	if (darkFile) {
		const buf = await fetchAssetAsArrayBuffer(darkFile);
		await parser.parseCalibrationFile(buf, 'dark');
		applyDarkCalibration = true;
	}
	if (whiteFile) {
		const buf = await fetchAssetAsArrayBuffer(whiteFile);
		await parser.parseCalibrationFile(buf, 'white');
		applyWhiteCalibration = true;
	}
	parser.applyCalibration(applyDarkCalibration, applyWhiteCalibration);
	updateChannelOptionsFromParser();
	if (!renderer) {
		const hiddenCanvas = document.createElement('canvas');
		renderer = new HSIRenderer(hiddenCanvas);
	}
	renderer.setParser(parser);
	if (!spectrumExtractor) {
		spectrumExtractor = new SpectrumExtractor(parser);
	} else {
		spectrumExtractor.setParser(parser);
	}
	spectralDataReady = true;
	await renderCurrentSpectralMode();
}

function resolveBandIndex(channelValue: number | null | undefined) {
	if (!parser) return 0;
	const dims = parser.getDimensions?.();
	if (!dims) return 0;
	const bands = dims.bands ?? 0;
	const normalized = Number.isFinite(channelValue ?? 0) ? Math.floor(channelValue ?? 0) : 0;
	if (normalized >= 0 && normalized < bands) {
		return normalized;
	}
	const wavelengths = parser.getWavelengths?.() ?? [];
	if (wavelengths.length > 0 && Number.isFinite(channelValue ?? null)) {
		const target = channelValue ?? 0;
		let closestIdx = 0;
		let minDiff = Infinity;
		for (let i = 0; i < wavelengths.length; i++) {
			const diff = Math.abs(wavelengths[i] - target);
			if (diff < minDiff) {
				minDiff = diff;
				closestIdx = i;
			}
		}
		return closestIdx;
	}
	return Math.min(Math.max(normalized, 0), Math.max(bands - 1, 0));
}

function normalizeDisplayChannels() {
	if (!parser) return;
	activeDisplayMode.r_channel = resolveBandIndex(activeDisplayMode.r_channel);
	activeDisplayMode.g_channel = resolveBandIndex(activeDisplayMode.g_channel);
	activeDisplayMode.b_channel = resolveBandIndex(activeDisplayMode.b_channel);
}

function updateChannelOptionsFromParser() {
	if (!parser) {
		channelOptions = [];
		return;
	}
	const dims = parser.getDimensions?.();
	const bands = Math.max(dims?.bands ?? 0, 0);
	if (!bands) {
		channelOptions = [];
		return;
	}
	const wavelengths = parser.getWavelengths?.() ?? [];
	channelOptions = Array.from({ length: bands }, (_, index) => {
		const wavelength = wavelengths[index];
		const hasWavelength = typeof wavelength === 'number' && Number.isFinite(wavelength);
		const rounded = hasWavelength ? Math.round(wavelength) : null;
		const label = hasWavelength ? `波段 ${index + 1} · ${rounded}nm` : `波段 ${index + 1}`;
		return { value: index, label };
	});
	normalizeDisplayChannels();
}

async function renderCurrentSpectralMode() {
	if (!renderer || !parser || !canvasSelect || !spectralDataReady) return;
	renderer.setParser(parser);
	const mode = activeDisplayMode;
	currentModeMemo = {
		...mode,
		dark_calibration: applyDarkCalibration,
		white_calibration: applyWhiteCalibration,
	};
	try {
		const rBand = resolveBandIndex(mode.r_channel);
		const gBand = resolveBandIndex(mode.g_channel);
		const bBand = resolveBandIndex(mode.b_channel);
		renderer.setAlgorithm(mode.gain_algorithm ?? 'linear');
		await renderer.renderFalseColor(
			rBand,
			gBand,
			bBand,
			mode.r_gain ?? 0,
			mode.g_gain ?? 0,
			mode.b_gain ?? 0,
		);
		const dataUrl = renderer.canvas.toDataURL('image/png');
		canvasSelect.setImage(dataUrl);
		if (!canvasSelect.dataset.length && sampleDetail?.annotations?.length) {
			canvasSelect.setData(convertAnnotationsToShapes(sampleDetail.annotations) as any);
		}
	} catch (error) {
		toasts.add({ message: extractApiError(error, '渲染高光谱失败'), type: 'error' });
	}
}

function convertAnnotationsToShapes(annotations: AnnotationSampleDetail['annotations']): any[] {
	if (!annotations) return [];
	return annotations.map((detail) => {
		const type = TOOL_TYPE_TO_CANVAS[detail.tool_type] ?? 1;
		const coordinates = (detail.coordinates?.coor as unknown) ?? detail.coordinates ?? [];
		const color = detail.color || DEFAULT_LABEL_COLOR;
		const shape: Record<string, any> = {
			type,
			label: detail.label_name,
			strokeStyle: color,
			fillStyle: toRgba(color, DEFAULT_FILL_ALPHA),
			coor: coordinates,
			uuid: detail.detail_id,
			radius: detail.radius ?? undefined,
			row: detail.coordinates?.row,
			col: detail.coordinates?.col,
			selected: detail.coordinates?.selected,
			modeSnapshot: detail.mode_snapshot,
			spectraPoints: detail.spectra?.[0]?.points ?? [],
		};
		return shape;
	});
}

function convertShapesToPayload(shapes: any[]): AnnotationDetailCreate[] {
	return shapes.map((shape) => {
		const toolType = CANVAS_TYPE_TO_TOOL[shape.type] ?? 'rect';
		const fallbackColor = selectedLabelColor || DEFAULT_LABEL_COLOR;
		const snapshotSource = shape.modeSnapshot ?? currentModeMemo;
		const modeSnapshotPayload = snapshotSource
			? {
					r_channel: snapshotSource.r_channel,
					g_channel: snapshotSource.g_channel,
					b_channel: snapshotSource.b_channel,
					r_gain: snapshotSource.r_gain ?? 1,
					g_gain: snapshotSource.g_gain ?? 1,
					b_gain: snapshotSource.b_gain ?? 1,
					gain_algorithm: snapshotSource.gain_algorithm ?? 'linear',
					dark_calibration:
						typeof snapshotSource.dark_calibration === 'boolean'
							? snapshotSource.dark_calibration
							: applyDarkCalibration,
					white_calibration:
						typeof snapshotSource.white_calibration === 'boolean'
							? snapshotSource.white_calibration
							: applyWhiteCalibration,
			  }
			: undefined;
		const payload: AnnotationDetailCreate = {
			label_name: shape.label || selectedLabelName || '未命名',
			color: shape.strokeStyle || fallbackColor,
			tool_type: toolType as AnnotationDetailCreate['tool_type'],
			coordinates: {
				coor: shape.coor ?? [],
				row: shape.row ?? null,
				col: shape.col ?? null,
				selected: shape.selected ?? [],
			},
			radius: shape.radius ?? null,
			area: shape.area ?? null,
			confidence: shape.confidence ?? null,
			mode_snapshot: modeSnapshotPayload,
			spectra: shape.spectraPoints && shape.spectraPoints.length
				? [
						{
							position: null,
							points: shape.spectraPoints,
						},
				  ]
				: [],
		};
		return payload;
	});
}

function attachCanvasEvents() {
	if (!canvasSelect || !annotationCanvas) return;
	canvasSelect.on('updated', (dataset: any) => {
		annotationDirty = true;
		updateZoomRatio();
		refreshAnnotationCount();
	});
	canvasSelect.on('select', (shape: any) => {
		if (shape) {
			selectedDetailId = shape.uuid ?? null;
			showAllSpectra = false;
			renderSpectrumForShape(shape);
		} else {
			selectedDetailId = null;
			setSpectrumView(null);
			spectrumChart?.clear();
		}
	});
	canvasSelect.on('add', (shape: any) => {
		handleShapeAdded(shape);
	});
	canvasSelect.on('delete', () => {
		handleShapeDeleted();
	});
	annotationCanvas.addEventListener('mousemove', () => {
		if (!canvasSelect) return;
		cursorPosition = [canvasSelect.mouse?.[0] ?? 0, canvasSelect.mouse?.[1] ?? 0];
	});
}

function updateZoomRatio() {
	if (!canvasSelect) return;
	zoomRatio = Number(canvasSelect.scale?.toFixed(2)) || 1;
}

async function persistAnnotations(successMessage?: string) {
	if (!canvasSelect || !sampleDetail) return;
	savingAnnotations = true;
	try {
		const dataset = canvasSelect.dataset ?? [];
		if (sampleDetail.sample_type === 'hyperspectral') {
			for (const shape of dataset) {
				if (!shape.spectraPoints?.length) {
					await captureSpectrumForShape(shape, { updateView: false });
				}
			}
		}
		const payload = {
			annotations: convertShapesToPayload(dataset),
			mark_annotated: dataset.length > 0,
		};
		const result = await replaceSampleAnnotationsEndpointApiV1SamplesSampleIdAnnotationsPut({
			path: { sample_id: sampleDetail.id },
			body: payload,
		});
		const data = unwrapOrThrow(result, '保存失败');
		sampleDetail = data;
		samples = samples.map((item) =>
			item.id === data.id ? { ...item, is_annotated: data.is_annotated, has_annotations: data.is_annotated } : item,
		);
		const shapes = convertAnnotationsToShapes(data.annotations ?? []) as any;
		canvasSelect.setData(shapes);
		refreshAnnotationCount();
		annotationDirty = false;
		syncSelectionAfterDataLoad();
		resetSelectionsAfterSave();
		if (successMessage) {
			toasts.add({ message: successMessage, type: 'success' });
		}
	} catch (error) {
		toasts.add({ message: extractApiError(error, '保存标注失败'), type: 'error' });
		throw error;
	} finally {
		savingAnnotations = false;
	}
}

async function handleSaveAnnotations() {
	if (!canvasSelect || !sampleDetail || savingAnnotations) return;
	await persistAnnotations('标注已保存');
}

function resetSelectionsAfterSave() {
	applySelectedLabel('');
	handleToolSelect(0);
}

async function handleToggleIgnored() {
	if (!sampleDetail || markingIgnored) return;
	markingIgnored = true;
	try {
		const nextStatus = sampleDetail.status === 'ignored' ? 'valid' : 'ignored';
		const result = await updateSampleStatusEndpointApiV1SamplesSampleIdPatch({
			path: { sample_id: sampleDetail.id },
			body: { status: nextStatus, is_annotated: sampleDetail.is_annotated },
		});
		const data = unwrapOrThrow(result, '更新失败');
		sampleDetail = data;
		samples = samples.map((item) => (item.id === data.id ? { ...item, status: data.status } : item));
		toasts.add({ message: nextStatus === 'ignored' ? '样本已排除' : '样本已恢复', type: 'success' });
	} catch (error) {
		toasts.add({ message: extractApiError(error, '更新状态失败'), type: 'error' });
	} finally {
		markingIgnored = false;
	}
}

async function captureSpectrumForShape(shape: any, options: { updateView?: boolean } = {}) {
	if (!spectrumExtractor || sampleDetail?.sample_type !== 'hyperspectral') return null;
	const { updateView = false } = options;
	try {
		let spectrum;
		if (shape.type === 1) {
			spectrum = await spectrumExtractor.getRegionSpectrum(spectrumExtractor.getPixelsInRectangle(shape));
		} else if (shape.type === 2) {
			spectrum = await spectrumExtractor.getRegionSpectrum(spectrumExtractor.getPixelsInPolygon(shape));
		} else if (shape.type === 5) {
			spectrum = await spectrumExtractor.getRegionSpectrum(spectrumExtractor.getPixelsInCircle(shape));
		} else {
			const [x, y] = shape.coor ?? [0, 0];
			spectrum = await spectrumExtractor.getPointSpectrum(x, y);
		}
		if (spectrum) {
			const seriesPoints = spectrum.wavelengths.map((wl: number, idx: number) => ({
				wavelength: wl,
				intensity: spectrum.values[idx],
			}));
			shape.spectraPoints = seriesPoints;
			if (updateView && spectrumChart) {
				const color = shape.strokeStyle || selectedLabelColor || DEFAULT_LABEL_COLOR;
				selectedDetailId = shape.uuid ?? selectedDetailId;
				showAllSpectra = false;
				showSingleSpectrum(spectrum.wavelengths, spectrum.values, shape.label || selectedLabelName || 'Spectrum', color);
			}
			return spectrum;
		}
	} catch (error) {
		console.warn(error);
		if (updateView) {
			toasts.add({ message: extractApiError(error, '光谱提取失败'), type: 'error' });
		}
	}
	return null;
}

async function renderSpectrumForShape(shape: any) {
	await captureSpectrumForShape(shape, { updateView: true });
}

function handleToolSelect(type: number) {
	if (!canvasSelect) return;
	disableAnchorPicking();
	canvasSelect.createType = type;
	activeTool = type;
}

function handleZoomIn() {
	canvasSelect?.setScale(true);
	updateZoomRatio();
}

function handleZoomOut() {
	canvasSelect?.setScale(false);
	updateZoomRatio();
}

function handleFit() {
	canvasSelect?.fitZoom();
	updateZoomRatio();
}

function handlePrevNext(direction: -1 | 1) {
	if (!selectedSampleId) return;
	const index = samples.findIndex((item) => item.id === selectedSampleId);
	if (index === -1) return;
	const target = samples[index + direction];
	if (target) {
		selectSample(target.id);
	}
}

onMount(() => {
	const pref = loadPreferencesFromStorage();
	if (pref) {
		preferences = pref;
	}
	if (typeof window !== 'undefined') {
		window.addEventListener('hsi-fixed-preferences-change', handlePreferenceChange as EventListener);
	}
	canvasSelect = annotationCanvas ? new CanvasSelect(annotationCanvas) : null;
	if (canvasSelect) {
		setCanvasDrawingStyles(selectedLabelColor);
	}
	refreshAnnotationCount();
	renderer = new HSIRenderer(document.createElement('canvas'));
	spectrumExtractor = new SpectrumExtractor(new HSIParser());
	if (spectrumCanvas) {
		spectrumChart = new SpectrumChart(spectrumCanvas);
		spectrumChart.initialize();
	}
	if (canvasSelect && pref) {
		applyPreferencesToCanvas(pref);
	}
	attachCanvasEvents();
	void fetchProjects();
	void fetchLabelGroups();
	void fetchSpectralModes();
	return () => {
		canvasSelect?.destroy();
		if (currentImageObjectUrl) {
			URL.revokeObjectURL(currentImageObjectUrl);
			currentImageObjectUrl = null;
		}
		if (typeof window !== 'undefined') {
			window.removeEventListener('hsi-fixed-preferences-change', handlePreferenceChange as EventListener);
		}
		spectrumChart?.destroy();
	};
});
</script>

<svelte:head>
	<title>在线任务 - HSI Annotation</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex flex-wrap items-center justify-between gap-4">
		<div>
			<h1 class="text-3xl font-bold">在线任务</h1>
			<p class="text-muted-foreground">加载项目样本，高光谱可视化 + 标注 + 光谱曲线</p>
		</div>
		<div class="flex flex-wrap items-center gap-3">
				<label class="flex items-center gap-2 text-sm text-muted-foreground">
					<span>项目</span>
					<select
						class="rounded-md border px-3 py-1 text-sm"
						value={selectedProjectId ?? ''}
						onchange={handleProjectChange}
					>
						<option value="">未选择项目</option>
						{#each projects as project}
							<option value={project.id}>{project.name}</option>
						{/each}
					</select>
				</label>
			<Button variant="outline" onclick={() => fetchSampleDetail()} disabled={!selectedSampleId}>
				刷新样本
			</Button>
		</div>
	</div>

		<div class="grid gap-4 lg:grid-cols-[300px_1fr_320px]">
			<div class="space-y-4 h-full">
				<Card class="h-full space-y-4 p-6">
					<section class="space-y-2">
						<h3 class="text-sm font-semibold">显示模式预设</h3>
						{#if spectralModes.length === 0}
							<p class="text-xs text-muted-foreground">暂无显示模式预设</p>
						{:else}
								<select
									class="w-full rounded border px-3 py-2 text-sm"
									bind:value={spectralPresetSelection}
									onchange={handlePresetModeChange}
								>
									<option value="">{spectralPresetApplied ? '已选择预设' : '未选择预设'}</option>
								{#each spectralModes as mode}
									<option value={mode.id}>{mode.name}</option>
								{/each}
							</select>
						{/if}
				</section>

					<section class="space-y-3">
						<h3 class="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
							CALIBRATION CHANNEL SELECTION
						</h3>
						{#if sampleDetail?.sample_type === 'hyperspectral'}
							<div class="space-y-3">
								{#each CHANNEL_FIELDS as channel (channel.key)}
									{@const inputId = `channel-${channel.key}`}
									<div class="space-y-1">
										<div class="flex items-center gap-2">
											<label class="w-20 text-xs font-medium text-muted-foreground" for={inputId}>{channel.label}</label>
											<select
												id={inputId}
												class="flex-1 rounded border px-3 py-2 text-sm"
												value={channelOptions.length ? String(activeDisplayMode[channel.key] ?? '') : ''}
												onchange={(event) => {
													const next = Number((event.currentTarget as HTMLSelectElement).value);
													activeDisplayMode[channel.key] = Number.isFinite(next) ? next : 0;
												}}
												disabled={channelOptions.length === 0}
											>
												{#if channelOptions.length === 0}
													<option value="">
														{sampleDetail?.sample_type === 'hyperspectral' ? '波段加载中...' : '暂无可选波段'}
													</option>
												{:else}
													{#each channelOptions as option}
														<option value={option.value}>{option.label}</option>
													{/each}
												{/if}
											</select>
										</div>
										{#if channelOptions.length > 0}
											<p class="pl-20 text-[11px] text-muted-foreground">
												{channelLabelFor(activeDisplayMode[channel.key])}
											</p>
										{/if}
									</div>
								{/each}
							</div>
						{:else if sampleDetail}
							<p class="text-xs text-muted-foreground">当前样本类型为图像，波段选择不可用</p>
						{:else}
							<p class="text-xs text-muted-foreground">选择高光谱样本以调整波段</p>
						{/if}
					</section>

					<section class="space-y-3">
						<h3 class="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
							VISUALIZATION GAIN
						</h3>
						{#if sampleDetail?.sample_type === 'hyperspectral'}
							<div class="space-y-2">
								<label class="text-xs font-medium text-muted-foreground" for="gain-algorithm-select">Gain Algorithm</label>
								<select
									class="w-full rounded border px-3 py-2 text-sm"
									bind:value={activeDisplayMode.gain_algorithm}
									id="gain-algorithm-select"
								>
									<option value="percentile-gamma">Percentile + Gamma</option>
									<option value="percentile">Percentile</option>
									<option value="gamma">Gamma</option>
									<option value="linear">Linear</option>
									<option value="log">Log</option>
									<option value="histogram">Histogram</option>
									<option value="raw">Raw</option>
								</select>
							</div>
							{#each GAIN_FIELDS as gain (gain.key)}
								{@const gainInputId = `gain-${gain.key}`}
								<div class="space-y-1">
									<label class="text-xs font-medium text-muted-foreground" for={gainInputId}>{gain.label}</label>
									<div class="flex items-center gap-2">
										<input
											type="range"
											min="-4096"
											max="4096"
											step="1"
											value={activeDisplayMode[gain.key]}
											oninput={(event) =>
												(activeDisplayMode[gain.key] = Number(
													(event.currentTarget as HTMLInputElement).value,
												))}
											class="h-1 flex-1 accent-primary"
										/>
										<input
											type="number"
											min="-4096"
											max="4096"
											class="w-20 rounded border px-2 py-1 text-sm"
											id={gainInputId}
											value={activeDisplayMode[gain.key]}
											oninput={(event) =>
												(activeDisplayMode[gain.key] = Number(
													(event.currentTarget as HTMLInputElement).value,
												))}
										/>
									</div>
								</div>
							{/each}
						{:else if sampleDetail}
							<p class="text-xs text-muted-foreground">当前样本为图像，伪彩增益不可用</p>
						{:else}
							<p class="text-xs text-muted-foreground">选择高光谱样本以调节增益</p>
						{/if}
					</section>

					<section class="space-y-2">
						<h3 class="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Calibration</h3>
						{#if sampleDetail?.sample_type === 'hyperspectral'}
							<div class="flex items-center gap-3 text-xs text-muted-foreground">
								<label class="flex items-center gap-1">
									<input type="checkbox" bind:checked={applyDarkCalibration} onchange={handleCalibrationToggle} />
									暗场
								</label>
								<label class="flex items-center gap-1">
									<input type="checkbox" bind:checked={applyWhiteCalibration} onchange={handleCalibrationToggle} />
									白板
								</label>
							</div>
						{:else if sampleDetail}
							<p class="text-xs text-muted-foreground">当前样本为图像，校准选项不可用</p>
						{:else}
							<p class="text-xs text-muted-foreground">选择高光谱样本以启用校准</p>
						{/if}
						</section>
				</Card>
		</div>

		<Card class="flex-1">
				<CardHeader class="flex flex-row items-center justify-between">
					<CardTitle>标注画布</CardTitle>
					<div class="flex items-center gap-2 text-sm text-muted-foreground">
						<span>缩放 {zoomRatio}x</span>
					</div>
				</CardHeader>
				<CardContent class="min-h-[500px]">
						<div class="relative flex h-[520px] items-center justify-center rounded border bg-muted/30">
							<canvas
								bind:this={annotationCanvas}
								class={`h-full w-full ${anchorPicking ? 'cursor-crosshair' : ''}`}
								onclick={handleAnnotationCanvasClick}
							></canvas>
							{#if !sampleDetail && !loadingSampleDetail}
								<p class="absolute text-sm text-muted-foreground">选择样本以加载画布</p>
							{/if}
						</div>
					<div class="mt-3 flex flex-wrap items-center gap-2">
						<Button variant="outline" size="sm" onclick={handleZoomIn} title="放大">
							+
						</Button>
						<Button variant="outline" size="sm" onclick={handleZoomOut} title="缩小">
							-
						</Button>
						<Button variant="outline" size="sm" onclick={handleFit} title="适配">
							适配
						</Button>
						<Button variant="outline" size="sm" onclick={() => handlePrevNext(-1)} disabled={!selectedSampleId}>
							上一张
						</Button>
						<Button variant="outline" size="sm" onclick={() => handlePrevNext(1)} disabled={!selectedSampleId}>
							下一张
						</Button>
						<div class="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
							<span>坐标：{cursorPosition[0]}, {cursorPosition[1]}</span>
							<span>样本状态：{sampleDetail?.status ?? '-'}</span>
						</div>
					</div>
				</CardContent>
			</Card>

		<div class="space-y-4">
			<Card class="flex max-h-[220px] flex-col">
				<CardHeader>
					<CardTitle class="flex items-center gap-2 text-sm font-semibold">
						<span>样本列表</span>
						<span class="text-[11px] text-muted-foreground">({samples.length})</span>
					</CardTitle>
				</CardHeader>
				<CardContent class="flex-1 overflow-y-auto pr-1">
					{#if loadingSamples}
						<p class="text-sm text-muted-foreground">加载中…</p>
					{:else if !selectedProjectId}
						<p class="text-sm text-muted-foreground">请选择项目以查看样本</p>
					{:else if samples.length === 0}
						<p class="text-sm text-muted-foreground">暂无样本</p>
					{:else}
						<ul class="space-y-2">
							{#each samples as sample}
								<li>
									<button
										type="button"
										class={`w-full rounded border px-3 py-2 text-left text-sm ${selectedSampleId === sample.id ? 'border-primary bg-primary/5' : 'border-muted'}`}
										onclick={() => selectSample(sample.id)}
									>
										<div class="flex items-center justify-between">
											<span class="font-medium">#{sample.id}</span>
											<span class={`text-xs ${sample.is_annotated ? 'text-green-600' : 'text-muted-foreground'}`}>
												{sample.is_annotated ? '已标注' : '未标注'}
											</span>
										</div>
									</button>
								</li>
							{/each}
						</ul>
					{/if}
				</CardContent>
			</Card>

			<Card class="space-y-4 p-6">
				<section class="space-y-3">
					<h3 class="text-sm font-semibold">标签组</h3>
						{#if labelGroups.length === 0}
							<p class="text-xs text-muted-foreground">暂无标签组</p>
						{:else}
								<select
									class="w-full rounded border px-3 py-2 text-sm"
									bind:value={labelPresetSelection}
									onchange={handleLabelGroupChange}
								>
									<option value="">{labelPresetApplied ? '已选择预设' : '未选择预设'}</option>
								{#each labelGroups as group}
									<option value={group.id}>{group.name}</option>
							{/each}
						</select>
					{/if}
					<div class="space-y-2 rounded border p-3">
						<div class="flex flex-wrap gap-2">
							<button
								type="button"
								class={`rounded border px-2 py-1 text-xs ${!selectedLabelName ? 'border-primary bg-primary/5' : 'border-muted'}`}
								onclick={() => applySelectedLabel('')}
							>
								未选择
							</button>
							{#if activeLabels.length === 0}
								<span class="text-xs text-muted-foreground">当前标签容器为空，可选择预设或手动添加</span>
							{:else}
								{#each activeLabels as label (label.name)}
									<div class="flex items-center gap-1">
										<button
											type="button"
											class={`rounded border px-2 py-1 text-xs ${selectedLabelName === label.name ? 'border-primary bg-primary/5' : 'border-muted'}`}
											onclick={() => applySelectedLabel(label.name)}
										>
											<span class="mr-1 inline-block h-2 w-2 rounded-full" style={`background:${label.color};`}></span>
											{label.name}
										</button>
										<button
											type="button"
											class="text-xs text-muted-foreground hover:text-destructive"
											onclick={(event) => {
												event.stopPropagation();
												handleRemoveActiveLabel(label.name);
											}}
										>
											✕
										</button>
									</div>
								{/each}
							{/if}
						</div>
						<div class="flex gap-2">
							<Input class="flex-1" bind:value={newLabelName} placeholder="新增标签名称" />
							<Button type="button" size="sm" onclick={handleAddActiveLabel}>
								添加
							</Button>
						</div>
					</div>
				</section>

				<section class="space-y-3">
					<h3 class="text-sm font-semibold">工具</h3>
					<div class="grid grid-cols-2 gap-2">
						{#each TOOL_OPTIONS as option}
							<button
								type="button"
								class={`rounded border px-2 py-1 text-xs ${activeTool === option.type ? 'border-primary bg-primary/5' : 'border-muted'}`}
								onclick={() => handleToolSelect(option.type)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</section>

				<section class="space-y-3">
					<div class="space-y-2">
						<Button variant="outline" onclick={handleToggleIgnored} disabled={!sampleDetail || markingIgnored}>
							{sampleDetail?.status === 'ignored' ? '恢复样本' : '排除当前样本'}
						</Button>
						<Button onclick={handleSaveAnnotations} disabled={!canPersistAnnotations}>
							{savingAnnotations ? '保存中…' : '保存标注'}
						</Button>
					</div>
				</section>
			</Card>
		</div>
	</div>

	<div class="grid gap-4 lg:grid-cols-2">
		<Card>
			<CardHeader class="flex flex-row items-center justify-between">
				<CardTitle>光谱曲线</CardTitle>
				<div class="flex flex-col items-end gap-2 text-xs text-muted-foreground md:flex-row md:items-center">
					<div class="flex items-center gap-2">
						<span>平滑</span>
						<input
							type="range"
							min="0"
							max="8"
							step="1"
							bind:value={smoothingLevel}
							class="h-1 w-24 accent-primary"
							disabled={sampleDetail?.sample_type !== 'hyperspectral'}
						/>
						<span>{smoothingLevel}</span>
					</div>
					<Button variant="outline" size="sm" onclick={handleToggleAllSpectra} disabled={sampleDetail?.sample_type !== 'hyperspectral'}>
						{showAllSpectra ? '查看单条' : '展示全部光谱'}
					</Button>
					<Button
						variant={anchorPicking ? 'default' : 'outline'}
						size="sm"
						onclick={handleAnchorToggle}
						disabled={!canUseSpectrumTools()}
					>
						{anchorPicking ? '点击画布取样' : '取点光谱'}
					</Button>
				</div>
				{#if anchorPicking}
					<p class="text-[11px] text-primary">单击画布任一点查看光谱</p>
				{/if}
			</CardHeader>
			<CardContent class="relative h-72">
				<canvas bind:this={spectrumCanvas} class={`h-full w-full ${sampleDetail?.sample_type === 'hyperspectral' ? '' : 'opacity-30'}`}></canvas>
				{#if !sampleDetail}
					<div class="absolute inset-0 flex items-center justify-center rounded border border-dashed text-sm text-muted-foreground">
						选择样本后查看光谱
					</div>
				{:else if sampleDetail.sample_type !== 'hyperspectral'}
					<div class="absolute inset-0 flex items-center justify-center rounded border border-dashed text-sm text-muted-foreground">
						当前样本为图像，未开启光谱分析
					</div>
				{/if}
			</CardContent>
		</Card>

		<Card>
			<CardHeader class="flex flex-row items-center justify-between">
				<CardTitle>标注细节</CardTitle>
				<p class="text-xs text-muted-foreground">共 {sampleDetail?.annotations?.length ?? 0} 条</p>
			</CardHeader>
			<CardContent class="h-72 overflow-auto text-xs">
				{#if sampleDetail?.annotations && sampleDetail.annotations.length > 0}
					<ul class="space-y-2">
						{#each sampleDetail.annotations as detail (detail.id)}
							<li
								class={`rounded border px-3 py-2 ${selectedDetailId === detail.detail_id ? 'border-primary bg-primary/5' : 'border-muted'}`}
							>
								<div class="flex items-start justify-between gap-2">
									<button
										type="button"
										class="flex-1 text-left"
										onclick={() => handleDetailSelect(detail)}
									>
										<div class="flex items-center gap-2 text-[11px] font-medium">
											<span class="h-2 w-2 rounded-full" style={`background-color: ${detail.color || DEFAULT_LABEL_COLOR}`}></span>
											<span>{detail.label_name || '未命名'}</span>
											<span class="text-muted-foreground">({detail.tool_type})</span>
										</div>
										<p class="mt-1 break-all text-[10px] text-muted-foreground">
											coordinates: {formatCoordinatePreview(detail)}
										</p>
									</button>
									<div>
										<Button
											variant="ghost"
											size="sm"
											class="px-2 text-red-500"
											disabled={savingAnnotations}
											onclick={(event) => {
												event.stopPropagation();
												void handleDeleteDetail(detail);
											}}
										>
											删除
										</Button>
									</div>
								</div>
							</li>
						{/each}
					</ul>
				{:else}
					<p class="text-muted-foreground">暂无已保存标注</p>
				{/if}
			</CardContent>
		</Card>
	</div>
</div>
