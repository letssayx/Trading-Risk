// Layout Manager
// Handles resizable splitters and panel resizing logic.

document.addEventListener('DOMContentLoaded', () => {
    initSplitter('split-main', 'left-group', 'center-group', 'horizontal');
    initSplitter('split-center', 'chart-panel', 'workbook-panel', 'vertical');

    // Internal splitter for left group (Toolbox vs Edge)
    // Allows resizing the Toolbox when it is open.
    initSplitter('split-left-internal', 'toolbox-panel', 'edge-panel', 'horizontal');
});

function initSplitter(splitterId, el1Id, el2Id, direction) {
    const splitter = document.getElementById(splitterId);
    const el1 = document.getElementById(el1Id);
    const el2 = document.getElementById(el2Id);

    if (!splitter || !el1 || !el2) return;

    let isDragging = false;

    splitter.addEventListener('mousedown', (e) => {
        isDragging = true;
        document.body.style.cursor = direction === 'horizontal' ? 'col-resize' : 'row-resize';
        e.preventDefault(); // Prevent text selection
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;

        if (direction === 'horizontal') {
            // Resize width
            // Calculate new width for el1 based on mouse X
            const containerOffset = el1.parentElement.getBoundingClientRect().left;
            const newWidth = e.clientX - containerOffset;

            if (newWidth > 50 && newWidth < (el1.parentElement.clientWidth - 50)) {
                el1.style.width = newWidth + 'px';
                // el2 takes remaining space via flex
            }
        } else {
            // Resize height (Vertical Splitter in column layout)
            // Actually split-center separates top and bottom
            // e.clientY relative to container top
            const containerTop = el1.parentElement.getBoundingClientRect().top;
            const newHeight = e.clientY - containerTop;

            if (newHeight > 50 && newHeight < (el1.parentElement.clientHeight - 50)) {
                el1.style.height = newHeight + 'px';
                // el2 needs to adjust if it's flex:1 or height calc
                // In flex col, if el1 has fixed height, el2 (flex:1) adjusts.
                // So setting el1 height is sufficient if el2 is flex:1.
                // BUT, workbook-panel was set to height: 50% initially.
                // We should ensure el1.style.flex = 'none' and el2.style.flex = '1'
                el1.style.flex = 'none';
                // el2.style.height = 'calc(100% - ' + newHeight + 'px)';
            }
        }
    });

    document.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            document.body.style.cursor = 'default';
            // Trigger resize for charts
            window.dispatchEvent(new Event('resize'));
        }
    });
}
