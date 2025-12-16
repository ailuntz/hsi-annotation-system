const app = {
    parser: new HSIParser(),
    renderer: null,
    spectrumExtractor: null,
    spectrumChart: null,
    files: {
        hdr: null,
        spe: null,
        figspecblack: null,
        figspecwhite: null
    },
    calibration: {
        darkApplied: false,
        whiteApplied: false
    },

    autoRender: {
        enabled: true,
        isRendering: false,
        needsRender: false,
        lastRenderTime: 0,
        targetFPS: 10,
        minInterval: 100,
        renderTimeout: null,
        sliderTimeout: null
    },

    spectrum: {
        smoothLevel: 0,
        selectedAnnotation: null,
        isExtracting: false,
        anchorActive: false
    },

    mockAnnotations: [
        {
            label: "rectangle",
            labelFillStyle: "#f00",
            textFillStyle: "#fff",
            coor: [[184, 183], [275, 238]],
            type: 1
        },
        {
            label: "polygon",
            labelFillStyle: "#0f0",
            coor: [[135, 291], [129, 319], [146, 346], [174, 365], [214, 362], [196, 337], [161, 288]],
            type: 2
        },
        {
            label: "dot",
            labelFillStyle: "#00f",
            coor: [345, 406],
            type: 3
        },
        {
            label: "circle",
            labelFillStyle: "#f0f",
            coor: [369, 197],
            radius: 38,
            type: 5
        }
    ]
};

document.addEventListener('DOMContentLoaded', () => {
    console.log('HSI Viewer initialized');

    const canvas = document.getElementById('hsiCanvas');
    app.renderer = new HSIRenderer(canvas);
    app.renderer.setParser(app.parser);

    const spectrumCanvas = document.getElementById('spectrumChart');
    app.spectrumChart = new SpectrumChart(spectrumCanvas);
    app.spectrumExtractor = new SpectrumExtractor(app.parser);

    app.autoRender.minInterval = 1000 / app.autoRender.targetFPS;

    setupFileUpload();
    setupCalibration();
    setupChannelControls();
    setupGainControls();
    setupAlgorithmSelector();
    setupRenderButton();
    setupSpectrumControls();
    setupAnnotationList();
});

async function performRender() {
    if (!app.autoRender.enabled || app.autoRender.isRendering) {
        return;
    }

    try {
        app.autoRender.isRendering = true;
        app.autoRender.lastRenderTime = Date.now();

        const rBand = parseInt(document.getElementById('rChannel').value);
        const gBand = parseInt(document.getElementById('gChannel').value);
        const bBand = parseInt(document.getElementById('bChannel').value);

        const rGain = parseFloat(document.getElementById('rGain').value);
        const gGain = parseFloat(document.getElementById('gGain').value);
        const bGain = parseFloat(document.getElementById('bGain').value);

        await app.renderer.renderFalseColor(
            rBand, gBand, bBand,
            rGain, gGain, bGain
        );

        app.autoRender.needsRender = false;
    } catch (error) {
        console.error('Render error:', error);
    } finally {
        app.autoRender.isRendering = false;

        if (app.autoRender.needsRender) {
            scheduleRender();
        }
    }
}

function scheduleRender() {
    const now = Date.now();
    const timeSinceLastRender = now - app.autoRender.lastRenderTime;
    const timeUntilNextRender = Math.max(0, app.autoRender.minInterval - timeSinceLastRender);

    clearTimeout(app.autoRender.renderTimeout);
    app.autoRender.renderTimeout = setTimeout(() => {
        performRender();
    }, timeUntilNextRender);
}

function immediateRender() {
    if (!app.autoRender.enabled) return;

    clearTimeout(app.autoRender.renderTimeout);
    clearTimeout(app.autoRender.sliderTimeout);
    performRender();
}

function throttledRender() {
    if (!app.autoRender.enabled) return;

    app.autoRender.needsRender = true;

    const now = Date.now();
    const timeSinceLastRender = now - app.autoRender.lastRenderTime;

    if (timeSinceLastRender >= app.autoRender.minInterval && !app.autoRender.isRendering) {
        performRender();
    } else {
        scheduleRender();
    }
}

function debouncedRender(delay = 300) {
    if (!app.autoRender.enabled) return;

    clearTimeout(app.autoRender.renderTimeout);
    clearTimeout(app.autoRender.sliderTimeout);

    app.autoRender.sliderTimeout = setTimeout(() => {
        performRender();
    }, delay);
}

