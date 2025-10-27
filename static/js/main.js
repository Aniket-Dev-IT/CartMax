// CartMax - Main JavaScript

$(document).ready(function() {
    // Back to top functionality
    $('.back-to-top-link').click(function(e) {
        e.preventDefault();
        $('html, body').animate({
            scrollTop: 0
        }, 800);
    });
    
    // Show/hide back to top button based on scroll
    $(window).scroll(function() {
        if ($(this).scrollTop() > 300) {
            $('.back-to-top').addClass('show');
        } else {
            $('.back-to-top').removeClass('show');
        }
    });
    
    // Search input focus effects
    $('.search-input').focus(function() {
        $('.search-container').addClass('search-focused');
    }).blur(function() {
        $('.search-container').removeClass('search-focused');
    });
    
    // Category navigation horizontal scroll for mobile
    $('.category-list').on('scroll', function() {
        // Optional: Add scroll indicators
    });
    
    // Product image lazy loading
    const observerOptions = {
        root: null,
        rootMargin: '50px',
        threshold: 0.1
    };
    
    const imageObserver = new IntersectionObserver(function(entries, observer) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                const img = entry.target;
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    img.classList.remove('lazy-load');
                    observer.unobserve(img);
                }
            }
        });
    }, observerOptions);
    
    // Observe all lazy load images
    document.querySelectorAll('img.lazy-load').forEach(function(img) {
        imageObserver.observe(img);
    });
    
    // Product rating display
    function displayRating(rating, container) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 !== 0;
        let starsHtml = '';
        
        // Full stars
        for (let i = 0; i < fullStars; i++) {
            starsHtml += '<i class="fas fa-star"></i>';
        }
        
        // Half star
        if (hasHalfStar) {
            starsHtml += '<i class="fas fa-star-half-alt"></i>';
        }
        
        // Empty stars
        const emptyStars = 5 - Math.ceil(rating);
        for (let i = 0; i < emptyStars; i++) {
            starsHtml += '<i class="far fa-star"></i>';
        }
        
        if (container) {
            container.innerHTML = starsHtml;
        }
        return starsHtml;
    }
    
    // Initialize rating displays
    $('.product-rating .stars').each(function() {
        const rating = parseFloat($(this).data('rating'));
        if (rating && rating > 0) {
            this.innerHTML = displayRating(rating);
        }
    });
    
    // Search suggestions
    let searchTimeout;
    $('.search-input').on('input', function() {
        const query = $(this).val().trim();
        const $suggestions = $('#search-suggestions');
        
        clearTimeout(searchTimeout);
        
        if (query.length >= 2) {
            searchTimeout = setTimeout(function() {
                $.ajax({
                    url: '/ajax/search-suggestions/',
                    method: 'GET',
                    data: { q: query },
                    success: function(data) {
                        if (data.suggestions && data.suggestions.length > 0) {
                            let suggestionsHtml = '<ul class="list-unstyled">';
                            data.suggestions.forEach(function(suggestion) {
                                suggestionsHtml += `<li><a href="#" class="suggestion-item">${suggestion}</a></li>`;
                            });
                            suggestionsHtml += '</ul>';
                            $suggestions.html(suggestionsHtml).show();
                        } else {
                            $suggestions.hide();
                        }
                    },
                    error: function() {
                        $suggestions.hide();
                    }
                });
            }, 300);
        } else {
            $suggestions.hide();
        }
    });
    
    // Hide suggestions when clicking outside
    $(document).click(function(e) {
        if (!$(e.target).closest('.search-form').length) {
            $('#search-suggestions').hide();
        }
    });
    
    // Handle suggestion clicks
    $(document).on('click', '.suggestion-item', function(e) {
        e.preventDefault();
        const suggestion = $(this).text();
        $('.search-input').val(suggestion);
        $('#search-suggestions').hide();
        $('.search-form').submit();
    });
    
    // Price formatting
    function formatPrice(price) {
        return '$' + parseFloat(price).toFixed(2);
    }
    
    // Quantity input validation
    $('.quantity-input').on('input', function() {
        let value = parseInt($(this).val());
        const min = parseInt($(this).attr('min')) || 1;
        const max = parseInt($(this).attr('max')) || 999;
        
        if (isNaN(value) || value < min) {
            value = min;
        } else if (value > max) {
            value = max;
        }
        
        $(this).val(value);
    });
    
    // Image gallery functionality
    $('.product-thumbnail').click(function(e) {
        e.preventDefault();
        const newSrc = $(this).data('full-image');
        const $mainImage = $('.main-product-image');
        
        if (newSrc && $mainImage.length) {
            $mainImage.attr('src', newSrc);
            $('.product-thumbnail').removeClass('active');
            $(this).addClass('active');
        }
    });
    
    // Toast notifications - Using modern toast_notifications.js system
    // Note: The showToast function is provided by toast_notifications.js
    // This is the preferred notification system across the entire application
    
    // Loading state management
    function showLoading($element) {
        const originalText = $element.text();
        $element.data('original-text', originalText);
        $element.html('<i class="fas fa-spinner fa-spin"></i> Loading...');
        $element.prop('disabled', true);
    }
    
    function hideLoading($element) {
        const originalText = $element.data('original-text');
        $element.html(originalText);
        $element.prop('disabled', false);
    }
    
    // Form validation
    $('.needs-validation').on('submit', function(e) {
        const form = this;
        if (!form.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
        }
        $(form).addClass('was-validated');
    });
    
    // Auto-hide alerts
    setTimeout(function() {
        $('.alert:not(.alert-permanent)').fadeOut();
    }, 5000);
    
    // Price range filter
    $('#price-range').on('change', function() {
        const value = $(this).val();
        $('#price-display').text('$0 - $' + value);
    });
    
    // Category filter
    $('.category-filter').change(function() {
        if (typeof filterProducts === 'function') {
            filterProducts();
        }
    });
    
    // Sort dropdown
    $('#sort-select').change(function() {
        if (typeof sortProducts === 'function') {
            sortProducts($(this).val());
        }
    });
    
    // Pagination
    $('.pagination').on('click', 'a', function(e) {
        const href = $(this).attr('href');
        if (href && href !== '#') {
            // Add loading state to pagination
            $(this).html('<i class="fas fa-spinner fa-spin"></i>');
        }
    });
    
    // Initialize tooltips
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Initialize popovers
    if (typeof bootstrap !== 'undefined' && bootstrap.Popover) {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }
    
    // Mobile navigation toggle
    $('#mobileNavToggle').click(function() {
        const $menu = $('#mobileNavMenu');
        const $icon = $('#mobileNavIcon');
        
        $menu.toggleClass('active');
        
        // Toggle icon between bars and times
        if ($menu.hasClass('active')) {
            $icon.removeClass('fa-bars').addClass('fa-times');
            $(this).attr('aria-expanded', 'true');
            // Prevent body scroll when menu is open
            $('body').addClass('mobile-menu-open');
        } else {
            $icon.removeClass('fa-times').addClass('fa-bars');
            $(this).attr('aria-expanded', 'false');
            $('body').removeClass('mobile-menu-open');
        }
    });
    
    // Close mobile menu when clicking outside or on a link
    $(document).click(function(e) {
        const $target = $(e.target);
        if (!$target.closest('.mobile-nav-menu, .mobile-nav-toggle').length) {
            closeMobileMenu();
        }
    });
    
    // Close mobile menu when clicking on nav links
    $('.mobile-nav-menu .nav-link').click(function() {
        closeMobileMenu();
    });
    
    // Close mobile menu on escape key
    $(document).keydown(function(e) {
        if (e.key === 'Escape') {
            closeMobileMenu();
        }
    });
    
    // Function to close mobile menu
    function closeMobileMenu() {
        $('#mobileNavMenu').removeClass('active');
        $('#mobileNavIcon').removeClass('fa-times').addClass('fa-bars');
        $('#mobileNavToggle').attr('aria-expanded', 'false');
        $('body').removeClass('mobile-menu-open');
    }
    
    // Handle window resize
    $(window).resize(function() {
        if ($(window).width() > 768) {
            closeMobileMenu();
        }
    });
    
    // Navbar scroll effect
    $(window).scroll(function() {
        const $navbar = $('.cartmax-navbar');
        if ($(window).scrollTop() > 50) {
            $navbar.addClass('scrolled');
        } else {
            $navbar.removeClass('scrolled');
        }
    });
    
    // Smooth navbar height adjustment on mobile menu toggle
    function adjustNavbarHeight() {
        const $navbar = $('.cartmax-navbar');
        const $menu = $('#mobileNavMenu');
        
        if ($menu.hasClass('active')) {
            // Set navbar height to accommodate menu
            const navbarHeight = $navbar.outerHeight();
            const menuHeight = $menu.outerHeight();
            $('body').css('padding-top', navbarHeight + menuHeight + 'px');
        } else {
            // Reset body padding
            $('body').css('padding-top', '');
        }
    }
    
    // Mobile touch improvements
    if ('ontouchstart' in window) {
        // Add touch class for touch-specific styles
        $('html').addClass('touch');
        
        // Faster tap response for mobile
        $('.btn, .nav-link, .card-modern').on('touchstart', function() {
            $(this).addClass('touch-active');
        }).on('touchend', function() {
            const $this = $(this);
            setTimeout(() => {
                $this.removeClass('touch-active');
            }, 150);
        });
    }
    
    // Image lazy loading with intersection observer
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        img.classList.add('loaded');
                        observer.unobserve(img);
                    }
                }
            });
        }, {
            rootMargin: '50px'
        });
        
        // Observe all lazy images
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
    
    // Smooth scrolling for anchor links
    $('a[href*="#"]:not([href="#"])').click(function() {
        if (location.pathname.replace(/^\//, '') === this.pathname.replace(/^\//, '') && location.hostname === this.hostname) {
            let target = $(this.hash);
            target = target.length ? target : $('[name=' + this.hash.slice(1) + ']');
            if (target.length) {
                $('html, body').animate({
                    scrollTop: target.offset().top - 100
                }, 1000);
                return false;
            }
        }
    });
    
    // Global error handler for AJAX requests
    $(document).ajaxError(function(event, jqXHR, ajaxSettings, thrownError) {
        if (jqXHR.status !== 0) { // Ignore aborted requests
            console.error('AJAX Error:', thrownError);
            showToast('An error occurred. Please try again.', 'error');
        }
    });
    
    // Note: Add to cart functionality is handled by cart.js to avoid conflicts
    
    // Get CSRF token from cookies
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
    
    // Update cart count in header - Enhanced with multiple selectors and animation
    function updateCartCount(count) {
        console.log('🛒 Updating cart count to:', count);
        
        // Selector targets: .cart-badge, .cart-count, #cart-count, [data-cart-count]
        const selectors = ['.cart-badge', '.cart-count', '#cart-count', '[data-cart-count]'];
        
        selectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                // Update text content
                element.textContent = count;
                element.setAttribute('data-cart-count', count);
                
                // Show/hide based on count
                if (count > 0) {
                    element.style.display = 'inline';
                    element.classList.remove('d-none');
                    // Add highlight animation
                    element.classList.add('cart-badge-update');
                    setTimeout(() => element.classList.remove('cart-badge-update'), 600);
                } else {
                    element.style.display = 'none';
                    element.classList.add('d-none');
                }
                
                console.log(`✅ Updated ${selector}:`, element, 'count:', count);
            });
        });
        
        // Update mobile cart links
        const mobileCartLinks = document.querySelectorAll('a[href*="cart"]');
        mobileCartLinks.forEach(link => {
            const text = link.textContent || link.innerText;
            if (text.includes('Cart')) {
                if (count > 0) {
                    link.innerHTML = link.innerHTML.replace(/Cart\s*\(\d+\)?/g, `Cart (${count})`);
                } else {
                    link.innerHTML = link.innerHTML.replace(/Cart\s*\(\d+\)?/g, 'Cart');
                }
            }
        });
    }
    
    // Make updateCartCount globally accessible
    window.updateCartCount = updateCartCount;
    
    // Add to Cart handling is now done by cart.js to avoid conflicts
    // This ensures consistent behavior and proper CSRF handling
    // The cart.js file handles all .add-to-cart-btn click events
    
    // Additional cart/loading helper functions
    function showLoading($btn) {
        $btn.data('original-text', $btn.html());
        $btn.html('<i class="fas fa-spinner fa-spin"></i> Loading...');
        $btn.prop('disabled', true);
    }
    
    function hideLoading($btn) {
        $btn.html($btn.data('original-text') || 'Add to Cart');
        $btn.prop('disabled', false);
    }
    
    // Expose utility functions globally
    window.CartMax = {
        showToast: showToast,
        showLoading: showLoading,
        hideLoading: hideLoading,
        displayRating: displayRating,
        formatPrice: formatPrice,
        addToCart: addToCart,
        updateCartCount: updateCartCount,
        getCookie: getCookie
    };
});