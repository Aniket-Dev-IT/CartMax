// CartMax Currency Converter System
// Allows users to switch between USD ($) and INR (₹) with real-time conversion

console.log('💱 CartMax Currency Converter: Loading...');

// Currency conversion rates (you can update these or fetch from API)
const CURRENCY_RATES = {
    USD_TO_INR: 83.25,  // 1 USD = 83.25 INR (approximate current rate)
    INR_TO_USD: 0.012   // 1 INR = 0.012 USD
};

// Current currency setting (default to INR for Indian market)
let currentCurrency = localStorage.getItem('cartmax_currency') || 'INR';

// Currency symbols
const CURRENCY_SYMBOLS = {
    'USD': '$',
    'INR': '₹'
};

class CurrencyConverter {
    constructor() {
        this.init();
    }
    
    init() {
        console.log(`💱 Currency Converter initialized. Current: ${currentCurrency}`);
        this.addCurrencySelector();
        // this.convertAllPrices(); // DISABLED - using smart pricing
        this.setupEventListeners();
    }
    
    addCurrencySelector() {
        // Add currency selector to navbar if it doesn't exist
        const navbar = document.querySelector('.nav-items, .navbar-nav');
        if (!navbar || document.querySelector('#currencySelector')) return;
        
        const currencySelector = document.createElement('div');
        currencySelector.className = 'dropdown currency-selector ms-2';
        currencySelector.innerHTML = `
            <button class="btn btn-outline-primary btn-sm dropdown-toggle" type="button" id="currencySelector" data-bs-toggle="dropdown" aria-expanded="false">
                <i class="fas fa-exchange-alt me-1"></i>
                <span id="currentCurrencyDisplay">${CURRENCY_SYMBOLS[currentCurrency]} ${currentCurrency}</span>
            </button>
            <ul class="dropdown-menu" aria-labelledby="currencySelector">
                <li><a class="dropdown-item currency-option" href="#" data-currency="USD">
                    <i class="fas fa-dollar-sign me-2"></i>USD ($) - US Dollar</a></li>
                <li><a class="dropdown-item currency-option" href="#" data-currency="INR">
                    <i class="fas fa-rupee-sign me-2"></i>INR (₹) - Indian Rupee</a></li>
            </ul>
        `;
        
        navbar.appendChild(currencySelector);
    }
    
    setupEventListeners() {
        // Currency selection
        document.addEventListener('click', (event) => {
            const currencyOption = event.target.closest('.currency-option');
            if (currencyOption) {
                event.preventDefault();
                const newCurrency = currencyOption.getAttribute('data-currency');
                this.changeCurrency(newCurrency);
            }
        });
    }
    
    changeCurrency(newCurrency) {
        if (newCurrency === currentCurrency) return;
        
        console.log(`💱 Changing currency from ${currentCurrency} to ${newCurrency}`);
        
        const oldCurrency = currentCurrency;
        currentCurrency = newCurrency;
        
        // Save to localStorage
        localStorage.setItem('cartmax_currency', currentCurrency);
        
        // Update display
        const displayElement = document.querySelector('#currentCurrencyDisplay');
        if (displayElement) {
            displayElement.textContent = `${CURRENCY_SYMBOLS[currentCurrency]} ${currentCurrency}`;
        }
        
        // Convert all prices on the page
        this.convertAllPrices();
        
        // Dispatch custom event for cart to listen
        const event = new CustomEvent('currencyChanged', {
            detail: {
                currency: {
                    symbol: CURRENCY_SYMBOLS[currentCurrency],
                    code: currentCurrency
                },
                oldCurrency: oldCurrency
            }
        });
        document.dispatchEvent(event);
        
        // Show conversion notification
        this.showConversionNotification(oldCurrency, newCurrency);
    }
    
    convertAllPrices() {
        // DISABLED: Prices are now managed by smart pricing system
        // No automatic conversion to prevent corruption of competitive prices
        console.log('💱 Price conversion disabled - using smart pricing system');
        return;
    }
    