function setupFileUpload() {
    const fileInput = document.getElementById('fileInput');
    const fileStatus = document.getElementById('fileStatus');

    fileInput.addEventListener('change', async (event) => {
        const files = Array.from(event.target.files);

        if (files.length === 0) {
            return;
        }

        fileStatus.textContent = 'Processing files...';
        fileStatus.className = 'file-status info';

        try {

            const filesByExt = {};
            files.forEach(file => {
                const ext = file.name.split('.').pop().toLowerCase();
                filesByExt[ext] = file;
            });

            if (!filesByExt['hdr'] || !filesByExt['spe']) {
                throw new Error('Missing required files: .hdr and .spe files are required');
            }

            app.files.hdr = filesByExt['hdr'];
            app.files.spe = filesByExt['spe'];
            app.files.figspecblack = filesByExt['figspecblack'] || null;
            app.files.figspecwhite = filesByExt['figspecwhite'] || null;

            fileStatus.textContent = 'Parsing header file...';
            const hdrText = await readFileAsText(app.files.hdr);
            const metadata = app.parser.parseHeader(hdrText);

            console.log('Metadata:', metadata);

            const speFileSize = app.files.spe.size;
            const speFileSizeGB = (speFileSize / 1024 / 1024 / 1024).toFixed(2);

            if (speFileSize > 1024 * 1024 * 1024) {
                fileStatus.textContent = `Loading large hyperspectral data (${speFileSizeGB} GB)... This may take a while and use significant memory.`;
                console.warn(`Large file detected: ${speFileSizeGB} GB`);
            } else {
                fileStatus.textContent = 'Loading hyperspectral data... (this may take a moment)';
            }

            let result;
            if (speFileSize > 500 * 1024 * 1024) {
                console.log('Using on-demand loading mode for large file');
                fileStatus.textContent = `Setting up on-demand loading for ${speFileSizeGB} GB file...`;

                const headerBlob = app.files.spe.slice(0, 1024);
                const headerBuffer = await headerBlob.arrayBuffer();
                result = await app.parser.parseSPE(headerBuffer, app.files.spe);
                fileStatus.textContent = `On-demand mode ready (${speFileSizeGB} GB). Loading bands as needed...`;
            } else {
                const speBuffer = await readFileAsArrayBuffer(app.files.spe);
                console.log('SPE file loaded into memory:', {
                    size: speFileSize,
                    sizeGB: speFileSizeGB,
                    bufferByteLength: speBuffer.byteLength
                });
                result = await app.parser.parseSPE(speBuffer);
            }

            if (app.files.figspecblack) {
                fileStatus.textContent = 'Loading dark field calibration...';
                const darkBuffer = await readFileAsArrayBuffer(app.files.figspecblack);
                await app.parser.parseCalibrationFile(darkBuffer, 'dark');
            }

            if (app.files.figspecwhite) {
                fileStatus.textContent = 'Loading white field calibration...';
                const whiteBuffer = await readFileAsArrayBuffer(app.files.figspecwhite);
                await app.parser.parseCalibrationFile(whiteBuffer, 'white');
            }

            populateChannelSelectors();
            enableControls();

            const dims = app.parser.getDimensions();
            fileStatus.textContent = `Loaded: ${dims.samples}×${dims.lines} pixels, ${dims.bands} bands`;
            fileStatus.className = 'file-status success';

            document.getElementById('darkCalibBtn').disabled = !app.files.figspecblack;
            document.getElementById('whiteCalibBtn').disabled = !app.files.figspecwhite;

            app.spectrumExtractor.setParser(app.parser);

            setTimeout(() => {
                immediateRender();
            }, 100);

        } catch (error) {
            console.error('Error loading files:', error);
            fileStatus.textContent = `Error: ${error.message}`;
            fileStatus.className = 'file-status error';
        }
    });
}

