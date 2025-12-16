// @ts-nocheck
export default class SpectrumExtractor {
    constructor(parser) {
        this.parser = parser;
        this.dimensions = null;
        this.spectrumCache = new Map();
        this.maxCacheSize = 20;
    }

    setParser(parser) {
        this.parser = parser;
        this.dimensions = parser.getDimensions();
        this.spectrumCache.clear();
    }

    async getPointSpectrum(x, y) {
        if (!this.parser || !this.dimensions) {
            throw new Error('Parser not initialized');
        }

        const cacheKey = `point_${x}_${y}`;

        if (this.spectrumCache.has(cacheKey)) {
            console.log(`Spectrum cache hit: ${cacheKey}`);
            return this.spectrumCache.get(cacheKey);
        }

        const wavelengths = this.parser.getWavelengths();
        let values = [];

        const { samples: height, lines: width } = this.dimensions;
        const pixelIdx = x * height + y;

        console.log(`Extracting spectrum for point (${x}, ${y}), pixel index: ${pixelIdx}`);

        if (this.parser.onDemandMode && this.parser.getPointSpectrumFast) {
            console.log(`Using fast chunk-based extraction (1 chunk load for all ${wavelengths.length} bands)`);
            const spectrumValues = await this.parser.getPointSpectrumFast(x, y);
            values = Array.from(spectrumValues);
        } else {

            for (let bandIdx = 0; bandIdx < wavelengths.length; bandIdx++) {
                const bandData = await this.parser.getBandDataCalibrated(bandIdx);
                values.push(bandData[pixelIdx]);
            }
        }

        const spectrum = { wavelengths, values };

        this.addToCache(cacheKey, spectrum);

        return spectrum;
    }

    async getRegionSpectrum(pixels, onProgress = null) {
        if (!this.parser || !this.dimensions) {
            throw new Error('Parser not initialized');
        }

        if (!pixels || pixels.length === 0) {
            throw new Error('No pixels provided');
        }

        const cacheKey = this.generateRegionCacheKey(pixels);

        if (this.spectrumCache.has(cacheKey)) {
            console.log(`Spectrum cache hit: region with ${pixels.length} pixels`);
            return this.spectrumCache.get(cacheKey);
        }

        const wavelengths = this.parser.getWavelengths();
        const avgValues = [];

        const { samples: height, lines: width } = this.dimensions;

        console.log(`Extracting spectrum for region with ${pixels.length} pixels`);

        if (this.parser.onDemandMode && this.parser.getPointSpectrumFast) {
            const sums = new Float64Array(wavelengths.length);
            for (let idx = 0; idx < pixels.length; idx++) {
                const [x, y] = pixels[idx];
                const spectrumValues = await this.parser.getPointSpectrumFast(x, y);
                for (let band = 0; band < spectrumValues.length; band++) {
                    sums[band] += spectrumValues[band];
                }
                if (onProgress && idx % 25 === 0) {
                    const progress = ((idx + 1) / pixels.length) * 100;
                    onProgress(progress);
                }
            }
            const spectrum = {
                wavelengths,
                values: Array.from(sums, sum => sum / pixels.length),
            };
            this.addToCache(cacheKey, spectrum);
            return spectrum;
        }

        for (let bandIdx = 0; bandIdx < wavelengths.length; bandIdx++) {
            const bandData = await this.parser.getBandDataCalibrated(bandIdx);

            let sum = 0;
            for (const [x, y] of pixels) {
                const pixelIdx = x * height + y;
                sum += bandData[pixelIdx];
            }
            avgValues.push(sum / pixels.length);

            if (onProgress && bandIdx % 10 === 0) {
                const progress = ((bandIdx + 1) / wavelengths.length) * 100;
                onProgress(progress);
            }
        }

        const spectrum = { wavelengths, values: avgValues };

        this.addToCache(cacheKey, spectrum);

        return spectrum;
    }

