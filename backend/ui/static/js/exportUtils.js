function exportTableToExcel(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;

    if (typeof XLSX === 'undefined') {
        console.warn("XLSX library not loaded. Falling back to CSV.");
        return exportTableToCSV(tableId, filename);
    }

    try {
        const wb = XLSX.utils.table_to_book(table, {sheet: "Sheet1"});
        XLSX.writeFile(wb, filename + '.xlsx');
    } catch (e) {
        console.error("Error exporting to Excel:", e);
        exportTableToCSV(tableId, filename); // Fallback
    }
}

function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;

    let csv = [];
    const rows = table.querySelectorAll('tr');

    for (let i = 0; i < rows.length; i++) {
        let row = [], cols = rows[i].querySelectorAll('td, th');

        for (let j = 0; j < cols.length; j++) {
            let data = cols[j].innerText.replace(/(\r\n|\n|\r)/gm, '').replace(/(\s\s)/gm, ' ');
            // Explicitly remove all variations of sorting arrows/junk characters that might exist
            data = data.replace(/[▼▲↕]/g, '').replace(/[\u25B2\u25BC\u2195]/g, '').trim();
            data = data.replace(/"/g, '""');
            row.push('"' + data + '"');
        }

        if (row.length > 0) {
            csv.push(row.join(','));
        }
    }

    const csvFile = new Blob([csv.join('\n')], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    downloadLink.download = filename + '.csv';
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

function exportChartDataToExcel(chartInstance, filename) {
    if (!chartInstance) {
        alert("Chart is not loaded or data is empty.");
        return;
    }

    // Handle Chart.js instances vs ECharts instances
    let isChartJS = typeof chartInstance.config !== 'undefined';
    let isECharts = typeof chartInstance.getOption === 'function';

    if (!isChartJS && !isECharts) {
        alert("Unsupported chart type.");
        return;
    }

    let dataArray = [];
    let headers = ['Date'];
    let seriesNames = [];
    let seriesData = [];
    let xAxisData = [];

    if (isECharts) {
        const option = chartInstance.getOption();
        if (!option) { alert("Error reading chart option"); return; }

        let yAxisObj = Array.isArray(option.yAxis) ? option.yAxis[0] : option.yAxis;
        let xAxisObj = Array.isArray(option.xAxis) ? option.xAxis[0] : option.xAxis;

        const isHorizontal = yAxisObj && yAxisObj.type === 'category' && yAxisObj.data;

        if (isHorizontal) {
            headers = ['Category'];
        }

        if (isHorizontal) {
            xAxisData = yAxisObj.data;
        } else if (xAxisObj && xAxisObj.data) {
            xAxisData = xAxisObj.data;
        } else if (option.dataset && option.dataset.length > 0 && option.dataset[0].source) {
            const src = option.dataset[0].source;
            if (Array.isArray(src) && src.length > 0) {
                xAxisData = src.slice(1).map(row => row[0]);
            }
        }

        if (option.series && option.series.length > 0) {
            option.series.forEach(s => {
                if (s.name) seriesNames.push(s.name);
                else seriesNames.push('Series');

                if (s.data && s.data.length > 0) {
                    seriesData.push(s.data);
                } else if (option.dataset && option.dataset.length > 0 && option.dataset[0].source) {
                    // Handled below
                } else {
                    seriesData.push([]);
                }
            });
        }

        if (seriesData.length > 0 && seriesData[0].length === 0 && option.dataset && option.dataset.length > 0 && option.dataset[0].source) {
            const src = option.dataset[0].source;
            if (Array.isArray(src) && src.length > 0) {
                for (let col = 1; col < src[0].length; col++) {
                    seriesNames[col - 1] = src[0][col] || `Series_${col}`;
                    let colData = [];
                    for (let r = 1; r < src.length; r++) {
                        colData.push(src[r][col]);
                    }
                    seriesData[col - 1] = colData;
                }
            }
        } else if (seriesData.length === 0 || (seriesData.length > 0 && seriesData[0].length === 0)) {
            if (option.series && option.series.some(s => s.data && s.data.length > 0)) {
                // Proceed
            } else {
                alert("No series data found in chart");
                return;
            }
        }
    } else if (isChartJS) {
        const data = chartInstance.data;
        if (!data || !data.datasets || data.datasets.length === 0) return;

        xAxisData = data.labels || [];

        data.datasets.forEach(s => {
            if (s.label) seriesNames.push(s.label);
            else seriesNames.push('Series');
            seriesData.push(s.data || []);
        });
    }

    // Build headers from series names
    seriesNames.forEach(name => {
        headers.push(name);
    });

    dataArray.push(headers);

    // Build rows
    const len = xAxisData.length > 0 ? xAxisData.length : (seriesData[0] ? seriesData[0].length : 0);

    for (let i = 0; i < len; i++) {
        let row = [];
        if (xAxisData.length > 0) {
            row.push(xAxisData[i]);
        } else {
            row.push(`Row_${i}`);
        }

        seriesData.forEach(d => {
            let val = '';
            if (d && d[i] !== undefined) {
                if (typeof d[i] === 'object' && d[i] !== null) {
                    if (d[i].value !== undefined) {
                        val = d[i].value;
                    } else if (Array.isArray(d[i])) {
                        val = d[i].join('|');
                    }
                } else {
                    val = d[i];
                }
            }
            row.push(val);
        });

        dataArray.push(row);
    }

    if (typeof XLSX !== 'undefined') {
        try {
            const ws = XLSX.utils.aoa_to_sheet(dataArray);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, "Chart Data");
            XLSX.writeFile(wb, filename + '.xlsx');
            return;
        } catch (e) {
            console.error("Error exporting to Excel:", e);
        }
    }

    console.warn("XLSX library not loaded or failed. Falling back to CSV.");
    let csvRows = dataArray.map(row => row.map(v => `"${String(v).replace(/"/g, '""')}"`).join(","));
    const csvFile = new Blob([csvRows.join('\n')], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    downloadLink.download = filename + '.csv';
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

function exportChartDataToCSV(chartInstance, filename) {
    if (!chartInstance) {
        alert("Chart is not loaded or data is empty.");
        return;
    }

    // Handle Chart.js instances vs ECharts instances
    let isChartJS = typeof chartInstance.config !== 'undefined';
    let isECharts = typeof chartInstance.getOption === 'function';

    if (!isChartJS && !isECharts) {
        alert("Unsupported chart type.");
        return;
    }

    let csvRows = [];
    let headers = ['Date'];
    let seriesNames = [];
    let seriesData = [];
    let xAxisData = [];

    if (isECharts) {
        const option = chartInstance.getOption();
        if (!option) { alert("Error reading chart option"); return; }

        // ECharts Horizontal Bar charts store categories in yAxis
        // Need to check both yAxis array or single object format
        let yAxisObj = Array.isArray(option.yAxis) ? option.yAxis[0] : option.yAxis;
        let xAxisObj = Array.isArray(option.xAxis) ? option.xAxis[0] : option.xAxis;

        const isHorizontal = yAxisObj && yAxisObj.type === 'category' && yAxisObj.data;

        if (isHorizontal) {
            headers = ['Category'];
        }

        // Find xAxis data
        if (isHorizontal) {
            xAxisData = yAxisObj.data;
        } else if (xAxisObj && xAxisObj.data) {
            xAxisData = xAxisObj.data;
        } else if (option.dataset && option.dataset.length > 0 && option.dataset[0].source) {
            // dataset fallback
            const src = option.dataset[0].source;
            if (Array.isArray(src) && src.length > 0) {
                // assume first row is headers, first col is dates
                xAxisData = src.slice(1).map(row => row[0]);
            }
        }

        if (option.series && option.series.length > 0) {
            option.series.forEach(s => {
                if (s.name) seriesNames.push(s.name);
                else seriesNames.push('Series');
                // Some charts might put data in dataset instead of directly in series
                if (s.data && s.data.length > 0) {
                    seriesData.push(s.data);
                } else if (option.dataset && option.dataset.length > 0 && option.dataset[0].source) {
                    // Handled below, we'll wait for the dataset fallback
                } else {
                    seriesData.push([]);
                }
            });
        }

        // If series data is empty but we have a dataset source
        if (seriesData.length > 0 && seriesData[0].length === 0 && option.dataset && option.dataset.length > 0 && option.dataset[0].source) {
            const src = option.dataset[0].source;
            if (Array.isArray(src) && src.length > 0) {
                // src[0] is headers, ignore [0][0] which is date
                for (let col = 1; col < src[0].length; col++) {
                    seriesNames[col - 1] = src[0][col] || `Series_${col}`;
                    let colData = [];
                    for (let r = 1; r < src.length; r++) {
                        colData.push(src[r][col]);
                    }
                    seriesData[col - 1] = colData;
                }
            }
        } else if (seriesData.length === 0 || (seriesData.length > 0 && seriesData[0].length === 0)) {
            // Check if there is data inside options.series regardless
            if (option.series && option.series.some(s => s.data && s.data.length > 0)) {
                // Proceed, data was successfully pushed
            } else {
                alert("No series data found in chart");
                return;
            }
        }
    } else if (isChartJS) {
        const data = chartInstance.data;
        if (!data || !data.datasets || data.datasets.length === 0) return;

        xAxisData = data.labels || [];

        data.datasets.forEach(s => {
            if (s.label) seriesNames.push(s.label);
            else seriesNames.push('Series');
            seriesData.push(s.data || []);
        });
    }

    // Build headers from series names
    seriesNames.forEach(name => {
        headers.push(`"${name}"`);
    });

    csvRows.push(headers.join(','));

    // Build rows
    const len = xAxisData.length > 0 ? xAxisData.length : (seriesData[0] ? seriesData[0].length : 0);

    for (let i = 0; i < len; i++) {
        let row = [];
        if (xAxisData.length > 0) {
            row.push(`"${xAxisData[i]}"`);
        } else {
            row.push(`"Row_${i}"`);
        }

        seriesData.forEach(d => {
            let val = '';
            if (d && d[i] !== undefined) {
                // Handle objects if data is complex (like candlesticks)
                if (typeof d[i] === 'object' && d[i] !== null) {
                    if (d[i].value !== undefined) {
                        val = d[i].value;
                    } else if (Array.isArray(d[i])) {
                        // For Candlesticks [open, close, min, max] or [date, val1, val2]
                        val = d[i].join('|');
                    }
                } else {
                    val = d[i];
                }
            }
            row.push(`"${val}"`);
        });

        csvRows.push(row.join(','));
    }

    const csvFile = new Blob([csvRows.join('\n')], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    downloadLink.download = filename + '.csv';
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}