function setupCalibration() {
    const darkBtn = document.getElementById('darkCalibBtn');
    const whiteBtn = document.getElementById('whiteCalibBtn');
    const calibStatus = document.getElementById('calibStatus');

    darkBtn.addEventListener('click', () => {
        app.calibration.darkApplied = !app.calibration.darkApplied;

        if (app.calibration.darkApplied) {
            darkBtn.textContent = 'Dark Field: ON';
            darkBtn.style.background = '#28a745';
        } else {
            darkBtn.textContent = 'Dark Field Calibration';
            darkBtn.style.background = '';
        }

        applyCalibration();
        updateCalibrationStatus(calibStatus);
        immediateRender();
    });

    whiteBtn.addEventListener('click', () => {
        app.calibration.whiteApplied = !app.calibration.whiteApplied;

        if (app.calibration.whiteApplied) {
            whiteBtn.textContent = 'White Field: ON';
            whiteBtn.style.background = '#28a745';
        } else {
            whiteBtn.textContent = 'White Field Calibration';
            whiteBtn.style.background = '';
        }

        applyCalibration();
        updateCalibrationStatus(calibStatus);
        immediateRender();
    });
}

function applyCalibration() {
    try {
        app.parser.applyCalibration(
            app.calibration.darkApplied,
            app.calibration.whiteApplied
        );
        console.log('Calibration applied:', app.calibration);
    } catch (error) {
        console.error('Calibration error:', error);
    }
}

function updateCalibrationStatus(statusElement) {
    const status = [];
    if (app.calibration.darkApplied) status.push('Dark field');
    if (app.calibration.whiteApplied) status.push('White field');

    if (status.length > 0) {
        statusElement.textContent = `Active: ${status.join(', ')}`;
        statusElement.className = 'calib-status success';
    } else {
        statusElement.textContent = '';
        statusElement.className = 'calib-status';
    }
}

function setupChannelControls() {
    const rChannel = document.getElementById('rChannel');
    const gChannel = document.getElementById('gChannel');
    const bChannel = document.getElementById('bChannel');

    const rWavelength = document.getElementById('rWavelength');
    const gWavelength = document.getElementById('gWavelength');
    const bWavelength = document.getElementById('bWavelength');

    rChannel.addEventListener('change', () => {
        const idx = parseInt(rChannel.value);
        const wl = app.parser.getWavelength(idx);
        rWavelength.textContent = wl ? `${wl.toFixed(2)} nm` : '';
        immediateRender();
    });

    gChannel.addEventListener('change', () => {
        const idx = parseInt(gChannel.value);
        const wl = app.parser.getWavelength(idx);
        gWavelength.textContent = wl ? `${wl.toFixed(2)} nm` : '';
        immediateRender();
    });

    bChannel.addEventListener('change', () => {
        const idx = parseInt(bChannel.value);
        const wl = app.parser.getWavelength(idx);
        bWavelength.textContent = wl ? `${wl.toFixed(2)} nm` : '';
        immediateRender();
    });
}

function setupAlgorithmSelector() {
    const algorithmSelector = document.getElementById('gainAlgorithm');

    algorithmSelector.addEventListener('change', () => {
        const selectedAlgorithm = algorithmSelector.value;
        app.renderer.setAlgorithm(selectedAlgorithm);
        console.log('Gain algorithm changed to:', selectedAlgorithm);
        immediateRender();
    });
}

function setupGainControls() {
    const rGain = document.getElementById('rGain');
    const gGain = document.getElementById('gGain');
    const bGain = document.getElementById('bGain');

    const rGainInput = document.getElementById('rGainInput');
    const gGainInput = document.getElementById('gGainInput');
    const bGainInput = document.getElementById('bGainInput');

    rGain.addEventListener('input', () => {
        rGainInput.value = rGain.value;
        throttledRender();
    });

    gGain.addEventListener('input', () => {
        gGainInput.value = gGain.value;
        throttledRender();
    });

    bGain.addEventListener('input', () => {
        bGainInput.value = bGain.value;
        throttledRender();
    });

    rGain.addEventListener('change', () => {
        debouncedRender(100);
    });

    gGain.addEventListener('change', () => {
        debouncedRender(100);
    });

    bGain.addEventListener('change', () => {
        debouncedRender(100);
    });

    rGainInput.addEventListener('input', () => {
        const value = Math.max(-4096, Math.min(4096, parseInt(rGainInput.value) || 0));
        rGainInput.value = value;
        rGain.value = value;
        debouncedRender(300);
    });

    gGainInput.addEventListener('input', () => {
        const value = Math.max(-4096, Math.min(4096, parseInt(gGainInput.value) || 0));
        gGainInput.value = value;
        gGain.value = value;
        debouncedRender(300);
    });

    bGainInput.addEventListener('input', () => {
        const value = Math.max(-4096, Math.min(4096, parseInt(bGainInput.value) || 0));
        bGainInput.value = value;
        bGain.value = value;
        debouncedRender(300);
    });
}

