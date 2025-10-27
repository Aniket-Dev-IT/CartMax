// CartMax - Modern Cart Functionality

// Helper function to show toast with fallback
function showCartToast(message, type) {
    // Try to use global showToast first (from toast_notifications.js)
    if (typeof window.showToast === 'function') {
        window.showToast(message, type);
    } 
    // Fallback to CartMax if available
    else if (window.CartMax && typeof window.CartMax.showToast === 'function') {
        window.CartMax.showToast(message, type);
    }
    // Last resort fallback
    else {
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
}

// Ensure CartMax object exists and delegates to modern toast notification system
if (typeof window.CartMax === 'undefined') {
    window.CartMax = {
        showToast: function(msg, type) {
            // Use the global showToast from toast_notifications.js
            if (typeof showToast === 'function') {
                showToast(msg, type);
            } else {
                console.log(`[${type.toUpperCase()}] ${msg}`);
            }
        },
        showLoading: function($btn) {
            $btn.data('original-text', $btn.html());
            $btn.html('<i class="fas fa-spinner fa-spin"></i> Loading...');
            $btn.prop('disabled', true);
        },
        hideLoading: function($btn) {
            $btn.html($btn.data('original-text') || 'Add to Cart');
            $btn.prop('disabled', false);
        },
        formatPrice: function(price, symbol) {
            const amount = parseFloat(price);
            const formatted = amount.toFixed(2);
            return symbol + formatted;
        }
    };
}

$(document).ready(function() {
    
    // CSRF token setup for Django
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
    console.log('🔐 CSRF Token Retrieved:', csrftoken ? '✅ Present' : '❌ MISSING');
    
    function csrfSafeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    
    // Setup AJAX with CSRF token in headers (more reliable than data)
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        },
        crossDomain: false  // Enable CSRF protection
    });
    
    // Also make csrftoken available globally
    window.csrftoken = csrftoken;
    
    // Add to cart functionality - Enhanced with toast notifications
    $('.add-to-cart-btn').click(function(e) {
        e.preventDefault();
        
        const $btn = $(this);
        const productId = $btn.data('product-id');
        const quantity = parseInt($('#quantity').val()) || 1;
        
        if (!productId) {
            showCartToast('Product not found.', 'error');
            return;
        }
        
        // Show loading state
        CartMax.showLoading($btn);
        
        // Log the request details
        console.log('🚀 Add to Cart Request:', {
            url: `/cart/add/${productId}/`,
            productId: productId,
            quantity: quantity,
            csrftoken: csrftoken ? '***present***' : '***MISSING***'
        });
        
        $.ajax({
            url: `/cart/add/${productId}/`,
            method: 'POST',
            data: {
                'quantity': quantity
            },
            success: function(data) {
                console.log('✅ Add to Cart Success:', data);
                
                if (data.success) {
                    // Update cart count in navigation (check both window and main.js context)
                    if (window.updateCartCount) {
                        window.updateCartCount(data.cart_count);
                        console.log('📊 Cart count updated to:', data.cart_count);
                    }
                    
                    // Show success message using unified toast notification system
                    showCartToast(data.message || 'Added to cart successfully!', 'success');
                    
                    // Log cart totals
                    console.log('💰 Cart Totals:', {
                        subtotal: data.subtotal,
                        tax: data.tax,
                        shipping: data.shipping,
                        total: data.total
                    });
                    
                    // Update button text temporarily with success feedback
                    $btn.html('<i class="fas fa-check"></i> Added to Cart');
                    $btn.addClass('btn-success').removeClass('btn-cartmax');
                    
                    setTimeout(function() {
                        $btn.html('<i class="fas fa-shopping-cart"></i> Add to Cart');
                        $btn.removeClass('btn-success').addClass('btn-cartmax');
                    }, 2000);
                } else {
                    const errorMsg = data.message || 'Failed to add to cart.';
                    console.error('❌ Add to Cart Failed:', errorMsg);
                    showCartToast(errorMsg, 'error');
                }
            },
            error: function(xhr) {
                let message = 'Failed to add to cart.';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    message = xhr.responseJSON.message;
                }
                console.error('❌ Add to Cart AJAX Error:', xhr.status, xhr.statusText, xhr.responseText);
                showCartToast(message, 'error');
            },
            complete: function() {
                CartMax.hideLoading($btn);
            }
        });
    });
    
    
    // Update cart item quantity - debounced to prevent multiple requests
    let quantityUpdateTimeout;
    $('.quantity-input').on('change', function() {
        clearTimeout(quantityUpdateTimeout);
        
        const $input = $(this);
        const productId = $input.data('product-id');
        const quantity = parseInt($input.val());
        const $row = $input.closest('.cart-item');
        
        if (!productId || !quantity || quantity < 1) {
            return;
        }
        
        // Store original value for revert
        const originalQuantity = $input.data('original-value') || 1;
        
        // Debounce the update to prevent multiple simultaneous requests
        quantityUpdateTimeout = setTimeout(function() {
            // Show loading on the row
            $row.addClass('updating');
            
            $.ajax({
                url: '/cart/update/',
                method: 'POST',
                data: {
                    'product_id': productId,
                    'quantity': quantity
                },
                success: function(data) {
                    if (data.success) {
                        // Reload page to show updated prices in user's currency
                        location.reload();
                        
                        // Update original value to prevent accidental reverts
                        $input.data('original-value', quantity);
                        
                        // Show toast notification ONCE
                        showCartToast('Quantity updated successfully!', 'success');
                    } else {
                        showCartToast(data.message || 'Failed to update cart.', 'error');
                        // Revert quantity
                        $input.val(originalQuantity);
                    }
                },
                error: function() {
                    showCartToast('Failed to update cart.', 'error');
                    // Revert to previous value
                    $input.val(originalQuantity);
                },
                complete: function() {
                    $row.removeClass('updating');
                }
            });
        }, 500);  // Debounce for 500ms
    });
    
    // Remove item from cart
    $('.remove-item').click(function(e) {
        e.preventDefault();
        
        const $btn = $(this);
        const productId = $btn.data('product-id');
        const $row = $btn.closest('.cart-item');
        const productName = $row.find('.product-title').text();
        
        if (!productId) {
            return;
        }
        
        // Confirm removal
        if (!confirm(`Remove "${productName}" from your cart?`)) {
            return;
        }
        
        // Add loading state
        $row.addClass('removing');
        
        $.ajax({
            url: `/cart/remove/${productId}/`,
            method: 'POST',
            data: {},
            success: function(data) {
                if (data.success) {
                    // If cart is empty, reload page immediately to show empty state
                    if (data.cart_empty) {
                        window.location.reload();
                        return;
                    }
                    
                    // Remove item with animation
                    $row.fadeOut(300, function() {
                        $(this).remove();
                    });
                    
                    // Update cart UI with new totals and currency
                    updateCartUI(data);
                    
                    // Show success toast
                    showCartToast(data.message || 'Item removed from cart.', 'success');
                } else {
                    showCartToast(data.message || 'Failed to remove item.', 'error');
                }
            },
            error: function() {
                showCartToast('Failed to remove item.', 'error');
            },
            complete: function() {
                $row.removeClass('removing');
            }
        });
    });
    
    
    // Quantity increment/decrement buttons - find input by searching parent
    $('.qty-btn-minus').click(function() {
        const $input = $(this).closest('.input-group').find('.quantity-input');
        let currentVal = parseInt($input.val());
        if (currentVal > 1) {
            $input.val(currentVal - 1).trigger('change');
        }
    });
    
    $('.qty-btn-plus').click(function() {
        const $input = $(this).closest('.input-group').find('.quantity-input');
        let currentVal = parseInt($input.val());
        const maxVal = parseInt($input.attr('max')) || 999;
        if (currentVal < maxVal) {
            $input.val(currentVal + 1).trigger('change');
        }
    });
    
    // Clear entire cart
    $('.clear-cart-btn').click(function(e) {
        e.preventDefault();
        
        const cartItemCount = $('.cart-item').length;
        if (cartItemCount === 0) {
            showCartToast('Your cart is already empty.', 'info');
            return;
        }
        
        // Confirm clear
        if (!confirm('Are you sure you want to clear your entire cart? This action cannot be undone.')) {
            return;
        }
        
        const $btn = $(this);
        $btn.prop('disabled', true).text('Clearing...');
        
        $.ajax({
            url: '/cart/clear/',
            method: 'POST',
            data: {},
            success: function(data) {
                if (data.success) {
                    // Fade out all cart items
                    $('.cart-item').fadeOut(300, function() {
                        location.reload();
                    });
                    
                    // Update cart count in navigation
                    if (window.updateCartCount) window.updateCartCount(0);
                    
                    showCartToast('Cart cleared successfully.', 'success');
                } else {
                    showCartToast(data.message || 'Failed to clear cart.', 'error');
                }
            },
            error: function() {
                showCartToast('Failed to clear cart.', 'error');
            },
            complete: function() {
                $btn.prop('disabled', false).text('Clear Cart');
            }
        });
    });
    
    // Proceed to checkout validation
    $('#checkout-btn').click(function(e) {
        const cartItemCount = $('.cart-item').length;
        if (cartItemCount === 0) {
            e.preventDefault();
            showCartToast('Your cart is empty.', 'error');
            return false;
        }
    });
    
    // Store original values for quantity inputs
    $('.quantity-input').each(function() {
        $(this).data('original-value', $(this).val());
    });
    
    // Add to wishlist functionality
    $('.add-to-wishlist-btn').click(function(e) {
        e.preventDefault();
        
        const $btn = $(this);
        const productId = $btn.data('product-id');
        
        if (!productId) {
            showCartToast('Product not found.', 'error');
            return;
        }
        
        // Show loading state
        const originalHtml = $btn.html();
        $btn.html('<i class="fas fa-spinner fa-spin"></i>').prop('disabled', true);
        
        $.ajax({
            url: `/store/wishlist/add/${productId}/`,
            method: 'POST',
            data: {},
            success: function(data) {
                if (data.success) {
                    showCartToast(data.message || 'Added to wishlist!', 'success');
                    
                    // Update button appearance
                    $btn.html('<i class="fas fa-heart"></i> In Wishlist');
                    $btn.addClass('btn-danger').removeClass('btn-outline-danger');
                    $btn.data('in-wishlist', 'true');
                    
                    // Show temporary login prompt if guest
                    if (data.is_guest) {
                        setTimeout(function() {
                            showCartToast('Sign in to save your wishlist permanently!', 'info');
                        }, 1500);
                    }
                } else {
                    showCartToast(data.message || 'Failed to add to wishlist.', 'error');
                }
            },
            error: function(xhr) {
                let message = 'Failed to add to wishlist.';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    message = xhr.responseJSON.message;
                }
                showCartToast(message, 'error');
            },
            complete: function() {
                $btn.prop('disabled', false);
                if ($btn.data('in-wishlist') !== 'true') {
                    $btn.html(originalHtml);
                }
            }
        });
    });
    
    // Remove from wishlist functionality
    $('.remove-from-wishlist-btn').click(function(e) {
        e.preventDefault();
        
        const $btn = $(this);
        const productId = $btn.data('product-id');
        
        if (!productId) {
            showCartToast('Product not found.', 'error');
            return;
        }
        
        const originalHtml = $btn.html();
        $btn.html('<i class="fas fa-spinner fa-spin"></i>').prop('disabled', true);
        
        $.ajax({
            url: `/store/wishlist/remove/${productId}/`,
            method: 'POST',
            data: {},
            success: function(data) {
                if (data.success) {
                    showCartToast(data.message || 'Removed from wishlist!', 'success');
                    
                    // Remove item with animation
                    const $row = $btn.closest('.wishlist-item');
                    $row.fadeOut(300, function() {
                        $(this).remove();
                        // Check if wishlist is empty
                        if ($('.wishlist-item').length === 0) {
                            location.reload();
                        }
                    });
                } else {
                    showCartToast(data.message || 'Failed to remove from wishlist.', 'error');
                }
            },
            error: function(xhr) {
                let message = 'Failed to remove from wishlist.';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    message = xhr.responseJSON.message;
                }
                showCartToast(message, 'error');
            },
            complete: function() {
                $btn.prop('disabled', false).html(originalHtml);
            }
        });
    });
    
    // Move from wishlist to cart
    $('.move-to-cart-btn').click(function(e) {
        e.preventDefault();
        
        const $btn = $(this);
        const productId = $btn.data('product-id');
        const $row = $btn.closest('.wishlist-item');
        
        if (!productId) {
            showCartToast('Product not found.', 'error');
            return;
        }
        
        $btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Moving...');
        
        $.ajax({
            url: `/store/wishlist/move-to-cart/${productId}/`,
            method: 'POST',
            data: {},
            success: function(data) {
                if (data.success) {
                    // Remove item with animation
                    $row.fadeOut(300, function() {
                        $(this).remove();
                    });
                    
                    showCartToast(data.message || 'Moved to cart!', 'success');
                    
                    // Update cart count if function exists
                    if (window.updateCartCount) {
                        window.updateCartCount(data.cart_count);
                    }
                } else {
                    showCartToast(data.message || 'Failed to move item.', 'error');
                }
            },
            error: function(xhr) {
                let message = 'Failed to move to cart.';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    message = xhr.responseJSON.message;
                }
                showCartToast(message, 'error');
            },
            complete: function() {
                $btn.prop('disabled', false).html('<i class="fas fa-shopping-cart"></i> Move to Cart');
            }
        });
    });
});