    convertPriceElement(element) {
        if (!element || !element.textContent) return;
        
        const text = element.textContent.trim();
        
        // Extract price from text using regex
        const dollarMatch = text.match(/\$\s?(\d+(?:,\d{3})*(?:\.\d{2})?)/);
        const rupeeMatch = text.match(/₹\s?(\d+(?:,\d{3})*(?:\.\d{2})?)/);
        
        let price = null;
        let originalCurrency = null;
        
        if (dollarMatch) {
            price = parseFloat(dollarMatch[1].replace(/,/g, ''));
            originalCurrency = 'USD';
        } else if (rupeeMatch) {
            price = parseFloat(rupeeMatch[1].replace(/,/g, ''));
            originalCurrency = 'INR';
        }
        
        // Smart pricing detection: If price looks like it's already market-researched (INR > 100), don't convert
        if (originalCurrency === 'INR' && price >= 100 && currentCurrency === 'INR') {
            // This is likely already a competitive INR price, don't convert
            return;
        }
        
        // Smart pricing detection: If price is very small (< $50), it might be incorrectly stored
        if (originalCurrency === 'USD' && price < 50 && currentCurrency === 'INR') {
            // Don't convert very small USD amounts as they're likely pricing errors
            return;
        }
        
        if (price && originalCurrency && originalCurrency !== currentCurrency) {
            const convertedPrice = this.convertPrice(price, originalCurrency, currentCurrency);
            const newText = text.replace(
                originalCurrency === 'USD' ? /\$\s?[\d,]+(?:\.\d{2})?/ : /₹\s?[\d,]+(?:\.\d{2})?/,
                `${CURRENCY_SYMBOLS[currentCurrency]}${this.formatPrice(convertedPrice)}`
            );
            element.textContent = newText;
        }
    }
    
    convertTextPrices() {
        // Find all text nodes containing currency symbols
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        
        const textNodes = [];
        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.includes('$') || node.textContent.includes('₹')) {
                textNodes.push(node);
            }
        }
        
        textNodes.forEach(textNode => {
            let text = textNode.textContent;
            let modified = false;
            
            // Convert USD to INR
            if (currentCurrency === 'INR') {
                text = text.replace(/\$(\d+(?:,\d{3})*(?:\.\d{2})?)/g, (match, amount) => {
                    const price = parseFloat(amount.replace(/,/g, ''));
                    const converted = this.convertPrice(price, 'USD', 'INR');
                    modified = true;
                    return `₹${this.formatPrice(converted)}`;
                });
            }
            
            // Convert INR to USD
            if (currentCurrency === 'USD') {
                text = text.replace(/₹(\d+(?:,\d{3})*(?:\.\d{2})?)/g, (match, amount) => {
                    const price = parseFloat(amount.replace(/,/g, ''));
                    const converted = this.convertPrice(price, 'INR', 'USD');
                    modified = true;
                    return `$${this.formatPrice(converted)}`;
                });
            }
            
            if (modified) {
                textNode.textContent = text;
            }
        });
    }
    
    convertPrice(amount, fromCurrency, toCurrency) {
        if (fromCurrency === toCurrency) return amount;
        
        if (fromCurrency === 'USD' && toCurrency === 'INR') {
            return amount * CURRENCY_RATES.USD_TO_INR;
        } else if (fromCurrency === 'INR' && toCurrency === 'USD') {
            return amount * CURRENCY_RATES.INR_TO_USD;
        }
        
        return amount;
    }
    
    formatPrice(price) {
        // Format price with proper decimals and commas
        if (currentCurrency === 'INR') {
            // Indian number format (₹1,23,456.78)
            return new Intl.NumberFormat('en-IN', {
                minimumFractionDigits: 0,
                maximumFractionDigits: 2
            }).format(price);
        } else {
            // US number format ($1,234.56)
            return new Intl.NumberFormat('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(price);
        }
    }
    
    showConversionNotification(oldCurrency, newCurrency) {
        // Show a toast notification about the currency conversion
        const message = `Currency changed from ${oldCurrency} to ${newCurrency}. All prices converted automatically.`;
        
        // Try to use existing toast system
        if (window.CartMax && window.CartMax.showToast) {
            window.CartMax.showToast(message, 'success');
        } else {
            // Fallback notification
            console.log(`💱 ${message}`);
        }
    }
}

// DISABLED: Currency switching is now handled directly in base.html with switchCurrency()
// The new system integrates with cart.js via custom events for real-time updates
// document.addEventListener('DOMContentLoaded', function() {
//     window.currencyConverter = new CurrencyConverter();
// });

// Reinitialize on page navigation (for SPA-like behavior)
window.addEventListener('load', function() {
    if (window.currencyConverter) {
        window.currencyConverter.convertAllPrices();
    }
});

// Export for global use
window.CurrencyConverter = CurrencyConverter;
window.CURRENCY_RATES = CURRENCY_RATES;

console.log('💱 CartMax Currency Converter: Ready!');