function setupRenderButton() {
    const renderBtn = document.getElementById('renderBtn');

    renderBtn.addEventListener('click', () => {
        console.log('Manual refresh triggered');
        immediateRender();
    });
}

function populateChannelSelectors() {
    const wavelengths = app.parser.getWavelengths();
    const rChannel = document.getElementById('rChannel');
    const gChannel = document.getElementById('gChannel');
    const bChannel = document.getElementById('bChannel');

    rChannel.innerHTML = '';
    gChannel.innerHTML = '';
    bChannel.innerHTML = '';

    wavelengths.forEach((wl, idx) => {
        const rOption = document.createElement('option');
        rOption.value = idx;
        rOption.textContent = `Band ${idx + 1}: ${wl.toFixed(2)} nm`;
        rChannel.appendChild(rOption);

        const gOption = rOption.cloneNode(true);
        const bOption = rOption.cloneNode(true);

        gChannel.appendChild(gOption);
        bChannel.appendChild(bOption);
    });

    const metadata = app.parser.metadata;
    let redIdx, greenIdx, blueIdx;

    if (metadata['default bands'] && Array.isArray(metadata['default bands']) && metadata['default bands'].length === 3) {

        redIdx = Math.min(Math.max(0, metadata['default bands'][0]), wavelengths.length - 1);
        greenIdx = Math.min(Math.max(0, metadata['default bands'][1]), wavelengths.length - 1);
        blueIdx = Math.min(Math.max(0, metadata['default bands'][2]), wavelengths.length - 1);
        console.log('Using default bands from .hdr file:', metadata['default bands']);
    } else {

        redIdx = Math.min(123, wavelengths.length - 1);
        greenIdx = Math.min(67, wavelengths.length - 1);
        blueIdx = Math.min(25, wavelengths.length - 1);
        console.log('Using fallback default bands: R=123, G=67, B=25');
    }

    rChannel.value = redIdx;
    gChannel.value = greenIdx;
    bChannel.value = blueIdx;

    rChannel.dispatchEvent(new Event('change'));
    gChannel.dispatchEvent(new Event('change'));
    bChannel.dispatchEvent(new Event('change'));
}

function findClosestWavelength(wavelengths, target) {
    let closest = 0;
    let minDiff = Math.abs(wavelengths[0] - target);

    for (let i = 1; i < wavelengths.length; i++) {
        const diff = Math.abs(wavelengths[i] - target);
        if (diff < minDiff) {
            minDiff = diff;
            closest = i;
        }
    }

    return closest;
}

function enableControls() {
    document.getElementById('rChannel').disabled = false;
    document.getElementById('gChannel').disabled = false;
    document.getElementById('bChannel').disabled = false;
    document.getElementById('rGain').disabled = false;
    document.getElementById('gGain').disabled = false;
    document.getElementById('bGain').disabled = false;
    document.getElementById('rGainInput').disabled = false;
    document.getElementById('gGainInput').disabled = false;
    document.getElementById('bGainInput').disabled = false;
    document.getElementById('renderBtn').disabled = false;
}

function readFileAsText(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsText(file);
    });
}

function readFileAsArrayBuffer(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();

        reader.onload = (event) => {
            const result = event.target.result;
            console.log('FileReader onload:', {
                fileName: file.name,
                fileSize: file.size,
                resultByteLength: result.byteLength,
                resultByteOffset: result.byteOffset || 0,
                match: file.size === result.byteLength
            });

            if (result.byteLength !== file.size) {
                reject(new Error(`File size mismatch: expected ${file.size}, got ${result.byteLength}`));
                return;
            }

            resolve(result);
        };

        reader.onerror = (event) => {
            console.error('FileReader error:', reader.error);
            reject(new Error(`Failed to read file ${file.name}: ${reader.error.message}`));
        };

        reader.onprogress = (event) => {
            if (event.lengthComputable) {
                const percentComplete = (event.loaded / event.total) * 100;
                console.log(`Reading ${file.name}: ${percentComplete.toFixed(1)}%`);
            }
        };

        try {
            reader.readAsArrayBuffer(file);
        } catch (error) {
            console.error('Error starting FileReader:', error);
            reject(new Error(`Failed to start reading file ${file.name}: ${error.message}`));
        }
    });
}

