class WorkbenchManager {
    constructor() {
        this.workbenches = [];
        this.activeWorkbenchId = null;
        this.loadFromStorage();
        this.initSync();
    }

    initSync() {
        this.channel = new BroadcastChannel('workbench_sync');
        this.channel.onmessage = (event) => {
            if (event.data.type === 'UPDATE_WORKBENCH') {
                this.updateLocalState(event.data.workbench);
            }
        };
    }

    loadFromStorage() {
        const saved = localStorage.getItem('turtle_workbenches');
        if (saved) {
            this.workbenches = JSON.parse(saved);
        } else {
            // Create Default
            this.createWorkbench('Default Workspace', true);
        }
    }

    saveToStorage() {
        localStorage.setItem('turtle_workbenches', JSON.stringify(this.workbenches));
    }

    createWorkbench(name, isDefault = false) {
        const workbench = {
            id: `wb_${Date.now()}`,
            name: name,
            isDefault: isDefault,
            layout: {
                leftWidth: '300px',
                rightWidth: '400px',
                bottomHeight: '250px'
            },
            tabs: ['strategy', 'python', 'jules']
        };

        this.workbenches.push(workbench);
        this.activeWorkbenchId = workbench.id;
        this.saveToStorage();
        return workbench;
    }

    getActiveWorkbench() {
        return this.workbenches.find(w => w.id === this.activeWorkbenchId) || this.workbenches[0];
    }

    updateLayout(layoutData) {
        const wb = this.getActiveWorkbench();
        if (wb) {
            wb.layout = { ...wb.layout, ...layoutData };
            this.saveToStorage();
            // Broadcast Change
            this.channel.postMessage({ type: 'UPDATE_WORKBENCH', workbench: wb });
        }
    }

    updateLocalState(updatedWb) {
        const index = this.workbenches.findIndex(w => w.id === updatedWb.id);
        if (index !== -1) {
            this.workbenches[index] = updatedWb;
            this.saveToStorage();
            console.log(`Synced Workbench: ${updatedWb.name}`);
        }
    }

    spawnNewWindow(workbenchId) {
        const workbench = this.workbenches.find(w => w.id === workbenchId);
        if (!workbench) return;

        const features = 'width=1200,height=800,menubar=no,toolbar=no';
        window.open(`/workbench?wb=${workbenchId}`, workbench.name, features);
    }
}

// Attach to Window
window.wbManager = new WorkbenchManager();
