"""
Utility functions for discount coupon operations
"""

from django.utils import timezone
from decimal import Decimal
from .models import DiscountCoupon, CouponUsage, Order
from .utils import get_exchange_rate


class CouponValidationError(Exception):
    """Custom exception for coupon validation errors"""
    pass


def convert_coupon_amount_to_currency(amount, source_currency='USD', target_currency='USD'):
    """
    Convert coupon amount limits from source currency to target currency.
    
    IMPORTANT: Coupon min/max amounts can be stored in ANY currency.
    This function converts between currencies as needed.
    
    Args:
        amount (Decimal): Amount in source currency
        source_currency (str): Currency of the stored amount ('USD' or 'INR')
        target_currency (str): Target currency code ('USD' or 'INR')
        
    Returns:
        Decimal: Converted amount in target currency
    """
    # If source and target are the same, no conversion needed
    if source_currency.upper() == target_currency.upper():
        return amount
    
    # Convert USD to INR
    if source_currency.upper() == 'USD' and target_currency.upper() == 'INR':
        rate = get_exchange_rate('USD', 'INR')
        converted = Decimal(str(amount)) * Decimal(str(rate))
        return converted.quantize(Decimal('0.01'))
    
    # Convert INR to USD
    elif source_currency.upper() == 'INR' and target_currency.upper() == 'USD':
        rate = get_exchange_rate('USD', 'INR')
        if rate > 0:
            converted = Decimal(str(amount)) / Decimal(str(rate))
            return converted.quantize(Decimal('0.01'))
        return amount
    
    return amount


def validate_coupon(coupon_code, user, cart_total, currency='USD'):
    """
    Validate a coupon code for a given user and cart total.
    
    Args:
        coupon_code (str): The coupon code to validate
        user (User): The user applying the coupon
        cart_total (Decimal): The total amount in the cart (before discount)
        currency (str): The currency code ('USD' or 'INR')
    
    Returns:
        tuple: (is_valid, error_message, coupon_object)
            - is_valid (bool): Whether the coupon is valid
            - error_message (str): Error message if invalid, "Valid" if valid
            - coupon_object (DiscountCoupon): The coupon object if found, None if not
    """
    
    # Check if coupon exists
    try:
        coupon = DiscountCoupon.objects.get(coupon_code=coupon_code.upper().strip())
    except DiscountCoupon.DoesNotExist:
        return False, "Invalid coupon code. Please check and try again.", None
    
    # Check if coupon is active
    if not coupon.is_active:
        return False, "This coupon is no longer active.", coupon
    
    # Check if coupon has expired
    if coupon.expiration_date and timezone.now() > coupon.expiration_date:
        return False, f"This coupon expired on {coupon.expiration_date.strftime('%Y-%m-%d')}.", coupon
    
    # Check global usage limit
    if coupon.max_usage_limit and coupon.usage_count >= coupon.max_usage_limit:
        return False, "This coupon has reached its maximum usage limit.", coupon
    
    # Check minimum order amount with proper currency conversion
    if coupon.minimum_order_amount:
        # Get the currency in which the coupon minimum amount is stored
        coupon_amount_currency = getattr(coupon, 'amount_currency', 'USD')  # Default to USD if not set
        
        # Convert coupon minimum amount to the cart's currency for comparison
        converted_minimum = convert_coupon_amount_to_currency(
            coupon.minimum_order_amount, 
            coupon_amount_currency, 
            currency
        )
        
        if cart_total < converted_minimum:
            # Use currency-appropriate symbol for display
            currency_symbol = '₹' if currency.upper() == 'INR' else '$'
            return False, f"This coupon requires a minimum order of {currency_symbol}{converted_minimum}. Your cart total is {currency_symbol}{cart_total}.", coupon
    
    # Check maximum order amount with proper currency conversion
    if coupon.maximum_order_amount:
        # Get the currency in which the coupon maximum amount is stored
        coupon_amount_currency = getattr(coupon, 'amount_currency', 'USD')  # Default to USD if not set
        
        # Convert coupon maximum amount to the cart's currency for comparison
        converted_maximum = convert_coupon_amount_to_currency(
            coupon.maximum_order_amount, 
            coupon_amount_currency, 
            currency
        )
        
        if cart_total > converted_maximum:
            # Use currency-appropriate symbol for display
            currency_symbol = '₹' if currency.upper() == 'INR' else '$'
            return False, f"This coupon is only valid for orders up to {currency_symbol}{converted_maximum}.", coupon
    
    # Per-user usage limits are disabled - coupons can be used multiple times
    # This allows users to apply the same coupon to multiple orders
    # Global usage limits are still enforced via coupon.max_usage_limit
    
    return True, "Valid", coupon


def calculate_discount(coupon, subtotal):
    """
    Calculate the discount amount for a given coupon and subtotal.
    
    Args:
        coupon (DiscountCoupon): The coupon object
        subtotal (Decimal): The cart/order subtotal before discount
    
    Returns:
        Decimal: The discount amount
    """
    if not coupon:
        return Decimal('0')
    
    return coupon.calculate_discount(subtotal)


