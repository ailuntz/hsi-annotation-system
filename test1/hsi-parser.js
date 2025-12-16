class HSIParser {
    constructor() {
        this.metadata = null;
        this.rawData = null;
        this.darkField = null;
        this.whiteField = null;
        this.calibratedData = null;

        this.speFile = null;
        this.bandCache = new Map();
        this.maxCacheSize = 100;
        this.onDemandMode = false;
        this.cacheHits = 0;
        this.cacheMisses = 0;

        this.lineChunkCache = new Map();
        this.lineChunkSize = 100;
        this.maxLineChunks = 3;
        this.useChunkLoading = true;
    }

    parseHeader(headerText) {
        const metadata = {};

        const singleLinePattern = /^(\w+(?:\s+\w+)*)\s*=\s*(.+)$/gm;
        let match;

        while ((match = singleLinePattern.exec(headerText)) !== null) {
            const key = match[1].trim();
            let value = match[2].trim();

            if (value.startsWith('{') && value.endsWith('}')) {
                value = value.slice(1, -1);

                if (value.includes(',')) {
                    metadata[key] = value.split(',').map(v => {
                        const num = parseFloat(v.trim());
                        return isNaN(num) ? v.trim() : num;
                    });
                } else {
                    metadata[key] = value;
                }
            } else {

                const num = parseFloat(value);
                metadata[key] = isNaN(num) ? value : num;
            }
        }

        this.metadata = metadata;
        return metadata;
    }

    setSPEFile(file) {
        this.speFile = file;
        this.onDemandMode = true;

        const fileGB = file.size / (1024 * 1024 * 1024);
        const samples = this.metadata.samples;
        const bands = this.metadata.bands;
        const bytesPerLine = samples * bands * 2;
        const linesPerGB = Math.floor((1024 * 1024 * 1024) / bytesPerLine);

        if (fileGB >= 5) {

            this.lineChunkSize = Math.max(50, linesPerGB);
            this.maxLineChunks = 2;
        } else if (fileGB >= 2) {

            this.lineChunkSize = Math.max(50, Math.floor(linesPerGB / 2));
            this.maxLineChunks = 3;
        } else {

            this.lineChunkSize = Math.max(50, Math.floor(linesPerGB / 4));
            this.maxLineChunks = 4;
        }

        const chunkSizeMB = (this.lineChunkSize * bytesPerLine) / (1024 * 1024);
        const totalChunks = Math.ceil(this.metadata.lines / this.lineChunkSize);

        console.log('On-demand mode enabled:', {
            fileName: file.name,
            fileSize: `${fileGB.toFixed(2)} GB`,
            linesPerChunk: this.lineChunkSize,
            chunkSize: `${chunkSizeMB.toFixed(0)} MB`,
            totalChunks: totalChunks,
            maxCachedChunks: this.maxLineChunks,
            estimatedMemory: `${(chunkSizeMB * this.maxLineChunks).toFixed(0)} MB`
        });
    }

    async getPointSpectrumFast(x, y) {
        if (!this.speFile || !this.metadata) {
            throw new Error('On-demand mode not initialized');
        }

        const samples = this.metadata.samples;
        const lines = this.metadata.lines;
        const bands = this.metadata.bands;

        const chunkIndex = Math.floor(x / this.lineChunkSize);

        let chunkData = this.lineChunkCache.get(chunkIndex);
        if (!chunkData) {

            chunkData = await this.loadLineChunk(chunkIndex);
        }

        const lineInChunk = x % this.lineChunkSize;
        const lineOffset = lineInChunk * bands * samples;

        const spectrumValues = new Float32Array(bands);

        for (let b = 0; b < bands; b++) {
            const bandOffset = lineOffset + b * samples;
            const rawValue = chunkData[bandOffset + y];
            spectrumValues[b] = rawValue;
        }

        return spectrumValues;
    }

    async loadLineChunk(chunkIndex) {
        const samples = this.metadata.samples;
        const lines = this.metadata.lines;
        const bands = this.metadata.bands;
        const bytesPerValue = 2;
        const bytesPerLine = samples * bands * bytesPerValue;

        const startLine = chunkIndex * this.lineChunkSize;
        const endLine = Math.min(startLine + this.lineChunkSize, lines);
        const actualLines = endLine - startLine;

        const startByte = startLine * bytesPerLine;
        const endByte = endLine * bytesPerLine;
        const chunkBytes = endByte - startByte;

        console.log(`Loading line-chunk ${chunkIndex}: lines ${startLine}-${endLine} (${(chunkBytes / 1024 / 1024).toFixed(0)} MB)`);

        const blob = this.speFile.slice(startByte, endByte);
        const arrayBuffer = await blob.arrayBuffer();
        const chunkData = new Uint16Array(arrayBuffer);

        this.lineChunkCache.set(chunkIndex, chunkData);

        if (this.lineChunkCache.size > this.maxLineChunks) {
            const firstKey = this.lineChunkCache.keys().next().value;
            this.lineChunkCache.delete(firstKey);
            console.log(`Line-chunk cache full, evicted chunk ${firstKey}. Current size: ${this.lineChunkCache.size}`);
        }

        return chunkData;
    }

    async loadBandOnDemand(bandIndex) {
        if (!this.speFile || !this.metadata) {
            throw new Error('On-demand mode not initialized');
        }

        if (this.bandCache.has(bandIndex)) {
            this.cacheHits++;

            if (this.cacheHits % 100 === 0) {
                console.log(`Band cache hits: ${this.cacheHits}, misses: ${this.cacheMisses}, hit rate: ${(this.cacheHits / (this.cacheHits + this.cacheMisses) * 100).toFixed(1)}%`);
            }
            return this.bandCache.get(bandIndex);
        }

        this.cacheMisses++;

        const samples = this.metadata.samples;
        const lines = this.metadata.lines;
        const bands = this.metadata.bands;

        if (this.useChunkLoading) {
            const bandData = new Uint16Array(samples * lines);
            const totalChunks = Math.ceil(lines / this.lineChunkSize);

            for (let chunkIdx = 0; chunkIdx < totalChunks; chunkIdx++) {

                let chunkData = this.lineChunkCache.get(chunkIdx);
                if (!chunkData) {

                    chunkData = await this.loadLineChunk(chunkIdx);
                }

                const startLine = chunkIdx * this.lineChunkSize;
                const endLine = Math.min(startLine + this.lineChunkSize, lines);
                const chunkLines = endLine - startLine;

                for (let lineInChunk = 0; lineInChunk < chunkLines; lineInChunk++) {
                    const globalLine = startLine + lineInChunk;
                    const lineOffset = lineInChunk * bands * samples;
                    const bandOffset = lineOffset + bandIndex * samples;

                    for (let sample = 0; sample < samples; sample++) {

                        bandData[sample * lines + globalLine] = chunkData[bandOffset + sample];
                    }
                }
            }

            this.bandCache.set(bandIndex, bandData);

            if (this.bandCache.size > this.maxCacheSize) {
                const removeCount = Math.floor(this.maxCacheSize * 0.2);
                const keysToRemove = Array.from(this.bandCache.keys()).slice(0, removeCount);
                keysToRemove.forEach(key => this.bandCache.delete(key));
                console.log(`Band cache full (${this.maxCacheSize}), removed ${removeCount} oldest bands. Current size: ${this.bandCache.size}`);
            }

            return bandData;

        } else {

            const bytesPerValue = 2;
            const bytesPerLine = samples * bands * bytesPerValue;
            const bytesPerBand = samples * bytesPerValue;

            const bandData = new Uint16Array(samples * lines);

            for (let line = 0; line < lines; line++) {
                const lineStart = line * bytesPerLine;
                const bandStart = lineStart + bandIndex * bytesPerBand;
                const bandEnd = bandStart + bytesPerBand;

                const blob = this.speFile.slice(bandStart, bandEnd);
                const arrayBuffer = await blob.arrayBuffer();
                const lineData = new Uint16Array(arrayBuffer);

                for (let sample = 0; sample < samples; sample++) {
                    bandData[sample * lines + line] = lineData[sample];
                }
            }

            this.bandCache.set(bandIndex, bandData);

            if (this.bandCache.size > this.maxCacheSize) {
                const removeCount = Math.floor(this.maxCacheSize * 0.2);
                const keysToRemove = Array.from(this.bandCache.keys()).slice(0, removeCount);
                keysToRemove.forEach(key => this.bandCache.delete(key));
                console.log(`Cache full (${this.maxCacheSize}), removed ${removeCount} oldest bands. Current size: ${this.bandCache.size}`);
            }

            return bandData;
        }
    }

    async parseSPE(arrayBuffer, file = null) {
        const samples = this.metadata.samples;
        const lines = this.metadata.lines;
        const bands = this.metadata.bands;
        const dataType = this.metadata['data type'];

        if (!samples || !lines || !bands) {
            throw new Error('Invalid metadata: missing dimensions');
        }

        if (dataType !== 12) {
            console.warn(`Unexpected data type: ${dataType}, assuming uint16`);
        }

        this.rawData = null;
        this.calibratedData = null;
        this.onDemandMode = false;
        this.bandCache.clear();
        this.lineChunkCache.clear();
        this.cacheHits = 0;
        this.cacheMisses = 0;

        if (file && file.size > 500 * 1024 * 1024) {
            const sizeGB = (file.size / 1024 / 1024 / 1024).toFixed(2);
            console.log(`Large file detected (${sizeGB} GB), using on-demand loading mode`);
            this.setSPEFile(file);

            this.rawData = null;
            return {
                samples,
                lines,
                bands,
                onDemandMode: true
            };
        }

        console.log('Parsing SPE file (full load):', {
            samples,
            lines,
            bands,
            arrayBufferByteLength: arrayBuffer.byteLength,
            arrayBufferByteOffset: arrayBuffer.byteOffset || 0
        });

        if (arrayBuffer.byteLength % 2 !== 0) {
            throw new Error(`Invalid ArrayBuffer length: ${arrayBuffer.byteLength} is not a multiple of 2`);
        }

        let uint16Array;
        try {

            if (arrayBuffer.byteOffset && arrayBuffer.byteOffset > 0) {
                console.log('ArrayBuffer has byteOffset, creating new buffer...');
                const newBuffer = arrayBuffer.slice(0);
                uint16Array = new Uint16Array(newBuffer);
            } else {
                uint16Array = new Uint16Array(arrayBuffer);
            }
        } catch (error) {
            console.error('Error creating Uint16Array:', error);
            throw new Error(`Failed to create Uint16Array: ${error.message}. ArrayBuffer size: ${arrayBuffer.byteLength} bytes (${(arrayBuffer.byteLength / 1024 / 1024 / 1024).toFixed(2)} GB)`);
        }

        const expectedSize = samples * lines * bands;
        console.log('Data validation:', {
            expectedSize,
            actualSize: uint16Array.length,
            match: uint16Array.length === expectedSize
        });

        if (uint16Array.length < expectedSize) {
            throw new Error(`Data size mismatch: expected ${expectedSize}, got ${uint16Array.length}`);
        }

        this.rawData = uint16Array;

        console.log('SPE file parsed successfully (full mode)');

        return {
            samples,
            lines,
            bands,
            data: uint16Array
        };
    }

    async parseCalibrationFile(arrayBuffer, type) {
        console.log(`Parsing calibration file (${type}):`, {
            byteLength: arrayBuffer.byteLength,
            isEven: arrayBuffer.byteLength % 2 === 0
        });

        if (arrayBuffer.byteLength % 2 !== 0) {
            console.warn(`Calibration file has odd byte length: ${arrayBuffer.byteLength}, trimming last byte`);

            arrayBuffer = arrayBuffer.slice(0, arrayBuffer.byteLength - 1);
        }

        const uint16Array = new Uint16Array(arrayBuffer);

        if (type === 'dark') {
            this.darkField = uint16Array;
            console.log('Dark field loaded:', uint16Array.length, 'values');
        } else if (type === 'white') {
            this.whiteField = uint16Array;
            console.log('White field loaded:', uint16Array.length, 'values');
        }

        return uint16Array;
    }

    getBandData(bandIndex) {
        if (!this.rawData || !this.metadata) {
            throw new Error('No data loaded');
        }

        const samples = this.metadata.samples;
        const lines = this.metadata.lines;
        const bands = this.metadata.bands;

        if (bandIndex < 0 || bandIndex >= bands) {
            throw new Error(`Invalid band index: ${bandIndex}`);
        }

        const bandData = new Uint16Array(samples * lines);

        for (let line = 0; line < lines; line++) {
            const lineOffset = line * bands * samples;
            for (let sample = 0; sample < samples; sample++) {
                const pixelOffset = lineOffset + bandIndex * samples + sample;

                bandData[sample * lines + line] = this.rawData[pixelOffset];
            }
        }

        return bandData;
    }

    applyCalibration(useDark = false, useWhite = false) {
        if (!this.rawData || !this.metadata) {
            throw new Error('No data loaded');
        }

        const samples = this.metadata.samples;
        const lines = this.metadata.lines;
        const bands = this.metadata.bands;
        const totalPixels = samples * lines * bands;

        if (!useDark && !useWhite) {
            this.calibratedData = null;
            return;
        }

        this.calibratedData = new Float32Array(totalPixels);

        const darkIsSpectral = this.darkField && this.darkField.length === bands;
        const whiteIsSpectral = this.whiteField && this.whiteField.length === bands;

        for (let i = 0; i < totalPixels; i++) {
            let value = this.rawData[i];

            const band = i % bands;

            if (useDark && this.darkField) {
                const darkValue = darkIsSpectral ? this.darkField[band] : this.darkField[i];
                value = Math.max(0, value - darkValue);
            }

            if (useWhite && this.whiteField) {
                const whiteValue = whiteIsSpectral ? this.whiteField[band] : this.whiteField[i];
                const darkValue = (useDark && this.darkField) ?
                    (darkIsSpectral ? this.darkField[band] : this.darkField[i]) : 0;

                const denominator = whiteValue - darkValue;
                if (denominator > 0) {
                    value = value / denominator;
                }
            }

            this.calibratedData[i] = value;
        }
    }

    async getBandDataCalibrated(bandIndex) {

        if (this.onDemandMode && this.speFile) {
            console.log(`Using on-demand mode for band ${bandIndex}`);
            return await this.loadBandOnDemand(bandIndex);
        }

        const dataSource = this.calibratedData || this.rawData;

        if (!dataSource || !this.metadata) {
            throw new Error('No data loaded');
        }

        const samples = this.metadata.samples;
        const lines = this.metadata.lines;
        const bands = this.metadata.bands;

        if (bandIndex < 0 || bandIndex >= bands) {
            throw new Error(`Invalid band index: ${bandIndex}`);
        }

        const bandData = new Float32Array(samples * lines);

        for (let line = 0; line < lines; line++) {
            const lineOffset = line * bands * samples;
            for (let sample = 0; sample < samples; sample++) {
                const pixelOffset = lineOffset + bandIndex * samples + sample;

                bandData[sample * lines + line] = dataSource[pixelOffset];
            }
        }

        return bandData;
    }

    getWavelength(bandIndex) {
        if (!this.metadata || !this.metadata.wavelength) {
            return null;
        }
        return this.metadata.wavelength[bandIndex];
    }

    getWavelengths() {
        if (!this.metadata || !this.metadata.wavelength) {
            return [];
        }
        return this.metadata.wavelength;
    }

    getDimensions() {
        if (!this.metadata) {
            return null;
        }
        return {
            samples: this.metadata.samples,
            lines: this.metadata.lines,
            bands: this.metadata.bands
        };
    }
}
