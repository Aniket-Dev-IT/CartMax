"""
API views for coupon operations
Provides AJAX endpoints for applying/removing coupons from cart
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from decimal import Decimal
import json
import logging

from .models import Cart, DiscountCoupon
from .coupon_utils import (
    validate_coupon,
    apply_coupon_to_cart,
    remove_coupon_from_cart,
)

logger = logging.getLogger(__name__)


def get_user_cart(request):
    """Get or create cart for current user/session"""
    if request.user.is_authenticated:
        # Try to get existing cart for user
        cart = Cart.objects.filter(user=request.user).first()
        if not cart:
            # No cart for this user - create one
            cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Always set cart currency from user's preferred currency
        if hasattr(request.user, 'profile') and request.user.profile.preferred_currency:
            if cart.currency != request.user.profile.preferred_currency:
                cart.currency = request.user.profile.preferred_currency
                cart.save()
        else:
            # If no profile, default to USD
            if cart.currency != 'USD':
                cart.currency = 'USD'
                cart.save()
    else:
        if not request.session.session_key:
            request.session.create()
        cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
        # For guests, try to get currency from session, otherwise default to USD
        currency = request.session.get('currency', 'USD')
        if cart.currency != currency:
            cart.currency = currency
            cart.save()
    
    return cart


@require_http_methods(["POST"])
def apply_coupon_api(request):
    """
    API endpoint to apply a coupon to the user's cart
    
    POST /api/cart/apply-coupon/
    Request body: {"coupon_code": "SAVE10"}
    Response: {"success": true/false, "message": "...", "discount_amount": X, "discounted_total": Y}
    """
    try:
        from .utils import get_user_currency
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code', '').strip().upper()
        
        if not coupon_code:
            return JsonResponse({
                'success': False,
                'message': 'Coupon code is required.'
            }, status=400)
        
        # Get user's cart
        cart = get_user_cart(request)
        
        # CRITICAL: Force cart currency to user's preferred currency
        if request.user.is_authenticated:
            user_currency = get_user_currency(request.user)
            cart.currency = user_currency
            cart.save()
        
        # Apply coupon
        result = apply_coupon_to_cart(coupon_code, cart, request.user)
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request format.'
        }, status=400)
    except Exception as e:
        logger.error(f"Error applying coupon: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while applying the coupon.'
        }, status=500)


@require_http_methods(["POST"])
def remove_coupon_api(request):
    """
    API endpoint to remove applied coupon from cart
    
    POST /api/cart/remove-coupon/
    Request body: {} (empty)
    Response: {"success": true/false, "message": "...", "new_total": X}
    """
    try:
        cart = get_user_cart(request)
        result = remove_coupon_from_cart(cart)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error removing coupon: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while removing the coupon.'
        }, status=500)


@require_http_methods(["GET"])
def validate_coupon_api(request):
    """
    API endpoint to validate coupon without applying it
    
    GET /api/coupon/validate/?code=SAVE10&amount=1000&currency=INR
    Response: {"valid": true/false, "discount_amount": X, "message": "..."}
    """
    try:
        from .utils import get_user_currency
        coupon_code = request.GET.get('code', '').strip().upper()
        amount_str = request.GET.get('amount', '0')
        
        # CRITICAL: Get user's actual currency from profile, not from request parameter
        if request.user.is_authenticated:
            currency = get_user_currency(request.user).upper()
        else:
            currency = request.GET.get('currency', 'USD').upper()
        
        if not coupon_code:
            return JsonResponse({
                'valid': False,
                'message': 'Coupon code is required.'
            }, status=400)
        
        try:
            cart_total = Decimal(amount_str)
        except:
            return JsonResponse({
                'valid': False,
                'message': 'Invalid order amount.'
            }, status=400)
        
        # Validate coupon
        is_valid, error_message, coupon = validate_coupon(
            coupon_code,
            request.user if request.user.is_authenticated else None,
            cart_total,
            currency
        )
        
        if is_valid and coupon:
            # Calculate discount preview
            discount_amount = coupon.calculate_discount(cart_total)
            return JsonResponse({
                'valid': True,
                'discount_amount': float(discount_amount),
                'discount_display': coupon.get_discount_display(),
                'message': f"This coupon will save you {discount_amount} {currency}!"
            })
        else:
            return JsonResponse({
                'valid': False,
                'message': error_message
            })
        
    except Exception as e:
        logger.error(f"Error validating coupon: {e}", exc_info=True)
        return JsonResponse({
            'valid': False,
            'message': 'An error occurred while validating the coupon.'
        }, status=500)


@require_http_methods(["GET"])
def get_cart_summary_api(request):
    """
    API endpoint to get current cart summary with coupon info
    
    GET /api/cart/summary/
    Response: {
        "subtotal": X,
        "discount_amount": Y,
        "discounted_subtotal": Z,
        "tax": T,
        "shipping": S,
        "final_total": F,
        "applied_coupon": "CODE" or null,
        "currency": "USD"/"INR"
    }
    """
    try:
        cart = get_user_cart(request)
        
        subtotal = cart.get_total_price_in_currency(cart.currency)
        discount_amount = cart.discount_amount or Decimal('0')
        discounted_subtotal = subtotal - discount_amount
        tax = cart.get_tax_in_currency(cart.currency)
        shipping = cart.shipping_amount if hasattr(cart, 'shipping_amount') else Decimal('0')
        final_total = discounted_subtotal + tax + shipping
        
        response = {
            'subtotal': float(subtotal),
            'discount_amount': float(discount_amount),
            'discounted_subtotal': float(discounted_subtotal),
            'tax': float(tax),
            'shipping': float(shipping),
            'final_total': float(final_total),
            'applied_coupon': cart.applied_coupon.coupon_code if cart.applied_coupon else None,
            'currency': cart.currency,
            'currency_symbol': cart.get_currency_symbol(),
            'item_count': cart.get_total_items()
        }
        
        return JsonResponse(response)
        
    except Exception as e:
        logger.error(f"Error getting cart summary: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while retrieving cart information.'
        }, status=500)


@require_http_methods(["GET"])
def get_applied_coupon_api(request):
    """
    API endpoint to get details of currently applied coupon
    
    GET /api/cart/coupon/
    Response: {
        "applied": true/false,
        "coupon_code": "CODE",
        "discount_type": "percentage"/"fixed_amount",
        "discount_value": X,
        "discount_amount": Y,
        "message": "..."
    }
    """
    try:
        cart = get_user_cart(request)
        
        if not cart.applied_coupon:
            return JsonResponse({
                'applied': False,
                'message': 'No coupon is currently applied.'
            })
        
        coupon = cart.applied_coupon
        response = {
            'applied': True,
            'coupon_code': coupon.coupon_code,
            'discount_type': coupon.discount_type,
            'discount_value': float(coupon.discount_value),
            'discount_amount': float(cart.discount_amount),
            'discount_display': coupon.get_discount_display(),
            'message': f'Coupon {coupon.coupon_code} is applied!'
        }
        
        return JsonResponse(response)
        
    except Exception as e:
        logger.error(f"Error getting applied coupon: {e}", exc_info=True)
        return JsonResponse({
            'applied': False,
            'message': 'An error occurred while retrieving coupon information.'
        }, status=500)
