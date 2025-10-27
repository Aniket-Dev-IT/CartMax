// CartMax Enhanced Admin JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all admin enhancements
    initPricingCalculators();
    initCharacterCounters();
    initStockAlerts();
    initFormValidations();
    initBulkActions();
    initSmartPricing();
});

// Pricing Calculator Functions
function initPricingCalculators() {
    const quickDiscountField = document.querySelector('#id_quick_discount_percent');
    const priceField = document.querySelector('#id_price');
    const originalPriceField = document.querySelector('#id_original_price');
    
    if (quickDiscountField && priceField) {
        quickDiscountField.addEventListener('input', function() {
            calculateQuickDiscount();
        });
        
        // Add real-time price validation
        priceField.addEventListener('blur', validatePrice);
        originalPriceField?.addEventListener('blur', validatePriceRelation);
    }
}

function calculateQuickDiscount() {
    const discountPercent = parseFloat(document.querySelector('#id_quick_discount_percent').value);
    const originalPrice = parseFloat(document.querySelector('#id_original_price').value);
    const currentPrice = parseFloat(document.querySelector('#id_price').value);
    
    if (discountPercent && discountPercent > 0) {
        let basePrice = originalPrice || currentPrice;
        
        if (basePrice) {
            const discountMultiplier = 1 - (discountPercent / 100);
            const newPrice = (basePrice * discountMultiplier).toFixed(2);
            
            // Update price field
            document.querySelector('#id_price').value = newPrice;
            
            // Set original price if not already set
            if (!originalPrice && currentPrice) {
                document.querySelector('#id_original_price').value = currentPrice.toFixed(2);
            }
            
            // Show calculation preview
            showDiscountPreview(basePrice, newPrice, discountPercent);
        }
    }
}

function showDiscountPreview(originalPrice, newPrice, discountPercent) {
    // Use the modern toast notification system
    const message = `Discount Preview: ₹${originalPrice} → ₹${newPrice} (${discountPercent}% off, Save ₹${(originalPrice - newPrice).toFixed(2)})`;
    if (typeof showToast === 'function') {
        showToast(message, 'success');
    } else {
        console.log(`[SUCCESS] ${message}`);
    }
}

function validatePrice() {
    const priceField = document.querySelector('#id_price');
    const price = parseFloat(priceField.value);
    
    if (price <= 0) {
        showFieldError(priceField, 'Price must be greater than 0');
        return false;
    }
    
    clearFieldError(priceField);
    return true;
}

function validatePriceRelation() {
    const priceField = document.querySelector('#id_price');
    const originalPriceField = document.querySelector('#id_original_price');
    
    const price = parseFloat(priceField.value);
    const originalPrice = parseFloat(originalPriceField.value);
    
    if (originalPrice && price && originalPrice <= price) {
        showFieldError(originalPriceField, 'Original price must be higher than current price');
        return false;
    }
    
    clearFieldError(originalPriceField);
    return true;
}

// Character Counter Functions
function initCharacterCounters() {
    const fields = [
        { id: '#id_description', max: 2000 },
        { id: '#id_short_description', max: 300 },
        { id: '#id_meta_title', max: 200 },
        { id: '#id_meta_description', max: 160 }
    ];
    
    fields.forEach(field => {
        const element = document.querySelector(field.id);
        if (element) {
            addCharacterCounter(element, field.max);
        }
    });
}

function addCharacterCounter(field, maxLength) {
    const counter = document.createElement('div');
    counter.className = 'char-counter';
    field.parentNode.appendChild(counter);
    
    function updateCounter() {
        const current = field.value.length;
        const remaining = maxLength - current;
        counter.textContent = `${current}/${maxLength} characters`;
        
        if (remaining < 20) {
            counter.className = 'char-counter danger';
        } else if (remaining < 50) {
            counter.className = 'char-counter warning';
        } else {
            counter.className = 'char-counter';
        }
    }
    
    field.addEventListener('input', updateCounter);
    updateCounter(); // Initial count
}

