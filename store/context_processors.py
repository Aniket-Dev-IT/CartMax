from .models import Cart, Category, ProductComparison
import requests
from decimal import Decimal
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Default exchange rates (fallback if API fails)
DEFAULT_RATES = {
    'USD_TO_INR': Decimal('83.25'),
    'INR_TO_USD': Decimal('0.012')
}

CURRENCY_SYMBOLS = {
    'USD': '$',
    'INR': '₹'
}

SUPPORTED_CURRENCIES = ['USD', 'INR']

def get_exchange_rates():
    """
    Get current exchange rates from cache or API
    Uses free API service or falls back to default rates
    """
    cached_rates = cache.get('currency_exchange_rates')
    if cached_rates:
        logger.debug("Using cached exchange rates")
        return cached_rates
    
    try:
        # Try to fetch from a free exchange rate API (example: exchangerate.host)
        # You can replace this with your preferred API
        response = requests.get(
            'https://api.exchangerate.host/latest?base=USD&symbols=INR',
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'rates' in data:
                usd_to_inr = Decimal(str(data['rates']['INR']))
                inr_to_usd = 1 / usd_to_inr
                
                rates = {
                    'USD_TO_INR': usd_to_inr,
                    'INR_TO_USD': inr_to_usd.quantize(Decimal('0.001'))
                }
                
                # Cache for 1 hour
                cache.set('currency_exchange_rates', rates, 3600)
                logger.info(f"Updated exchange rates: 1 USD = {usd_to_inr} INR")
                return rates
    except Exception as e:
        logger.warning(f"Failed to fetch exchange rates: {e}")
    
    # Fallback to default rates
    logger.info("Using default exchange rates")
    cache.set('currency_exchange_rates', DEFAULT_RATES, 1800)  # Cache for 30 minutes
    return DEFAULT_RATES

def convert_price(amount, from_currency, to_currency, rates=None):
    """
    Convert price between USD and INR - DEPRECATED
    This function is kept for backward compatibility but should not be used
    for products with manual dual currency pricing.
    
    For new products, use product.get_price(currency) instead.
    """
    if not amount or from_currency == to_currency:
        return Decimal(str(amount)) if amount else Decimal('0')
    
    if not rates:
        rates = get_exchange_rates()
    
    amount = Decimal(str(amount))
    
    if from_currency == 'USD' and to_currency == 'INR':
        return amount * rates['USD_TO_INR']
    elif from_currency == 'INR' and to_currency == 'USD':
        return amount * rates['INR_TO_USD']
    
    return amount

def get_product_price(product, currency='INR'):
    """
    Get product price in specified currency using manual admin-set prices.
    This replaces automatic conversion for better price control.
    """
    if hasattr(product, 'get_price'):
        # New dual currency products
        return product.get_price(currency)
    else:
        # Legacy products - convert if needed
        if currency == 'INR':
            return product.price or Decimal('0')
        elif currency == 'USD':
            # Convert legacy INR price to USD
            return convert_price(product.price, 'INR', 'USD')
    
    return Decimal('0')

def format_currency(amount, currency):
    """
    Format currency amount with proper symbol and formatting
    """
    if not amount:
        return f"{CURRENCY_SYMBOLS.get(currency, currency)} 0"
    
    amount = Decimal(str(amount))
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    
    if currency == 'INR':
        # Indian number format (₹1,23,456.78)
        formatted = f"{amount:,.0f}" if amount == amount.to_integral_value() else f"{amount:,.2f}"
    else:
        # US number format ($1,234.56)
        formatted = f"{amount:,.2f}"
    
    return f"{symbol}{formatted}"

def cart_context(request):
    """
    Context processor to provide cart information and categories across all templates
    """
    cart = None
    cart_items_count = 0
    comparison_count = 0
    
    if request.user.is_authenticated:
        # For authenticated users, get or create cart
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items_count = cart.get_total_items()
        
        # Get comparison count for authenticated users
        try:
            comparison = ProductComparison.objects.get(user=request.user)
            comparison_count = comparison.get_product_count()
        except ProductComparison.DoesNotExist:
            comparison_count = 0
    else:
        # For anonymous users, use session-based cart
        if not hasattr(request, 'session'):
            return {
                'cart': None, 
                'cart_items_count': 0,
                'comparison_count': 0,
                'categories': Category.objects.filter(is_active=True)[:8]
            }
            
        session_key = request.session.session_key
        if session_key:
            try:
                cart = Cart.objects.get(session_key=session_key, user__isnull=True)
                cart_items_count = cart.get_total_items()
            except Cart.DoesNotExist:
                pass
            
            # Get comparison count for anonymous users
            try:
                comparison = ProductComparison.objects.get(session_key=session_key, user__isnull=True)
                comparison_count = comparison.get_product_count()
            except ProductComparison.DoesNotExist:
                comparison_count = 0
    
    # Get active categories for navigation
    categories = Category.objects.filter(is_active=True)[:8]
    
    # Currency functionality
    # Get user's preferred currency from session or default to INR
    preferred_currency = request.session.get('preferred_currency', 'INR')
    
    # Validate currency
    if preferred_currency not in SUPPORTED_CURRENCIES:
        preferred_currency = 'INR'
        request.session['preferred_currency'] = preferred_currency
    
    # Get current exchange rates
    rates = get_exchange_rates()
    
    return {
        'cart': cart,
        'cart_items_count': cart_items_count,
        'comparison_count': comparison_count,
        'categories': categories,
        # Manual dual currency context
        'current_currency': preferred_currency,
        'supported_currencies': SUPPORTED_CURRENCIES,
        'currency_symbols': CURRENCY_SYMBOLS,
        'exchange_rates': rates,  # Keep for backward compatibility
        'currency_converter': {
            'get_product_price': get_product_price,  # New manual price getter
            'convert_price': lambda amount, from_curr, to_curr: convert_price(amount, from_curr, to_curr, rates),  # Legacy
            'format_currency': format_currency,
        },
        # Manual currency helper
        'manual_currency_mode': True,
        # Helper functions for templates
        'get_price_for_currency': lambda product, currency=None: get_product_price(product, currency or preferred_currency),
        'get_original_price_for_currency': lambda product, currency=None: product.get_original_price(currency or preferred_currency) if hasattr(product, 'get_original_price') else None,
    }
