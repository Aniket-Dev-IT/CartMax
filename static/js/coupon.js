/**
 * CartMax Coupon System - AJAX Implementation
 * Handles seamless coupon application/removal from cart
 */

const CouponManager = {
    /**
     * Initialize coupon system
     */
    init: function() {
        this.setupEventListeners();
        this.loadAppliedCoupon();
    },

    /**
     * Setup event listeners for coupon actions
     */
    setupEventListeners: function() {
        // Apply coupon button
        const applyBtn = document.getElementById('apply-coupon-btn');
        if (applyBtn) {
            applyBtn.addEventListener('click', () => this.applyCoupon());
        }

        // Remove coupon button
        const removeBtn = document.getElementById('remove-coupon-btn');
        if (removeBtn) {
            removeBtn.addEventListener('click', () => this.removeCoupon());
        }

        // Coupon input field
        const couponInput = document.getElementById('coupon-code-input');
        if (couponInput) {
            // Enter key to apply
            couponInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.applyCoupon();
                }
            });

            // Real-time validation preview
            couponInput.addEventListener('blur', () => this.previewCoupon());
        }
    },

    /**
     * Apply coupon to cart
     */
    applyCoupon: function() {
        const couponInput = document.getElementById('coupon-code-input');
        if (!couponInput) return;

        const couponCode = couponInput.value.trim().toUpperCase();

        if (!couponCode) {
            this.showError('Please enter a coupon code.');
            return;
        }

        this.showLoading('Applying coupon...');

        fetch('/api/cart/apply-coupon/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: JSON.stringify({ coupon_code: couponCode })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showSuccess(data.message);
                this.updateCouponDisplay(data);
                this.updateCartTotals();
                couponInput.value = ''; // Clear input
            } else {
                this.showError(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.showError('An error occurred while applying the coupon.');
        })
        .finally(() => this.hideLoading());
    },

    /**
     * Remove coupon from cart
     */
    removeCoupon: function() {
        if (!confirm('Are you sure you want to remove this coupon?')) {
            return;
        }

        this.showLoading('Removing coupon...');

        fetch('/api/cart/remove-coupon/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showSuccess(data.message);
                this.hideCouponDisplay();
                this.updateCartTotals();
            } else {
                this.showError(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.showError('An error occurred while removing the coupon.');
        })
        .finally(() => this.hideLoading());
    },

    /**
     * Preview coupon discount without applying
     */
    previewCoupon: function() {
        const couponInput = document.getElementById('coupon-code-input');
        if (!couponInput) return;

        const couponCode = couponInput.value.trim().toUpperCase();
        if (!couponCode || couponCode.length < 3) return;

        // Get current cart total
        const subtotalEl = document.querySelector('[data-subtotal]');
        const subtotal = subtotalEl ? parseFloat(subtotalEl.textContent) : 0;
        
        const currencyEl = document.querySelector('[data-currency]');
        const currency = currencyEl ? currencyEl.textContent : 'USD';

        // Create preview element if doesn't exist
        let previewEl = document.getElementById('coupon-preview');
        if (!previewEl) {
            previewEl = document.createElement('div');
            previewEl.id = 'coupon-preview';
            previewEl.className = 'coupon-preview alert alert-info mt-2';
            couponInput.parentNode.insertBefore(previewEl, couponInput.nextSibling);
        }

        fetch(`/api/coupon/validate/?code=${couponCode}&amount=${subtotal}&currency=${currency}`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': this.getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.valid) {
                previewEl.className = 'coupon-preview alert alert-success mt-2';
                previewEl.innerHTML = `
                    <i class="fas fa-check-circle"></i>
                    <strong>${data.discount_display}</strong> - ${data.message}
                `;
                previewEl.style.display = 'block';
            } else {
                previewEl.className = 'coupon-preview alert alert-warning mt-2';
                previewEl.innerHTML = `
                    <i class="fas fa-exclamation-circle"></i>
                    ${data.message}
                `;
                previewEl.style.display = 'block';
            }
        })
        .catch(error => {
            previewEl.style.display = 'none';
        });
    },

    /**
     * Update coupon display UI
     */
    updateCouponDisplay: function(data) {
        const couponInputContainer = document.getElementById('coupon-input-container');
        const couponDisplayContainer = document.getElementById('coupon-display-container');

        if (couponInputContainer) {
            couponInputContainer.style.display = 'none';
        }

        if (couponDisplayContainer) {
            couponDisplayContainer.innerHTML = `
                <div class="alert alert-success">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>Coupon Applied:</strong> <code>${data.coupon_code}</code>
                            <br>
                            <small>You saved <strong>${data.currency_symbol}${parseFloat(data.discount_amount).toFixed(2)}</strong></small>
                        </div>
                        <button type="button" id="remove-coupon-btn" class="btn btn-sm btn-outline-danger">
                            <i class="fas fa-times"></i> Remove
                        </button>
                    </div>
                </div>
            `;
            couponDisplayContainer.style.display = 'block';

            // Re-attach remove button listener
            const removeBtn = document.getElementById('remove-coupon-btn');
            if (removeBtn) {
                removeBtn.addEventListener('click', () => this.removeCoupon());
            }
        }

        // Update cart display
        this.updateCartDisplay(data);
    },

    /**
     * Hide coupon display
     */
    hideCouponDisplay: function() {
        const couponInputContainer = document.getElementById('coupon-input-container');
        const couponDisplayContainer = document.getElementById('coupon-display-container');

        if (couponInputContainer) {
            couponInputContainer.style.display = 'block';
            const input = document.getElementById('coupon-code-input');
            if (input) input.value = '';
        }

        if (couponDisplayContainer) {
            couponDisplayContainer.style.display = 'none';
            couponDisplayContainer.innerHTML = '';
        }

        // Clear preview
        const previewEl = document.getElementById('coupon-preview');
        if (previewEl) {
            previewEl.style.display = 'none';
        }
    },

    /**
     * Update cart totals display
     */
    updateCartTotals: function() {
        fetch('/api/cart/summary/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': this.getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            this.updateCartDisplay(data);
        })
        .catch(error => console.error('Error fetching cart totals:', error));
    },

    /**
     * Update cart display with new totals
     * HARDENED: Prevents mixed currency symbols
     */
    updateCartDisplay: function(data) {
        // CRITICAL FIX: Validate currency symbol to prevent mixing ₹ and $
        let symbol = data.currency_symbol;
        
        // Fallback if missing
        if (!symbol) {
            symbol = (data.currency === 'INR' ? '₹' : '$');
        }
        
        // CRITICAL FIX: Detect and fix mixed symbols
        // If API returns "₹$" or "$₹" or any multi-character symbol, fix it
        if (symbol.length > 1) {
            console.error('CURRENCY ERROR: Mixed symbols detected!', symbol);
            symbol = (data.currency === 'INR' ? '₹' : '$');
        }
        
        // CRITICAL FIX: Validate symbol matches currency
        const expectedSymbol = (data.currency === 'INR' ? '₹' : '$');
        if (symbol !== expectedSymbol && symbol !== '₹' && symbol !== '$') {
            console.warn(
                `CURRENCY MISMATCH: Symbol "${symbol}" doesn't match ` +
                `currency "${data.currency}". Using "${expectedSymbol}"`
            );
            symbol = expectedSymbol;
        }

        // Update subtotal with validated symbol
        const subtotalEl = document.querySelector('[data-total-subtotal]');
        if (subtotalEl) {
            subtotalEl.textContent = `${symbol}${parseFloat(data.subtotal || data.original_subtotal).toFixed(2)}`;
        }

        // Show discount if applied - use SAME symbol throughout
        if (data.discount_amount > 0 || data.applied_coupon) {
            const discountEl = document.querySelector('[data-total-discount]');
            if (discountEl) {
                // CRITICAL: Always use same symbol for discount
                discountEl.textContent = `-${symbol}${parseFloat(data.discount_amount).toFixed(2)}`;
                discountEl.parentElement.style.display = 'block';
            }

            // Update discounted subtotal with SAME symbol
            const discountedEl = document.querySelector('[data-total-discounted]');
            if (discountedEl) {
                discountedEl.textContent = `${symbol}${parseFloat(data.discounted_subtotal).toFixed(2)}`;
                discountedEl.parentElement.style.display = 'block';
            }
        } else {
            // Hide discount row
            const discountEl = document.querySelector('[data-total-discount]');
            if (discountEl) {
                discountEl.parentElement.style.display = 'none';
            }

            const discountedEl = document.querySelector('[data-total-discounted]');
            if (discountedEl) {
                discountedEl.parentElement.style.display = 'none';
            }
        }

        // Update tax with SAME symbol
        const taxEl = document.querySelector('[data-total-tax]');
        if (taxEl) {
            taxEl.textContent = `${symbol}${parseFloat(data.tax).toFixed(2)}`;
        }

        // Update shipping with SAME symbol
        const shippingEl = document.querySelector('[data-total-shipping]');
        if (shippingEl) {
            shippingEl.textContent = `${symbol}${parseFloat(data.shipping).toFixed(2)}`;
        }

        // Update final total with SAME symbol
        const finalEl = document.querySelector('[data-total-final]');
        if (finalEl) {
            finalEl.textContent = `${symbol}${parseFloat(data.final_total).toFixed(2)}`;
        }
    },

    /**
     * Load applied coupon on page load
     */
    loadAppliedCoupon: function() {
        fetch('/api/cart/coupon/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': this.getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.applied) {
                const displayContainer = document.getElementById('coupon-display-container');
                if (displayContainer) {
                    displayContainer.innerHTML = `
                        <div class="alert alert-success">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>Coupon Applied:</strong> <code>${data.coupon_code}</code>
                                    <br>
                                    <small>Discount: ${data.discount_display}</small>
                                </div>
                                <button type="button" id="remove-coupon-btn" class="btn btn-sm btn-outline-danger">
                                    <i class="fas fa-times"></i> Remove
                                </button>
                            </div>
                        </div>
                    `;
                    displayContainer.style.display = 'block';

                    const inputContainer = document.getElementById('coupon-input-container');
                    if (inputContainer) {
                        inputContainer.style.display = 'none';
                    }

                    // Re-attach listener
                    const removeBtn = document.getElementById('remove-coupon-btn');
                    if (removeBtn) {
                        removeBtn.addEventListener('click', () => this.removeCoupon());
                    }
                }
            }
        })
        .catch(error => console.error('Error loading applied coupon:', error));
    },

    /**
     * Show loading state
     */
    showLoading: function(message = 'Loading...') {
        const msgEl = document.getElementById('coupon-message');
        if (msgEl) {
            msgEl.className = 'alert alert-info mt-2';
            msgEl.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${message}`;
            msgEl.style.display = 'block';
        }
    },

    /**
     * Hide loading state
     */
    hideLoading: function() {
        // Message will be replaced by success/error
    },

    /**
     * Show success message
     */
    showSuccess: function(message) {
        const msgEl = document.getElementById('coupon-message');
        if (msgEl) {
            msgEl.className = 'alert alert-success mt-2';
            msgEl.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`;
            msgEl.style.display = 'block';
            setTimeout(() => { msgEl.style.display = 'none'; }, 3000);
        }
    },

    /**
     * Show error message
     */
    showError: function(message) {
        const msgEl = document.getElementById('coupon-message');
        if (msgEl) {
            msgEl.className = 'alert alert-danger mt-2';
            msgEl.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
            msgEl.style.display = 'block';
        }
    },

    /**
     * Get CSRF token from cookies
     */
    getCookie: function(name) {
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
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    CouponManager.init();
});