// Stock Alert Functions
function initStockAlerts() {
    const stockField = document.querySelector('#id_stock');
    const lowStockField = document.querySelector('#id_low_stock_alert');
    
    if (stockField) {
        stockField.addEventListener('input', function() {
            updateStockStatus();
            validateStockAlert();
        });
        
        updateStockStatus(); // Initial status
    }
    
    if (lowStockField) {
        lowStockField.addEventListener('input', validateStockAlert);
    }
}

function updateStockStatus() {
    const stockField = document.querySelector('#id_stock');
    const stock = parseInt(stockField.value) || 0;
    
    // Remove existing classes
    stockField.classList.remove('stock-alert-low', 'stock-alert-critical');
    
    if (stock === 0) {
        stockField.classList.add('stock-alert-critical');
        showStockAlert('Out of Stock!', 'error');
    } else if (stock <= 5) {
        stockField.classList.add('stock-alert-critical');
        showStockAlert('Critical Stock Level!', 'warning');
    } else if (stock <= 10) {
        stockField.classList.add('stock-alert-low');
        showStockAlert('Low Stock', 'warning');
    }
}

function validateStockAlert() {
    const stockField = document.querySelector('#id_stock');
    const lowStockField = document.querySelector('#id_low_stock_alert');
    
    if (!stockField || !lowStockField) return true;
    
    const stock = parseInt(stockField.value) || 0;
    const lowStockAlert = parseInt(lowStockField.value) || 0;
    
    if (lowStockAlert > stock) {
        showFieldError(lowStockField, 'Alert threshold cannot be higher than current stock');
        return false;
    }
    
    clearFieldError(lowStockField);
    return true;
}

function showStockAlert(message, type) {
    // Use the modern toast notification system
    if (typeof showToast === 'function') {
        showToast(message, type);
    } else {
        // Fallback: log to console if showToast is not available
        console.log(`[STOCK ALERT ${type.toUpperCase()}] ${message}`);
    }
}

// Form Validation Functions
function initFormValidations() {
    const form = document.querySelector('.admin-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
                scrollToFirstError();
            }
        });
    }
}

function validateForm() {
    let isValid = true;
    
    // Validate price fields
    if (!validatePrice()) isValid = false;
    if (!validatePriceRelation()) isValid = false;
    if (!validateStockAlert()) isValid = false;
    
    return isValid;
}

function scrollToFirstError() {
    const firstError = document.querySelector('.field-error');
    if (firstError) {
        firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// Utility Functions
function showFieldError(field, message) {
    clearFieldError(field);
    
    // Use modern toast notification
    if (typeof showToast === 'function') {
        showToast(message, 'error');
    } else {
        console.error(`[ERROR] ${message}`);
    }
    
    // Also highlight the field visually
    field.classList.add('error');
}

function clearFieldError(field) {
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    field.classList.remove('error');
}

// Bulk Actions Functions
function initBulkActions() {
    // Price update type switcher
    const updateTypeRadios = document.querySelectorAll('input[name="update_type"]');
    updateTypeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            updateBulkPriceHelperText(this.value);
        });
    });
    
    // Bulk action form submission with loading
    const bulkForms = document.querySelectorAll('.bulk-action-form form');
    bulkForms.forEach(form => {
        form.addEventListener('submit', function() {
            showLoadingOverlay();
        });
    });
}

function updateBulkPriceHelperText(updateType) {
    const valueField = document.querySelector('#id_value');
    if (!valueField) return;
    
    const helpTexts = {
        'percentage': 'Enter percentage change (e.g., 10 for 10% increase, -5 for 5% decrease)',
        'fixed': 'Enter fixed amount to add/subtract (e.g., 100 for +₹100, -50 for -₹50)',
        'set': 'Enter exact price to set for all products (e.g., 999.99)'
    };
    
    const helpText = valueField.parentNode.querySelector('.help-text');
    if (helpText) {
        helpText.textContent = helpTexts[updateType];
    }
    
    // Update placeholder
    const placeholders = {
        'percentage': 'e.g., 10 or -5',
        'fixed': 'e.g., 100 or -50',
        'set': 'e.g., 999.99'
    };
    
    valueField.placeholder = placeholders[updateType];
}

