const Layout = {
    init: function() {
        this.initResizers();
    },

    initResizers: function() {
        // Vertical Resizer (Left Panel)
        const leftPanel = document.getElementById('left-panel');
        const resizerLeft = document.getElementById('resizer-left');

        if (resizerLeft) {
            resizerLeft.addEventListener('mousedown', (e) => {
                e.preventDefault();
                document.addEventListener('mousemove', resizeLeft);
                document.addEventListener('mouseup', stopResizeLeft);
            });

            function resizeLeft(e) {
                leftPanel.style.width = e.clientX - 50 + 'px'; // Minus toolbox width
            }
            function stopResizeLeft() {
                document.removeEventListener('mousemove', resizeLeft);
                document.removeEventListener('mouseup', stopResizeLeft);
            }
        }

        // Horizontal Resizer (Charts vs Workbook)
        const chartBox = document.getElementById('chart-workbench');
        const resizerCharts = document.getElementById('resizer-charts');

        if (resizerCharts) {
            resizerCharts.addEventListener('mousedown', (e) => {
                e.preventDefault();
                document.addEventListener('mousemove', resizeHeight);
                document.addEventListener('mouseup', stopResizeHeight);
            });

            function resizeHeight(e) {
                // e.clientY is relative to viewport.
                // We need relative to main-panel, but main-panel starts at top.
                // Chart box height is effectively e.clientY.
                chartBox.style.height = e.clientY + 'px';

                // Notify charts to resize
                if (window.ChartTabs) ChartTabs.resizeAll();
            }
            function stopResizeHeight() {
                document.removeEventListener('mousemove', resizeHeight);
                document.removeEventListener('mouseup', stopResizeHeight);
            }
        }
    }
};
