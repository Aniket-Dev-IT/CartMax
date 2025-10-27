// CartMax Product Comparison Functionality
console.log('CartMax Comparison: Starting initialization...');

document.addEventListener('DOMContentLoaded', function() {
    console.log('CartMax Comparison: DOM loaded, initializing...');
    
    // CSRF token setup for AJAX requests
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    const csrftoken = getCookie('csrftoken');
    
    // Add product to comparison
    function addToComparison(productId) {
        fetch(`/comparison/add/${productId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast(data.message, 'success');
                updateComparisonCount(data.comparison_count);
                updateComparisonButton(productId, true);
            } else {
                showToast(data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error adding to comparison:', error);
            showToast('Failed to add product to comparison. Please try again.', 'error');
        });
    }
    
    // Remove product from comparison
    function removeFromComparison(productId) {
        fetch(`/comparison/remove/${productId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast(data.message, 'success');
                updateComparisonCount(data.comparison_count);
                updateComparisonButton(productId, false);
                
                // Remove item from comparison page if we're on it
                const comparisonItem = document.querySelector(`[data-comparison-item="${productId}"]`);
                if (comparisonItem) {
                    comparisonItem.remove();
                    // Reload page if no items left
                    if (data.comparison_count === 0) {
                        location.reload();
                    }
                }
            } else {
                showToast(data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error removing from comparison:', error);
            showToast('Failed to remove product from comparison. Please try again.', 'error');
        });
    }
    
    // Clear all comparison items
    function clearComparison() {
        if (!confirm('Are you sure you want to clear all items from comparison?')) {
            return;
        }
        
        fetch('/comparison/clear/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast(data.message, 'success');
                updateComparisonCount(0);
                
                // Clear all comparison buttons
                document.querySelectorAll('.comparison-btn').forEach(btn => {
                    updateComparisonButton(btn.dataset.productId, false);
                });
                
                // Reload comparison page if we're on it
                if (window.location.pathname.includes('/comparison/')) {
                    location.reload();
                }
            } else {
                showToast(data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error clearing comparison:', error);
            showToast('Failed to clear comparison. Please try again.', 'error');
        });
    }
    
    // Update comparison count in navbar/header
    function updateComparisonCount(count) {
        const countElements = document.querySelectorAll('.comparison-count');
        countElements.forEach(element => {
            element.textContent = count;
            if (count > 0) {
                element.style.display = 'inline';
            } else {
                element.style.display = 'none';
            }
        });
    }
    
    // Update comparison button state
    function updateComparisonButton(productId, inComparison) {
        const buttons = document.querySelectorAll(`[data-product-id="${productId}"][title*="Compare"]`);
        buttons.forEach(button => {
            if (inComparison) {
                button.classList.add('btn-warning', 'active');
                button.classList.remove('btn-light');
                button.title = 'Remove from comparison';
                button.innerHTML = '<i class="fas fa-balance-scale"></i>';
            } else {
                button.classList.remove('btn-warning', 'active');
                button.classList.add('btn-light');
                button.title = 'Compare';
                button.innerHTML = '<i class="fas fa-balance-scale"></i>';
            }
        });
    }
    
    // Show toast notifications
    function showToast(message, type = 'success') {
        // Use existing CartMax toast function if available
        if (window.CartMax && window.CartMax.showToast) {
            window.CartMax.showToast(message, type);
            return;
        }
        
        // Fallback toast implementation
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        // Create toast container if it doesn't exist
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = toastContainer.lastElementChild;
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        // Remove from DOM after hiding
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });
    }
    
    // Event listeners for comparison buttons
    document.addEventListener('click', function(event) {
        console.log('CartMax Comparison: Click detected on:', event.target);
        
        const target = event.target.closest('[title*="Compare"], .comparison-btn');
        if (!target) {
            // Log for debugging - remove in production
            if (event.target.tagName === 'BUTTON' || event.target.closest('button')) {
                console.log('CartMax Comparison: Button clicked but not a comparison button');
            }
            return;
        }
        
        console.log('CartMax Comparison: Comparison button clicked:', target);
        event.preventDefault();
        
        const productId = target.dataset.productId;
        if (!productId) {
            console.error('CartMax Comparison: No product ID found on button:', target);
            return;
        }
        
        console.log('CartMax Comparison: Product ID:', productId);
        
        const isInComparison = target.classList.contains('active') || target.classList.contains('btn-warning');
        
        if (isInComparison) {
            console.log('CartMax Comparison: Removing from comparison...');
            removeFromComparison(productId);
        } else {
            console.log('CartMax Comparison: Adding to comparison...');
            addToComparison(productId);
        }
    });
    
    // Event listener for clear comparison button
    document.addEventListener('click', function(event) {
        if (event.target.closest('[onclick*="clearComparison"]') || 
            event.target.closest('.clear-comparison-btn')) {
            event.preventDefault();
            clearComparison();
        }
    });
    
    // Global function to clear comparison (for inline onclick handlers)
    window.clearComparison = clearComparison;
    window.removeFromComparison = function(productId) {
        removeFromComparison(productId);
    };
    
    // Add to global CartMax object if it exists
    if (window.CartMax) {
        window.CartMax.addToComparison = addToComparison;
        window.CartMax.removeFromComparison = removeFromComparison;
        window.CartMax.clearComparison = clearComparison;
    } else {
        // Create CartMax object if it doesn't exist
        window.CartMax = {
            addToComparison: addToComparison,
            removeFromComparison: removeFromComparison,
            clearComparison: clearComparison,
            showToast: showToast
        };
    }
    
    // Initialize comparison state on page load
    function initializeComparisonState() {
        // Check which products are already in comparison
        // This would typically be done by checking session data or making an API call
        // For now, we'll rely on the backend to mark buttons appropriately
        
        // Update comparison count from any existing badges
        const comparisonBadge = document.querySelector('.comparison-count');
        if (comparisonBadge && comparisonBadge.textContent) {
            const count = parseInt(comparisonBadge.textContent);
            updateComparisonCount(count);
        }
    }
    
    // Initialize on page load
    console.log('CartMax Comparison: Initializing state...');
    initializeComparisonState();
    
    // Check if buttons exist
    const buttons = document.querySelectorAll('[title*="Compare"], .comparison-btn');
    console.log(`CartMax Comparison: Found ${buttons.length} comparison buttons on page`);
    
    if (buttons.length === 0) {
        console.warn('CartMax Comparison: No comparison buttons found on this page');
    }
    
    console.log('CartMax Comparison: Initialization complete!');
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        // Ctrl+Shift+C to clear comparison
        if (event.ctrlKey && event.shiftKey && event.code === 'KeyC') {
            event.preventDefault();
            clearComparison();
        }
    });
    
    // Update comparison buttons based on current state
    function refreshComparisonButtons() {
        // This function can be called to refresh all comparison button states
        // Useful after page navigation or state changes
        fetch('/comparison/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const comparisonItems = doc.querySelectorAll('[data-comparison-item]');
            
            // Reset all buttons
            document.querySelectorAll('[title*="Compare"]').forEach(btn => {
                updateComparisonButton(btn.dataset.productId, false);
            });
            
            // Mark buttons for products in comparison
            comparisonItems.forEach(item => {
                const productId = item.dataset.comparisonItem;
                updateComparisonButton(productId, true);
            });
            
            // Update count
            updateComparisonCount(comparisonItems.length);
        })
        .catch(error => {
            console.error('Error refreshing comparison state:', error);
        });
    }
    
    // Expose refresh function globally
    window.refreshComparisonButtons = refreshComparisonButtons;
});