function setupSpectrumControls() {
    const smoothLevelSlider = document.getElementById('smoothLevel');
    const smoothLevelValue = document.getElementById('smoothLevelValue');
    const anchorBtn = document.getElementById('anchorBtn');
    const anchorHint = document.getElementById('anchorHint');
    const hsiCanvas = document.getElementById('hsiCanvas');

    smoothLevelSlider.addEventListener('input', () => {
        const level = parseInt(smoothLevelSlider.value);
        app.spectrum.smoothLevel = level;
        smoothLevelValue.textContent = level === 0 ? 'Off' : level;

        if (app.spectrumChart && app.spectrumChart.currentData) {
            const { wavelengths, values, label, color } = app.spectrumChart.currentData;

            if (!app.spectrumChart.chart) {
                app.spectrumChart.initialize();
            }

            const windowSize = level * 2 + 1;
            const displayValues = level > 0 ?
                app.spectrumChart.smoothData(values, windowSize) : values;

            const baseLabel = label.split(' [Smooth:')[0];
            const newLabel = baseLabel + (level > 0 ? ` [Smooth: ${level}]` : '');

            app.spectrumChart.chart.data.labels = wavelengths.map(wl => wl.toFixed(2));
            app.spectrumChart.chart.data.datasets = [{
                label: newLabel,
                data: displayValues,
                borderColor: color,
                backgroundColor: color.replace('rgb', 'rgba').replace(')', ', 0.1)'),
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 4,
                tension: 0.1
            }];
            app.spectrumChart.chart.update();
        }
    });

    anchorBtn.addEventListener('click', () => {
        app.spectrum.anchorActive = !app.spectrum.anchorActive;

        if (app.spectrum.anchorActive) {
            anchorBtn.classList.add('active');
            anchorBtn.textContent = 'Anchoring...';
            anchorHint.textContent = 'Click on image to view spectrum';
            hsiCanvas.style.cursor = 'crosshair';
        } else {
            anchorBtn.classList.remove('active');
            anchorBtn.textContent = 'Anchor Point';
            anchorHint.textContent = '';
            hsiCanvas.style.cursor = 'default';
        }
    });

    hsiCanvas.addEventListener('click', async (e) => {

        if (!app.spectrum.anchorActive || app.spectrum.isExtracting) return;

        const rect = hsiCanvas.getBoundingClientRect();
        const x = Math.floor(e.clientX - rect.left);
        const y = Math.floor(e.clientY - rect.top);

        const dims = app.parser.getDimensions();
        if (!dims) return;

        const scaleX = dims.lines / hsiCanvas.width;
        const scaleY = dims.samples / hsiCanvas.height;

        const dataX = Math.floor(x * scaleX);
        const dataY = Math.floor(y * scaleY);

        if (dataX >= 0 && dataX < dims.lines && dataY >= 0 && dataY < dims.samples) {

            app.spectrum.anchorActive = false;
            anchorBtn.classList.remove('active');
            anchorBtn.textContent = 'Anchor Point';
            anchorHint.textContent = '';
            hsiCanvas.style.cursor = 'default';

            try {
                app.spectrum.isExtracting = true;
                showSpectrumStatus('Extracting...');

                const spectrum = await app.spectrumExtractor.getPointSpectrum(dataX, dataY);

                const baseLabel = `Point (${dataX}, ${dataY})`;
                const pointColor = 'rgb(59, 130, 246)';

                app.spectrumChart.currentData = {
                    wavelengths: spectrum.wavelengths,
                    values: spectrum.values,
                    label: baseLabel,
                    color: pointColor
                };

                if (!app.spectrumChart.chart) {
                    app.spectrumChart.initialize();
                }

                const windowSize = app.spectrum.smoothLevel * 2 + 1;
                const displayValues = app.spectrum.smoothLevel > 0 ?
                    app.spectrumChart.smoothData(spectrum.values, windowSize) : spectrum.values;

                const displayLabel = baseLabel +
                    (app.spectrum.smoothLevel > 0 ? ` [Smooth: ${app.spectrum.smoothLevel}]` : '');

                app.spectrumChart.chart.data.labels = spectrum.wavelengths.map(wl => wl.toFixed(2));
                app.spectrumChart.chart.data.datasets = [{
                    label: displayLabel,
                    data: displayValues,
                    borderColor: pointColor,
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    tension: 0.1
                }];
                app.spectrumChart.chart.update();

                hideSpectrumStatus();
            } catch (error) {
                console.error('Error extracting spectrum:', error);
                hideSpectrumStatus();
            } finally {
                app.spectrum.isExtracting = false;
            }
        } else {

            app.spectrum.anchorActive = false;
            anchorBtn.classList.remove('active');
            anchorBtn.textContent = 'Anchor Point';
            anchorHint.textContent = 'Click outside - anchor cancelled';
            hsiCanvas.style.cursor = 'default';

            setTimeout(() => {
                anchorHint.textContent = '';
            }, 2000);
        }
    });
}

