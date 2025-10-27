/**
 * Modern Toast Notification System
 * Usage: showToast(message, type, title)
 * Types: 'success', 'error', 'warning', 'info'
 */

(function() {
    'use strict';

    // Icons for each toast type
    const TOAST_ICONS = {
        success: '✓',
        error: '×',
        warning: '⚠',
        info: 'ℹ'
    };

    /**
     * Get or create toast container
     */
    function getToastContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        return container;
    }

    /**
     * Show a toast notification
     * @param {string} message - The notification message
     * @param {string} type - Type of notification: 'success', 'error', 'warning', 'info'
     * @param {string} title - Optional title (not used in admin style)
     */
    window.showToast = function(message, type = 'info', title = '') {
        // Validate type
        if (!['success', 'error', 'warning', 'info'].includes(type)) {
            type = 'info';
        }

        const container = getToastContainer();

        // Create toast element
        const toast = document.createElement('div');
        toast.className = `modern-toast ${type}`;

        // Build toast HTML - Admin style exact match
        const icon = TOAST_ICONS[type] || 'ℹ';
        const toastTitle = type.charAt(0).toUpperCase() + type.slice(1);
        toast.innerHTML = `
            <div class="toast-icon">${icon}</div>
            <div class="toast-content">
                <div class="toast-title">${toastTitle}</div>
                <p class="toast-message">${escapeHtml(message)}</p>
            </div>
            <button class="toast-close" aria-label="Close notification" title="Close">
                ×
            </button>
        `;

        // Add to container
        container.appendChild(toast);

        // Trigger animation
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);

        // Close button handler
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', function() {
            closeToast(toast);
        });

        // Auto-hide after 6 seconds
        const autoHideTimeout = setTimeout(() => {
            closeToast(toast);
        }, 6000);

        // Store timeout for manual close to clear it
        toast.dataset.timeout = autoHideTimeout;

        return toast;
    };

    /**
     * Close a toast notification
     */
    function closeToast(toast) {
        if (!toast) return;

        // Clear auto-hide timeout if exists
        if (toast.dataset.timeout) {
            clearTimeout(toast.dataset.timeout);
        }

        // Trigger hide animation
        toast.classList.remove('show');
        toast.classList.add('hide');

        // Remove from DOM after animation completes
        setTimeout(() => {
            if (toast.parentElement) {
                toast.parentElement.removeChild(toast);
            }
        }, 300);
    }

    /**
     * Escape HTML special characters to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Process Django messages on page load
     */
    document.addEventListener('DOMContentLoaded', function() {
        // Check for Django messages
        const messageElements = document.querySelectorAll('[data-message]');
        
        messageElements.forEach(element => {
            const message = element.getAttribute('data-message');
            const type = element.getAttribute('data-message-type') || 'info';
            const title = element.getAttribute('data-message-title') || '';

            if (message) {
                showToast(message, type, title);
            }
        });

        // Also check for Django message framework messages if they're rendered
        const djangoMessages = document.querySelectorAll('.django-message');
        djangoMessages.forEach(msg => {
            const message = msg.textContent.trim();
            const classes = msg.className;
            
            let type = 'info';
            if (classes.includes('success')) type = 'success';
            else if (classes.includes('error') || classes.includes('danger')) type = 'error';
            else if (classes.includes('warning')) type = 'warning';
            else if (classes.includes('info')) type = 'info';

            if (message) {
                showToast(message, type);
            }

            // Hide the original message div
            msg.style.display = 'none';
        });
    });

    // Make closeToast available globally if needed
    window.closeToast = closeToast;
})();
