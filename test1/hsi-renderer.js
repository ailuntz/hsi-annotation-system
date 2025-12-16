class HSIRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.parser = null;
        this.algorithm = 'percentile-gamma';
    }

    setParser(parser) {
        this.parser = parser;
    }

    setAlgorithm(algorithm) {
        this.algorithm = algorithm;
    }

    calculatePercentile(data, percentile) {

        const sorted = new Float32Array(data);
        sorted.sort();

        const index = Math.floor(sorted.length * percentile / 100);
        return sorted[Math.min(index, sorted.length - 1)];
    }

    buildHistogram(data, bins = 256) {
        const histogram = new Array(bins).fill(0);
        const min = this.getStats(data).min;
        const max = this.getStats(data).max;
        const range = max - min;

        for (let i = 0; i < data.length; i++) {
            const bin = Math.min(Math.floor(((data[i] - min) / range) * (bins - 1)), bins - 1);
            histogram[bin]++;
        }

        return histogram;
    }

    applyStretch(value, stats, gain, algorithm) {

        const exponent = gain / 4096;

        const gainFactor = Math.pow(4096, exponent);

        let result;

        switch (algorithm) {
            case 'raw':

                result = this.normalize(value, stats.min, stats.max);
                result = result * gainFactor;
                break;

            case 'linear':

                result = this.normalize(value, stats.min, stats.max);
                result = result * gainFactor;
                break;

            case 'percentile':

                result = this.normalize(value, stats.p2, stats.p98);
                result = result * gainFactor;
                break;

            case 'gamma':

                const gamma = Math.pow(10, -exponent);
                result = this.normalize(value, stats.min, stats.max);
                result = Math.pow(result / 255, gamma) * 255;
                break;

            case 'percentile-gamma':

                const gammaVal = Math.pow(10, -exponent * 0.5);
                result = this.normalize(value, stats.p2, stats.p98);
                result = Math.pow(result / 255, gammaVal) * 255;
                break;

            case 'log':

                const normalized = (value - stats.min) / (stats.max - stats.min);
                result = (Math.log(normalized * (Math.E - 1) + 1)) * 255;
                result = result * gainFactor;
                break;

            case 'histogram':

                const bin = Math.min(
                    Math.floor(((value - stats.min) / (stats.max - stats.min)) * 255),
                    255
                );
                result = stats.cdf[bin] * 255;
                result = result * gainFactor;
                break;

            default:
                result = this.normalize(value, stats.min, stats.max);
                result = result * gainFactor;
        }

        return result;
    }

    async renderFalseColor(rBand, gBand, bBand, rGain, gGain, bGain) {
        if (!this.parser) {
            throw new Error('Parser not set');
        }

        const dims = this.parser.getDimensions();
        if (!dims) {
            throw new Error('No data loaded');
        }

        const { samples: height, lines: width } = dims;

        this.canvas.width = width;
        this.canvas.height = height;

        console.log(`Extracting band data: R=${rBand}, G=${gBand}, B=${bBand}`);
        const rData = await this.parser.getBandDataCalibrated(rBand);
        const gData = await this.parser.getBandDataCalibrated(gBand);
        const bData = await this.parser.getBandDataCalibrated(bBand);

        const rStats = this.getStats(rData);
        const gStats = this.getStats(gData);
        const bStats = this.getStats(bData);

        console.log('Channel statistics:', { rStats, gStats, bStats });

        const imageData = this.ctx.createImageData(width, height);
        const pixels = imageData.data;

        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const idx = y * width + x;
                const pixelIdx = idx * 4;

                let r = this.applyStretch(rData[idx], rStats, rGain, this.algorithm);
                let g = this.applyStretch(gData[idx], gStats, gGain, this.algorithm);
                let b = this.applyStretch(bData[idx], bStats, bGain, this.algorithm);

                pixels[pixelIdx] = Math.min(255, Math.max(0, r));
                pixels[pixelIdx + 1] = Math.min(255, Math.max(0, g));
                pixels[pixelIdx + 2] = Math.min(255, Math.max(0, b));
                pixels[pixelIdx + 3] = 255;
            }
        }

        this.ctx.putImageData(imageData, 0, 0);

        console.log('Rendering complete');
    }

    normalize(value, min, max) {
        if (max === min) return 0;
        return ((value - min) / (max - min)) * 255;
    }

    getStats(data) {
        let min = Infinity;
        let max = -Infinity;
        let sum = 0;

        for (let i = 0; i < data.length; i++) {
            const val = data[i];
            if (val < min) min = val;
            if (val > max) max = val;
            sum += val;
        }

        const p2 = this.calculatePercentile(data, 2);
        const p98 = this.calculatePercentile(data, 98);

        const histogram = new Array(256).fill(0);
        const range = max - min;

        for (let i = 0; i < data.length; i++) {
            const bin = Math.min(Math.floor(((data[i] - min) / range) * 255), 255);
            histogram[bin]++;
        }

        const cdf = new Array(256);
        cdf[0] = histogram[0] / data.length;
        for (let i = 1; i < 256; i++) {
            cdf[i] = cdf[i - 1] + (histogram[i] / data.length);
        }

        return {
            min,
            max,
            mean: sum / data.length,
            p2,
            p98,
            histogram,
            cdf
        };
    }

    clear() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }

    async renderFalseColorProgressive(rBand, gBand, bBand, rGain, gGain, bGain, onProgress) {
        if (!this.parser) {
            throw new Error('Parser not set');
        }

        const dims = this.parser.getDimensions();
        if (!dims) {
            throw new Error('No data loaded');
        }

        const { samples: height, lines: width } = dims;

        this.canvas.width = width;
        this.canvas.height = height;

        if (onProgress) onProgress(0, 'Extracting R channel...');
        const rData = await this.parser.getBandDataCalibrated(rBand);

        if (onProgress) onProgress(20, 'Extracting G channel...');
        const gData = await this.parser.getBandDataCalibrated(gBand);

        if (onProgress) onProgress(40, 'Extracting B channel...');
        const bData = await this.parser.getBandDataCalibrated(bBand);

        if (onProgress) onProgress(60, 'Calculating statistics...');
        const rStats = this.getStats(rData);
        const gStats = this.getStats(gData);
        const bStats = this.getStats(bData);

        if (onProgress) onProgress(70, 'Generating image...');
        const imageData = this.ctx.createImageData(width, height);
        const pixels = imageData.data;

        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const idx = y * width + x;
                const pixelIdx = idx * 4;

                let r = this.applyStretch(rData[idx], rStats, rGain, this.algorithm);
                let g = this.applyStretch(gData[idx], gStats, gGain, this.algorithm);
                let b = this.applyStretch(bData[idx], bStats, bGain, this.algorithm);

                pixels[pixelIdx] = Math.min(255, Math.max(0, r));
                pixels[pixelIdx + 1] = Math.min(255, Math.max(0, g));
                pixels[pixelIdx + 2] = Math.min(255, Math.max(0, b));
                pixels[pixelIdx + 3] = 255;
            }

            if (y % Math.floor(height / 10) === 0) {
                const progress = 70 + ((y / height) * 25);
                if (onProgress) onProgress(progress, `Rendering... ${Math.floor((y / height) * 100)}%`);
                await new Promise(resolve => setTimeout(resolve, 0));
            }
        }

        if (onProgress) onProgress(95, 'Finalizing...');
        this.ctx.putImageData(imageData, 0, 0);

        if (onProgress) onProgress(100, 'Complete!');
    }
}