function showLoadingOverlay() {
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = '<div class="spinner"></div>';
    document.body.appendChild(overlay);
}

// Smart Pricing Functions
function initSmartPricing() {
    const analysisTypeSelect = document.querySelector('#id_analysis_type');
    if (analysisTypeSelect) {
        analysisTypeSelect.addEventListener('change', function() {
            updateSmartPricingOptions(this.value);
        });
    }
    
    // Initialize pricing recommendation cards
    const recommendationCards = document.querySelectorAll('.pricing-analysis-card');
    recommendationCards.forEach(card => {
        addRecommendationActions(card);
    });
}

function updateSmartPricingOptions(analysisType) {
    const descriptions = {
        'competitive': 'Compare your prices with similar products in the same category',
        'margin': 'Analyze profit margins and suggest optimal pricing for better profitability',
        'demand': 'Price products based on demand patterns and sales velocity',
        'seasonal': 'Adjust prices based on seasonal trends and market patterns'
    };
    
    // Update description
    const description = document.querySelector('.analysis-description');
    if (description) {
        description.textContent = descriptions[analysisType];
    }
}

function addRecommendationActions(card) {
    // Add quick action buttons to pricing recommendations
    const actions = document.createElement('div');
    actions.className = 'recommendation-actions';
    actions.innerHTML = `
        <button type="button" class="admin-action-btn success" onclick="acceptRecommendation(this)">
            Accept Recommendation
        </button>
        <button type="button" class="admin-action-btn" onclick="reviewRecommendation(this)">
            Review Details
        </button>
    `;
    
    card.appendChild(actions);
}

function acceptRecommendation(button) {
    // Implementation for accepting pricing recommendations
    button.textContent = 'Accepted ✓';
    button.disabled = true;
    button.classList.remove('success');
    button.classList.add('secondary');
    
    showNotification('Pricing recommendation accepted', 'success');
}

function reviewRecommendation(button) {
    // Implementation for reviewing recommendation details
    const card = button.closest('.pricing-analysis-card');
    const details = card.querySelector('.recommendation-details');
    
    if (details) {
        details.style.display = details.style.display === 'none' ? 'block' : 'none';
        button.textContent = details.style.display === 'none' ? 'Review Details' : 'Hide Details';
    }
}

// Notification System - Delegate to modern toast notifications
function showNotification(message, type = 'info') {
    // Use the modern toast notification system
    if (typeof showToast === 'function') {
        showToast(message, type);
    } else {
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
}

// Currency Selection Handler
function handleCurrencyChange() {
    const currencySelect = document.querySelector('#id_price_currency');
    if (currencySelect) {
        currencySelect.addEventListener('change', function() {
            updateCurrencySymbols(this.value);
        });
        
        // Initialize with current selection
        updateCurrencySymbols(currencySelect.value);
    }
}

function updateCurrencySymbols(currency) {
    const symbols = {
        'INR': '₹',
        'USD': '$'
    };
    
    const symbol = symbols[currency] || '₹';
    
    // Update all currency symbols in the interface
    const currencySymbols = document.querySelectorAll('.currency-symbol');
    currencySymbols.forEach(element => {
        element.textContent = symbol;
    });
    
    // Update help texts
    const helpTexts = document.querySelectorAll('.currency-help-text');
    helpTexts.forEach(text => {
        text.textContent = text.textContent.replace(/[₹$]/, symbol);
    });
}

// Initialize currency handler
document.addEventListener('DOMContentLoaded', function() {
    handleCurrencyChange();
});