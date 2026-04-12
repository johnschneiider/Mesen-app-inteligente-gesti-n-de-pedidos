/**
 * utils.js — Utilidades globales de Mesenú
 */

// Formato de moneda COP
function formatCOP(value) {
    return '$' + parseInt(value).toLocaleString('es-CO');
}

// Toast global
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('toast-visible'), 10);
    setTimeout(() => {
        toast.classList.remove('toast-visible');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// HTMX global config
document.addEventListener('DOMContentLoaded', () => {
    // Show loading state during HTMX requests
    document.body.addEventListener('htmx:beforeRequest', (e) => {
        const btn = e.detail.elt;
        if (btn.tagName === 'BUTTON' || btn.tagName === 'FORM') {
            btn.classList.add('loading');
        }
    });
    document.body.addEventListener('htmx:afterRequest', (e) => {
        const btn = e.detail.elt;
        btn.classList.remove('loading');
    });
});

// Alpine.js component: styled file upload zone
function fileUpload() {
    return {
        fileName: '',
        previewUrl: '',
        pick(event) {
            const file = event.target.files[0];
            if (!file) return;
            this.fileName = file.name;
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => { this.previewUrl = e.target.result; };
                reader.readAsDataURL(file);
            }
        }
    };
}
