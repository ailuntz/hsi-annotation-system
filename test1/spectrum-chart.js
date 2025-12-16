class SpectrumChart {
    constructor(canvas) {
        this.canvas = canvas;
        this.chart = null;
        this.currentData = null;
    }

    initialize() {
        const ctx = this.canvas.getContext('2d');

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 300
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Spectral Curve',
                        font: {
                            size: 16
                        }
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            title: function(context) {
                                return `Wavelength: ${context[0].label} nm`;
                            },
                            label: function(context) {
                                return `Intensity: ${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Wavelength (nm)'
                        },
                        ticks: {
                            maxTicksLimit: 20
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Intensity'
                        },
                        beginAtZero: false
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });

        console.log('Spectrum chart initialized');
    }

    renderSpectrum(wavelengths, values, label = 'Spectrum', color = 'rgb(147, 51, 234)') {
        if (!this.chart) {
            this.initialize();
        }

        this.currentData = { wavelengths, values, label, color };

        this.chart.data.labels = wavelengths.map(wl => wl.toFixed(2));
        this.chart.data.datasets = [{
            label: label,
            data: values,
            borderColor: color,
            backgroundColor: color.replace('rgb', 'rgba').replace(')', ', 0.1)'),
            borderWidth: 2,
            pointRadius: 0,
            pointHoverRadius: 4,
            tension: 0.1
        }];

        this.chart.update();
    }

    smoothData(data, windowSize = 5) {
        const result = [];
        const halfWindow = Math.floor(windowSize / 2);

        for (let i = 0; i < data.length; i++) {
            const start = Math.max(0, i - halfWindow);
            const end = Math.min(data.length, i + halfWindow + 1);
            const window = data.slice(start, end);
            const sum = window.reduce((a, b) => a + b, 0);
            result.push(sum / window.length);
        }

        return result;
    }

    updateSmoothing(smooth) {
        if (!this.currentData) return;

        const { wavelengths, values, label } = this.currentData;
        const displayValues = smooth ? this.smoothData(values, 5) : values;

        this.renderSpectrum(
            wavelengths,
            displayValues,
            label + (smooth ? ' (Smoothed)' : ''),
            'rgb(147, 51, 234)'
        );
    }

    clear() {
        if (!this.chart) return;

        this.chart.data.labels = [];
        this.chart.data.datasets = [];
        this.chart.update();
        this.currentData = null;
    }

    showLoading(progress = 0) {
        if (!this.chart) {
            this.initialize();
        }

        this.chart.options.plugins.title.text = `Loading Spectrum... ${Math.round(progress)}%`;
        this.chart.update('none');
    }

    renderPartial(wavelengths, values, label = 'Spectrum (Loading...)', totalBands) {
        if (!this.chart) {
            this.initialize();
        }

        const progress = Math.round((wavelengths.length / totalBands) * 100);

        this.chart.options.plugins.title.text = `Spectral Curve - Loading ${progress}%`;
        this.chart.data.labels = wavelengths.map(wl => wl.toFixed(2));
        this.chart.data.datasets = [{
            label: label,
            data: values,
            borderColor: 'rgb(147, 51, 234)',
            backgroundColor: 'rgba(147, 51, 234, 0.1)',
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.1
        }];

        this.chart.update('none');
    }

    finalize() {
        if (!this.chart) return;
        this.chart.options.plugins.title.text = 'Spectral Curve';
        this.chart.update('none');
    }

    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }
}
