// CartMax Advanced Search Functionality
document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('search-form');
    const sortSelect = document.getElementById('sort-select');
    const perPageSelect = document.getElementById('per-page-select');
    const loadingIndicator = document.getElementById('loading-indicator');
    const searchResults = document.getElementById('search-results');
    const clearFiltersBtn = document.getElementById('clear-all-filters');
    const gridViewBtn = document.getElementById('grid-view');
    const listViewBtn = document.getElementById('list-view');
    const gridViewContainer = document.getElementById('grid-view-container');
    const listViewContainer = document.getElementById('list-view-container');
    
    // Price slider initialization
    initializePriceSlider();
    
    // Event listeners
    if (sortSelect) {
        sortSelect.addEventListener('change', handleSortChange);
    }
    
    if (perPageSelect) {
        perPageSelect.addEventListener('change', handlePerPageChange);
    }
    
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearAllFilters);
    }
    
    // Filter checkboxes and radio buttons - increased debounce for perf
    document.querySelectorAll('.filter-checkbox, .filter-radio').forEach(function(input) {
        input.addEventListener('change', debounce(handleFilterChange, 500));
    });
    
    // View toggle buttons
    if (gridViewBtn && listViewBtn) {
        gridViewBtn.addEventListener('click', () => toggleView('grid'));
        listViewBtn.addEventListener('click', () => toggleView('list'));
    }
    
    // Brand search functionality
    const brandSearchInput = document.getElementById('brand-search');
    if (brandSearchInput) {
        brandSearchInput.addEventListener('input', function() {
            filterBrandOptions(this.value);
        });
    }
    
    // Price slider event handlers
    const minPriceInput = document.getElementById('min-price-input');
    const maxPriceInput = document.getElementById('max-price-input');
    
    if (minPriceInput) {
        minPriceInput.addEventListener('change', handlePriceInputChange);
    }
    
    if (maxPriceInput) {
        maxPriceInput.addEventListener('change', handlePriceInputChange);
    }
    
    function initializePriceSlider() {
        const priceSlider = document.getElementById('price-slider');
        if (!priceSlider || !window.noUiSlider) return;
        
        // Get price stats from template context or set defaults
        const minPrice = parseFloat(priceSlider.dataset.minPrice) || 0;
        const maxPrice = parseFloat(priceSlider.dataset.maxPrice) || 1000;
        
        window.noUiSlider.create(priceSlider, {
            start: [minPrice, maxPrice],
            connect: true,
            range: {
                'min': minPrice,
                'max': maxPrice
            },
            step: 1,
            format: {
                to: function(value) {
                    return Math.round(value);
                },
                from: function(value) {
                    return Number(value);
                }
            }
        });
        
        priceSlider.noUiSlider.on('update', function(values, handle) {
            const minVal = values[0];
            const maxVal = values[1];
            
            if (minPriceInput) minPriceInput.value = minVal;
            if (maxPriceInput) maxPriceInput.value = maxVal;
        });
        
        priceSlider.noUiSlider.on('change', function(values, handle) {
            debounce(handleFilterChange, 500)();
        });
    }
    
    function handleSortChange() {
        updateSearchResults();
    }
    
    function handlePerPageChange() {
        updateSearchResults();
    }
    
    function handleFilterChange() {
        updateSearchResults();
    }
    
    function handlePriceInputChange() {
        const priceSlider = document.getElementById('price-slider');
        if (priceSlider && priceSlider.noUiSlider) {
            const minVal = parseFloat(minPriceInput.value) || 0;
            const maxVal = parseFloat(maxPriceInput.value) || 1000;
            priceSlider.noUiSlider.set([minVal, maxVal]);
        }
        debounce(handleFilterChange, 500)();
    }
    
    function clearAllFilters() {
        // Clear all filter inputs
        document.querySelectorAll('.filter-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        document.querySelectorAll('.filter-radio').forEach(radio => {
            radio.checked = false;
        });
        
        // Reset price inputs
        if (minPriceInput) minPriceInput.value = '';
        if (maxPriceInput) maxPriceInput.value = '';
        
        // Reset price slider
        const priceSlider = document.getElementById('price-slider');
        if (priceSlider && priceSlider.noUiSlider) {
            const minPrice = parseFloat(priceSlider.dataset.minPrice) || 0;
            const maxPrice = parseFloat(priceSlider.dataset.maxPrice) || 1000;
            priceSlider.noUiSlider.set([minPrice, maxPrice]);
        }
        
        // Clear brand search
        if (brandSearchInput) {
            brandSearchInput.value = '';
            filterBrandOptions('');
        }
        
        updateSearchResults();
    }
    
    function filterBrandOptions(searchTerm) {
        const brandOptions = document.querySelectorAll('.brand-option');
        searchTerm = searchTerm.toLowerCase();
        
        brandOptions.forEach(option => {
            const brandName = option.textContent.toLowerCase();
            if (brandName.includes(searchTerm)) {
                option.style.display = 'block';
            } else {
                option.style.display = 'none';
            }
        });
    }
    
    function toggleView(viewType) {
        if (viewType === 'grid') {
            gridViewContainer.style.display = 'block';
            listViewContainer.style.display = 'none';
            gridViewBtn.classList.add('active');
            listViewBtn.classList.remove('active');
            localStorage.setItem('cartmax-view-preference', 'grid');
        } else {
            gridViewContainer.style.display = 'none';
            listViewContainer.style.display = 'block';
            listViewBtn.classList.add('active');
            gridViewBtn.classList.remove('active');
            localStorage.setItem('cartmax-view-preference', 'list');
        }
    }
    
    function buildQueryString() {
        const params = new URLSearchParams();
        
        // Get current search query from URL or input
        const urlParams = new URLSearchParams(window.location.search);
        const query = urlParams.get('q') || '';
        if (query) {
            params.append('q', query);
        }
        
        // Get sort option
        if (sortSelect && sortSelect.value) {
            params.append('sort', sortSelect.value);
        }
        
        // Get per page option
        if (perPageSelect && perPageSelect.value) {
            params.append('per_page', perPageSelect.value);
        }
        
        // Get category filters
        document.querySelectorAll('input[name="category"]:checked').forEach(input => {
            params.append('category', input.value);
        });
        
        // Get brand filters
        document.querySelectorAll('input[name="brand"]:checked').forEach(input => {
            params.append('brand', input.value);
        });
        
        // Get price range filters
        document.querySelectorAll('input[name="price"]:checked').forEach(input => {
            params.append('price', input.value);
        });
        
        // Get custom price range
        if (minPriceInput && minPriceInput.value) {
            params.append('min_price', minPriceInput.value);
        }
        if (maxPriceInput && maxPriceInput.value) {
            params.append('max_price', maxPriceInput.value);
        }
        
        // Get rating filter
        const ratingInput = document.querySelector('input[name="rating"]:checked');
        if (ratingInput) {
            params.append('rating', ratingInput.value);
        }
        
        // Get availability filters
        document.querySelectorAll('input[name="availability"]:checked').forEach(input => {
            params.append('availability', input.value);
        });
        
        // Get color filters
        document.querySelectorAll('input[name="color"]:checked').forEach(input => {
            params.append('color', input.value);
        });
        
        // Get size filters
        document.querySelectorAll('input[name="size"]:checked').forEach(input => {
            params.append('size', input.value);
        });
        
        // Get material filters
        document.querySelectorAll('input[name="material"]:checked').forEach(input => {
            params.append('material', input.value);
        });
        
        // Get tag filters
        document.querySelectorAll('input[name="tag"]:checked').forEach(input => {
            params.append('tag', input.value);
        });
        
        return params.toString();
    }
    
    function showLoading() {
        if (loadingIndicator) {
            loadingIndicator.style.display = 'block';
        }
        if (searchResults) {
            searchResults.style.opacity = '0.5';
        }
    }
    
    function hideLoading() {
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
        if (searchResults) {
            searchResults.style.opacity = '1';
        }
    }
    
    function updateSearchResults() {
        const queryString = buildQueryString();
        const newUrl = window.location.pathname + '?' + queryString;
        
        // Update URL without page reload
        window.history.pushState({}, '', newUrl);
        
        // Show loading state
        showLoading();
        
        // Make AJAX request
        fetch(newUrl, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'text/html'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.text();
        })
        .then(html => {
            // Parse the HTML response
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Update the search results section
            const newSearchResults = doc.getElementById('search-results');
            if (newSearchResults && searchResults) {
                searchResults.innerHTML = newSearchResults.innerHTML;
            }
            
            // Update pagination if exists
            const paginationElement = document.querySelector('.pagination');
            const newPagination = doc.querySelector('.pagination');
            if (paginationElement && newPagination) {
                paginationElement.parentElement.innerHTML = newPagination.parentElement.innerHTML;
            }
            
            // Update result count
            const resultCount = doc.querySelector('.search-header');
            const currentResultCount = document.querySelector('.search-header');
            if (resultCount && currentResultCount) {
                currentResultCount.innerHTML = resultCount.innerHTML;
            }
            
            // Reinitialize any dynamic elements
            initializeProductActions();
            
            hideLoading();
        })
        .catch(error => {
            console.error('Error updating search results:', error);
            hideLoading();
            
            // Fallback to page reload
            window.location.href = newUrl;
        });
    }
    
    function initializeProductActions() {
        // Reinitialize add to cart buttons
        document.querySelectorAll('.add-to-cart-btn').forEach(button => {
            button.addEventListener('click', handleAddToCart);
        });
        
        // Reinitialize comparison buttons
        document.querySelectorAll('[title="Compare"]').forEach(button => {
            button.addEventListener('click', handleAddToComparison);
        });
        
        // Reinitialize wishlist buttons
        document.querySelectorAll('[title="Add to Wishlist"]').forEach(button => {
            button.addEventListener('click', handleAddToWishlist);
        });
    }
    
    function handleAddToCart(event) {
        const productId = event.target.closest('[data-product-id]').dataset.productId;
        // Implementation for add to cart functionality
        if (window.CartMax && window.CartMax.addToCart) {
            window.CartMax.addToCart(productId);
        }
    }
    
    function handleAddToComparison(event) {
        const productId = event.target.closest('[data-product-id]').dataset.productId;
        // Implementation for add to comparison functionality
        if (window.CartMax && window.CartMax.addToComparison) {
            window.CartMax.addToComparison(productId);
        }
    }
    
    function handleAddToWishlist(event) {
        const productId = event.target.closest('[data-product-id]').dataset.productId;
        // Implementation for add to wishlist functionality
        if (window.CartMax && window.CartMax.addToWishlist) {
            window.CartMax.addToWishlist(productId);
        }
    }
    
    // Utility function for debouncing
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Initialize product actions on page load
    initializeProductActions();
    
    // Restore view preference
    const viewPreference = localStorage.getItem('cartmax-view-preference');
    if (viewPreference) {
        toggleView(viewPreference);
    }
});