def apply_coupon_to_cart(coupon_code, cart, user):
    """
    Validate and apply a coupon to a cart.
    
    Args:
        coupon_code (str): The coupon code to apply
        cart (Cart): The cart object to apply coupon to
        user (User): The user applying the coupon
    
    Returns:
        dict: Response with success status and message
            {
                'success': bool,
                'message': str,
                'discount_amount': Decimal (if successful),
                'discounted_total': Decimal (if successful),
                'currency': str,
                'currency_symbol': str
            }
    """
    from django.contrib.auth.models import AnonymousUser
    import sys
    
    # Refresh cart to ensure latest currency setting
    from .models import Cart as CartModel
    cart = CartModel.objects.get(pk=cart.pk)
    
    # Ensure cart currency is set correctly from user profile if authenticated
    if user and not isinstance(user, AnonymousUser):
        if hasattr(user, 'profile') and user.profile.preferred_currency:
            if cart.currency != user.profile.preferred_currency:
                cart.currency = user.profile.preferred_currency
                cart.save()
    
    # Get cart subtotal - always calculate directly from items
    cart_subtotal = Decimal('0')
    items_list = list(cart.items.all())
    for item in items_list:
        item_total = item.get_total_price_in_currency(cart.currency)
        cart_subtotal += item_total
    
    print(f'DEBUG: Cart {cart.id}, currency={cart.currency}, items={len(items_list)}, subtotal={cart_subtotal}', file=sys.stderr)
    
    # If still 0, cannot apply coupon
    if cart_subtotal <= 0:
        return {
            'success': False,
            'message': 'Cannot apply coupon to an empty cart.'
        }
    
    # Validate coupon
    is_valid, error_message, coupon = validate_coupon(coupon_code, user, cart_subtotal, cart.currency)
    
    if not is_valid:
        return {
            'success': False,
            'message': error_message
        }
    
    # Apply coupon to cart
    cart.applied_coupon = coupon
    cart.calculate_discount()
    cart.save()
    
    return {
        'success': True,
        'message': f"Coupon applied! You saved {cart.discount_amount} {cart.currency}.",
        'coupon_code': coupon.coupon_code,
        'discount_amount': float(cart.discount_amount),
        'discounted_total': float(cart.get_discounted_total()),
        'currency': cart.currency,
        'currency_symbol': cart.get_currency_symbol(),
        'subtotal': float(cart_subtotal),
        'original_subtotal': float(cart_subtotal),
        'tax': float(cart.get_tax_in_currency(cart.currency)),
        'shipping': 0.0,
        'applied_coupon': coupon.coupon_code,
        'final_total': float(cart.get_final_total_in_currency(cart.currency))
    }


def remove_coupon_from_cart(cart):
    """
    Remove the applied coupon from a cart.
    
    Args:
        cart (Cart): The cart object
    
    Returns:
        dict: Response with success status
    """
    cart.applied_coupon = None
    cart.discount_amount = Decimal('0')
    cart.save()
    
    return {
        'success': True,
        'message': 'Coupon removed successfully.',
        'new_total': cart.get_total_price_in_currency(cart.currency)
    }


def apply_coupon_to_order(coupon_code, order, user):
    """
    Apply a validated coupon to an order and track usage.
    
    Args:
        coupon_code (str): The coupon code to apply
        order (Order): The order object
        user (User): The user who placed the order
    
    Returns:
        dict: Response with success status
            {
                'success': bool,
                'message': str,
                'discount_amount': Decimal (if successful)
            }
    """
    from django.db import transaction
    
    # Get order subtotal
    order_subtotal = sum(item.get_total_price_in_currency(order.currency) for item in order.items.all())
    
    # Validate coupon
    is_valid, error_message, coupon = validate_coupon(coupon_code, user, order_subtotal, order.currency)
    
    if not is_valid:
        return {
            'success': False,
            'message': error_message
        }
    
    with transaction.atomic():
        # Lock the coupon to prevent race conditions
        coupon = DiscountCoupon.objects.select_for_update().get(pk=coupon.pk)
        
        # Re-check limits after locking
        if coupon.max_usage_limit and coupon.usage_count >= coupon.max_usage_limit:
            return {
                'success': False,
                'message': 'This coupon has reached its maximum usage limit.'
            }
        
        # Store original subtotal
        order.original_subtotal = order_subtotal
        
        # Calculate and apply discount
        discount = coupon.calculate_discount(order_subtotal)
        order.applied_coupon = coupon
        order.discount_amount = discount
        
        # Recalculate tax on discounted amount
        discounted_subtotal = order_subtotal - discount
        order.tax_amount = discounted_subtotal * Decimal('0.08')
        
        # Save order with discount
        order.save()
        
        # Update coupon usage
        coupon.usage_count += 1
        coupon.save()
        
        # Per-user usage tracking is disabled - users can apply coupons to multiple orders
        # Only global usage count is tracked
    
    return {
        'success': True,
        'message': f"Coupon applied successfully! You saved {discount} {order.currency}.",
        'discount_amount': discount,
        'final_total': order.get_final_total()
    }


def validate_coupon_on_checkout(coupon_code, user, cart):
    """
    Re-validate a coupon before checkout (security check).
    
    Args:
        coupon_code (str): The coupon code
        user (User): The user
        cart (Cart): The cart object
    
    Returns:
        tuple: (is_valid, coupon_object, error_message)
    """
    cart_subtotal = cart.get_total_price_in_currency(cart.currency)
    is_valid, error_message, coupon = validate_coupon(coupon_code, user, cart_subtotal, cart.currency)
    
    return is_valid, coupon, error_message