    getPixelsInRectangle(annotation) {
        const [[x1, y1], [x2, y2]] = annotation.coor;
        const minX = Math.min(x1, x2);
        const maxX = Math.max(x1, x2);
        const minY = Math.min(y1, y2);
        const maxY = Math.max(y1, y2);

        const pixels = [];
        for (let x = minX; x <= maxX; x++) {
            for (let y = minY; y <= maxY; y++) {
                pixels.push([x, y]);
            }
        }

        return this.samplePixels(pixels);
    }

    getPixelsInPolygon(annotation) {
        const polygon = annotation.coor;

        const xs = polygon.map(p => p[0]);
        const ys = polygon.map(p => p[1]);
        const minX = Math.min(...xs);
        const maxX = Math.max(...xs);
        const minY = Math.min(...ys);
        const maxY = Math.max(...ys);

        const pixels = [];

        for (let x = minX; x <= maxX; x++) {
            for (let y = minY; y <= maxY; y++) {
                if (this.isPointInPolygon([x, y], polygon)) {
                    pixels.push([x, y]);
                }
            }
        }

        return this.samplePixels(pixels);
    }

    getPixelsInCircle(annotation) {
        const [cx, cy] = annotation.coor;
        const radius = annotation.radius;

        const pixels = [];

        const minX = Math.floor(cx - radius);
        const maxX = Math.ceil(cx + radius);
        const minY = Math.floor(cy - radius);
        const maxY = Math.ceil(cy + radius);

        for (let x = minX; x <= maxX; x++) {
            for (let y = minY; y <= maxY; y++) {
                const dx = x - cx;
                const dy = y - cy;
                if (dx * dx + dy * dy <= radius * radius) {
                    pixels.push([x, y]);
                }
            }
        }

        return this.samplePixels(pixels);
    }

    isPointInPolygon(point, polygon) {
        const [x, y] = point;
        let inside = false;

        for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
            const [xi, yi] = polygon[i];
            const [xj, yj] = polygon[j];

            const intersect = ((yi > y) !== (yj > y)) &&
                (x < (xj - xi) * (y - yi) / (yj - yi) + xi);

            if (intersect) inside = !inside;
        }

        return inside;
    }

    samplePixels(pixels, maxSamples = 1000) {
        if (pixels.length <= maxSamples) {
            return pixels;
        }

        console.log(`Sampling ${maxSamples} pixels from ${pixels.length} total pixels`);

        const step = Math.floor(pixels.length / maxSamples);
        return pixels.filter((_, idx) => idx % step === 0).slice(0, maxSamples);
    }

    generateRegionCacheKey(pixels) {

        if (pixels.length === 0) return 'empty';
        if (pixels.length === 1) return `point_${pixels[0][0]}_${pixels[0][1]}`;

        const first = pixels[0];
        const last = pixels[pixels.length - 1];
        const middle = pixels[Math.floor(pixels.length / 2)];

        return `region_${first[0]}_${first[1]}_${middle[0]}_${middle[1]}_${last[0]}_${last[1]}_${pixels.length}`;
    }

    addToCache(key, spectrum) {
        if (this.spectrumCache.size >= this.maxCacheSize) {

            const firstKey = this.spectrumCache.keys().next().value;
            this.spectrumCache.delete(firstKey);
            console.log(`Cache full, removed: ${firstKey}`);
        }

        this.spectrumCache.set(key, spectrum);
        console.log(`Cached spectrum: ${key} (cache size: ${this.spectrumCache.size})`);
    }

    clearCache() {
        this.spectrumCache.clear();
        console.log('Spectrum cache cleared');
    }

    async getAnnotationSpectrum(annotation, onProgress = null) {
        let pixels;

        switch (annotation.type) {
            case 1:
                pixels = this.getPixelsInRectangle(annotation);
                break;

            case 2:
                pixels = this.getPixelsInPolygon(annotation);
                break;

            case 3:
                return await this.getPointSpectrum(annotation.coor[0], annotation.coor[1]);

            case 5:
                pixels = this.getPixelsInCircle(annotation);
                break;

            default:
                throw new Error(`Unknown annotation type: ${annotation.type}`);
        }

        console.log(`Annotation "${annotation.label}" has ${pixels.length} pixels`);
        return await this.getRegionSpectrum(pixels, onProgress);
    }
}
