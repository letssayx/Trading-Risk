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

        if (option.dataset && option.dataset.length > 0 && option.dataset[0].source) {
            const src = option.dataset[0].source;
            if (Array.isArray(src) && src.length > 0) {
                for (let col = 1; col < src[0].length; col++) {
                    seriesNames.push(src[0][col] || `Series_${col}`);
                    let colData = [];
                    for (let r = 1; r < src.length; r++) {
                        colData.push(src[r][col]);
                    }
                    seriesData.push(colData);
                }
            }
        } else if (option.series && option.series.length > 0) {
            option.series.forEach(s => {
                if (s.name && (s.name.includes('Placeholder') || s.name.includes('Background'))) return;

                if (s.name) seriesNames.push(s.name);
                else seriesNames.push('Series');
                seriesData.push(s.data || []);
            });
        } else {
            alert("No series data found in chart");
            return;
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

    seriesNames.forEach(name => {
        headers.push(name);
    });

    dataArray.push(headers);

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
            let item = d ? d[i] : undefined;
            if (item !== undefined && item !== null) {
                if (typeof item === 'object' && !Array.isArray(item)) {
                    if (item.value !== undefined) {
                        if (Array.isArray(item.value)) {
                            val = item.value.length > 1 ? item.value[1] : item.value[0];
                        } else {
                            val = item.value;
                        }
                    } else {
                        val = JSON.stringify(item);
                    }
                } else if (Array.isArray(item)) {
                    val = item.length > 1 ? item[1] : item[0];
                } else {
                    val = item;
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

        if (option.dataset && option.dataset.length > 0 && option.dataset[0].source) {
            // ECharts using dataset mapping (like the Smart Money Net Pos charts)
            const src = option.dataset[0].source;
            if (Array.isArray(src) && src.length > 0) {
                // src[0] is headers, ignore [0][0] which is date
                for (let col = 1; col < src[0].length; col++) {
                    seriesNames.push(src[0][col] || `Series_${col}`);
                    let colData = [];
                    for (let r = 1; r < src.length; r++) {
                        colData.push(src[r][col]);
                    }
                    seriesData.push(colData);
                }
            }
        } else if (option.series && option.series.length > 0) {
            // Traditional ECharts using explicit series data arrays
            option.series.forEach(s => {
                // Skip placeholder/background series if their name implies it
                if (s.name && (s.name.includes('Placeholder') || s.name.includes('Background'))) return;

                if (s.name) seriesNames.push(s.name);
                else seriesNames.push('Series');
                // Some charts might put data in dataset instead of directly in series
                seriesData.push(s.data || []);
            });
        } else {
            alert("No series data found in chart");
            return;
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
            let item = d ? d[i] : undefined;
            if (item !== undefined && item !== null) {
                // Handle objects if data is complex (like candlesticks or ECharts objects)
                if (typeof item === 'object' && !Array.isArray(item)) {
                    if (item.value !== undefined) {
                        if (Array.isArray(item.value)) {
                            // ECharts format for some series: [xAxis, yAxis]
                            val = item.value.length > 1 ? item.value[1] : item.value[0];
                        } else {
                            val = item.value;
                        }
                    } else {
                        // generic fallback
                        val = JSON.stringify(item);
                    }
                } else if (Array.isArray(item)) {
                    // For Candlesticks [open, close, min, max] or [date, val1, val2]
                    val = item.join(' | ');
                } else {
                    val = item;
                }
            }

            // Format string specifically to escape quotes for CSV
            if (typeof val === 'string') {
                val = val.replace(/"/g, '""');
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
