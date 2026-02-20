// Enhanced Modal Handling
class UploadModal {
    constructor(modalId) {
        this.modal = document.getElementById(modalId);
        if (!this.modal) return;

        this.closeBtn = this.modal.querySelector('.close');
        this.cancelBtn = this.modal.querySelector('.btn-cancel'); // Assuming cancel class

        this._bindEvents();
    }

    _bindEvents() {
        // Scoped close button
        if (this.closeBtn) {
            this.closeBtn.onclick = () => this.close();
        }

        // Scoped cancel button
        if (this.cancelBtn) {
            this.cancelBtn.onclick = () => this.close();
        }

        // Click outside to close
        window.onclick = (event) => {
            if (event.target == this.modal) {
                this.close();
            }
        };

        // ESC Key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.style.display === 'block') {
                this.close();
            }
        });
    }

    open() {
        this.modal.style.display = 'block';
    }

    close() {
        this.modal.style.display = 'none';
    }
}

// Instantiate specific modals
window.bhavcopyUploadModal = new UploadModal('upload-bhavcopy-modal');

// Example for other modals if they exist
// window.otherModal = new UploadModal('other-modal');