function setupAnnotationList() {
    const annotationListContainer = document.getElementById('annotationList');

    app.mockAnnotations.forEach((annotation, index) => {
        const item = document.createElement('div');
        item.className = 'annotation-item';
        item.dataset.annotationId = annotation.id;

        const typeNames = {
            1: 'Rectangle',
            2: 'Polygon',
            3: 'Point',
            5: 'Circle'
        };

        item.innerHTML = `
            <div class="annotation-color" style="background: ${annotation.labelFillStyle}"></div>
            <div class="annotation-info">
                <div class="annotation-label">${annotation.label}</div>
                <div class="annotation-type">${typeNames[annotation.type]}</div>
            </div>
            <div class="annotation-badge">#${index + 1}</div>
        `;

        item.addEventListener('click', () => {
            selectAnnotation(annotation, item);
        });

        annotationListContainer.appendChild(item);
    });

    console.log('Annotation list populated with', app.mockAnnotations.length, 'items');
}

async function selectAnnotation(annotation, itemElement) {

    document.querySelectorAll('.annotation-item').forEach(el => {
        el.classList.remove('selected');
    });
    itemElement.classList.add('selected');

    app.spectrum.selectedAnnotation = annotation;

    console.log('Selected annotation:', annotation.label);

    try {
        app.spectrum.isExtracting = true;
        showSpectrumStatus('Extracting...');

        const spectrum = await app.spectrumExtractor.getAnnotationSpectrum(
            annotation,
            (progress) => {
                showSpectrumStatus(`Extracting... ${Math.round(progress)}%`);
            }
        );

        const label = annotation.label +
            (app.spectrum.smoothLevel > 0 ? ` [Smooth: ${app.spectrum.smoothLevel}]` : '');

        const windowSize = app.spectrum.smoothLevel * 2 + 1;
        const displayValues = app.spectrum.smoothLevel > 0 ?
            app.spectrumChart.smoothData(spectrum.values, windowSize) : spectrum.values;

        app.spectrumChart.currentData = {
            wavelengths: spectrum.wavelengths,
            values: spectrum.values,
            label: annotation.label,
            color: annotation.labelFillStyle
        };

        if (!app.spectrumChart.chart) {
            app.spectrumChart.initialize();
        }

        app.spectrumChart.chart.data.labels = spectrum.wavelengths.map(wl => wl.toFixed(2));
        app.spectrumChart.chart.data.datasets = [{
            label: label,
            data: displayValues,
            borderColor: annotation.labelFillStyle,
            backgroundColor: annotation.labelFillStyle.replace('rgb', 'rgba').replace(')', ', 0.1)'),
            borderWidth: 2,
            pointRadius: 0,
            pointHoverRadius: 4,
            tension: 0.1
        }];
        app.spectrumChart.chart.update();

        hideSpectrumStatus();
    } catch (error) {
        console.error('Error extracting annotation spectrum:', error);
        showSpectrumStatus('Error: ' + error.message);
        setTimeout(hideSpectrumStatus, 3000);
    } finally {
        app.spectrum.isExtracting = false;
    }
}

function showSpectrumStatus(message) {
    const statusElement = document.getElementById('spectrumStatus');
    statusElement.textContent = message;
    statusElement.classList.add('active');
}

function hideSpectrumStatus() {
    const statusElement = document.getElementById('spectrumStatus');
    statusElement.classList.remove('active');
}
