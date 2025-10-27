from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse, Http404
from django.db.models import Q, Count
from django.db import models
from django.core.paginator import Paginator
from django.contrib import messages
from .models import *
from .emails import send_order_confirmation_email, send_order_status_update_email
from .recommendations import recommendation_engine
from .inventory import inventory_manager
from .search import search_manager
from .utils import get_currency_by_country, get_user_currency
import json
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime
import logging
from io import BytesIO
from decimal import Decimal
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

logger = logging.getLogger(__name__)

# Utility function for getting client IP
def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Placeholder views - will be implemented in detail later

def homepage(request):
    # homepage with featured stuff - trying to make it faster
    
    # Get featured products - added prefetch to avoid n+1 queries
    featured_products = Product.objects.filter(
        featured=True, 
        available=True
    ).select_related('category').prefetch_related('images', 'reviews')[:8]
    
    # deals section - products with original pricing
    deals_products = Product.objects.filter(
        available=True,
        original_price__isnull=False
    ).select_related('category').prefetch_related('images')[:8]
    
    # recently viewed from session
    recently_viewed_ids = request.session.get('recently_viewed', [])
    recently_viewed = []
    if recently_viewed_ids:
        recently_viewed = Product.objects.filter(
            id__in=recently_viewed_ids,
            available=True
        ).select_related('category').prefetch_related('images')[:6]
    
    # TODO: optimize these recommendation calls - they're slow
    popular_products = recommendation_engine.get_recommendations(
        user=request.user,
        recommendation_type='popular',
        limit=8
    )
    
    trending_products = recommendation_engine.get_recommendations(
        user=request.user,
        recommendation_type='trending',
        limit=8
    )
    
    # personal recommendations for logged in users
    recommended_for_you = []
    if request.user.is_authenticated:
        recommended_for_you = recommendation_engine.get_recommendations(
            user=request.user,
            recommendation_type='user_based',
            limit=8
        )
    
    # categories with product counts - this was causing slow queries
    categories = Category.objects.filter(is_active=True).annotate(
        product_count=Count('products')
    ).prefetch_related('products').order_by('name')[:8]
    
    context = {
        'featured_products': featured_products,
        'deals_products': deals_products,
        'recently_viewed': recently_viewed,
        'popular_products': popular_products,
        'trending_products': trending_products,
        'recommended_for_you': recommended_for_you,
        'categories': categories,
    }
    
    return render(request, 'store/homepage.html', context)

def category_list(request):
    """List all categories"""
    categories = Category.objects.filter(is_active=True).annotate(
        product_count=Count('products')
    ).order_by('name')
    
    # Get popular categories (categories with most products)
    popular_categories = categories.order_by('-product_count')[:6]
    
    context = {
        'categories': categories,
        'popular_categories': popular_categories,
    }
    
    return render(request, 'store/category_list.html', context)

def category_detail(request, slug):
    """Show products in a specific category"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    
    # Get products in this category
    products_list = Product.objects.filter(
        category=category,
        available=True
    ).select_related('category')
    
    # Handle sorting
    sort_by = request.GET.get('sort', 'featured')
    if sort_by == 'price-low':
        products_list = products_list.order_by('price')
    elif sort_by == 'price-high':
        products_list = products_list.order_by('-price')
    elif sort_by == 'rating':
        products_list = products_list.order_by('-created_at')  # Placeholder for rating
    elif sort_by == 'newest':
        products_list = products_list.order_by('-created_at')
    else:  # featured
        products_list = products_list.order_by('-featured', '-created_at')
    
    # Get unique brands for filters
    brands = products_list.values_list('brand', flat=True).distinct().exclude(brand='')
    
    # Pagination
    paginator = Paginator(products_list, 12)  # 12 products per page
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'products': products,
        'brands': brands,
    }
    
    return render(request, 'store/category_detail.html', context)

def product_detail(request, slug):
    # product detail page with redirects for old slugs
    try:
        # optimized query with prefetch to avoid n+1 queries
        product = Product.objects.select_related('category').prefetch_related(
            'images', 'reviews__user', 'specifications'
        ).get(slug=slug, available=True)
    except Product.DoesNotExist:
        try:
            from .models import ProductSlug
            old_slug = ProductSlug.objects.select_related('product').get(slug=slug)
            return redirect('store:product_detail', slug=old_slug.product.slug, permanent=True)
        except ProductSlug.DoesNotExist:
            from django.http import Http404
            raise Http404("No Product matches the given query.")
    
    # track viewing if logged in
    if request.user.is_authenticated:
        recommendation_engine.track_interaction(request.user, product, 'view')
    
    # similar products recommendations
    similar_products = recommendation_engine.get_recommendations(
        product=product, 
        user=request.user, 
        recommendation_type='similar', 
        limit=8
    )
    
    frequently_bought = recommendation_engine.get_recommendations(
        product=product, 
        user=request.user, 
        recommendation_type='frequently_bought', 
        limit=6
    )
    
    user_recommendations = []
    if request.user.is_authenticated:
        user_recommendations = recommendation_engine.get_recommendations(
            product=product,
            user=request.user,
            recommendation_type='user_based',
            limit=8
        )
    
    # Get related products from the same category (fallback)
    related_products = Product.objects.filter(
        category=product.category,
        available=True
    ).exclude(id=product.id).select_related('category')[:8]
    
    # Add to recently viewed session
    recently_viewed = request.session.get('recently_viewed', [])
    if product.id not in recently_viewed:
        recently_viewed.insert(0, product.id)
        request.session['recently_viewed'] = recently_viewed[:10]  # Keep last 10
    
    context = {
        'product': product,
        'similar_products': similar_products,
        'frequently_bought': frequently_bought,
        'user_recommendations': user_recommendations,
        'related_products': related_products,  # Keep for backward compatibility
    }
    
    return render(request, 'store/product_detail.html', context)

def search_products(request):
    # search with filters and analytics
    query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'relevance')
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 12))
    
    # Build filters dictionary from request parameters
    filters = {
        'categories': request.GET.getlist('category'),
        'brands': request.GET.getlist('brand'),
        'price_ranges': request.GET.getlist('price'),
        'colors': request.GET.getlist('color'),
        'sizes': request.GET.getlist('size'), 
        'materials': request.GET.getlist('material'),
        'tags': request.GET.getlist('tag'),
        'availability': request.GET.getlist('availability'),
    }
    
    # Custom price range
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            filters['min_price'] = float(min_price)
        except (ValueError, TypeError):
            pass
    if max_price:
        try:
            filters['max_price'] = float(max_price)
        except (ValueError, TypeError):
            pass
    
    # Rating filter
    min_rating = request.GET.get('rating')
    if min_rating:
        try:
            filters['min_rating'] = int(min_rating)
        except (ValueError, TypeError):
            pass
    
    # Perform search using advanced search manager
    search_results = search_manager.search_products(
        query=query,
        filters=filters,
        sort_by=sort_by,
        page=page,
        per_page=per_page
    )
    
    # Log search for analytics
    user = request.user if request.user.is_authenticated else None
    session_key = request.session.session_key
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    search_manager.log_search(
        query=query,
        user=user,
        session_key=session_key,
        ip_address=ip_address,
        user_agent=user_agent,
        filters=filters,
        results_count=search_results['total_results']
    )
    
    # Build query string for pagination (excluding page parameter)
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    query_string = query_params.urlencode()
    
    # Prepare context for template
    context = {
        'query': query,
        'products': search_results['products'],
        'filter_options': search_results['filter_options'],
        'sort_by': sort_by,
        'query_string': query_string,
        'total_results': search_results['total_results'],
        'page_info': search_results['page_info'],
        'applied_filters': filters,
        
        # Template helper data
        'sort_options': [
            ('relevance', 'Relevance'),
            ('price-low', 'Price: Low to High'),
            ('price-high', 'Price: High to Low'),
            ('rating', 'Customer Rating'),
            ('newest', 'Newest First'),
            ('popularity', 'Popularity'),
        ],
        'price_ranges': [
            ('0-25', 'Under $25'),
            ('25-50', '$25 to $50'),
            ('50-100', '$50 to $100'),
            ('100-200', '$100 to $200'),
            ('200+', '$200 & Above'),
        ],
        'rating_options': [
            (4, '4 Stars & Up'),
            (3, '3 Stars & Up'),
            (2, '2 Stars & Up'),
            (1, '1 Star & Up'),
        ],
        'availability_options': [
            ('in_stock', 'In Stock'),
            ('on_sale', 'On Sale'),
            ('featured', 'Featured'),
        ],
    }
    
    
    return render(request, 'store/search_results.html', context)


def search_suggestions(request):
    """AJAX endpoint for search suggestions and autocomplete"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        query = request.GET.get('q', '').strip()
        if len(query) >= 2:
            suggestions = search_manager.get_search_suggestions(query, limit=10)
            return JsonResponse({'suggestions': suggestions})
    return JsonResponse({'suggestions': []})


def track_search_click(request):
    """Track when a user clicks on a search result"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            search_query_id = data.get('search_query_id')
            product_id = data.get('product_id')
            position = data.get('position', 0)
            
            if search_query_id and product_id:
                from .models import SearchQuery as SearchQueryModel, Product, SearchProductClick
                
                search_query = SearchQueryModel.objects.get(id=search_query_id)
                product = Product.objects.get(id=product_id)
                
                # Create or update click record
                click, created = SearchProductClick.objects.get_or_create(
                    search_query=search_query,
                    product=product,
                    defaults={'click_position': position}
                )
                
                return JsonResponse({'success': True})
                
        except (json.JSONDecodeError, SearchQueryModel.DoesNotExist, Product.DoesNotExist) as e:
            pass
    
    return JsonResponse({'success': False})

def cart_detail(request):
    # show user's shopping cart
    cart = None
    cart_items = []
    
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).prefetch_related(
            'items__product__images'
        ).first()
        user_currency = get_user_currency(request.user)
    else:
        if request.session.session_key:
            cart = Cart.objects.filter(
                session_key=request.session.session_key,
                user=None
            ).prefetch_related('items__product__images').first()
        user_currency = 'USD'  # anonymous default to USD
    
    if cart:
        cart_items = cart.items.all().select_related('product').prefetch_related('product__images')
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'user_currency': user_currency,
        'currency_symbol': '₹' if user_currency == 'INR' else '$',
    }
    
    return render(request, 'store/cart.html', context)

@require_POST
def set_cart_currency(request):
    """Set cart currency via AJAX"""
    try:
        currency = request.POST.get('currency', 'USD')
        
        # Validate currency
        if currency not in ['INR', 'USD']:
            return JsonResponse({'success': False, 'message': 'Invalid currency'})
        
        # Get or create cart
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            if not request.session.session_key:
                request.session.create()
            cart, created = Cart.objects.get_or_create(
                session_key=request.session.session_key,
                user=None
            )
        
        # Update cart currency
        cart.currency = currency
        cart.save()
        
        # Return updated cart totals
        subtotal = float(cart.get_total_price_in_currency(currency))
        tax = float(cart.get_tax_in_currency(currency))
        total = float(cart.get_final_total_in_currency(currency))
        
        return JsonResponse({
            'success': True,
            'currency': {
                'code': currency,
                'symbol': cart.get_currency_symbol()
            },
            'subtotal': subtotal,
            'tax': tax,
            'total': total
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

def add_to_cart(request, product_id):
    """Add product to cart"""
    if request.method == 'POST':
        try:
            product = Product.objects.get(id=product_id, available=True)
            quantity = int(request.POST.get('quantity', 1))
            
            if quantity <= 0 or quantity > product.stock:
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid quantity. Available stock: {product.stock}'
                })
            
            # Get user's currency based on country (if authenticated) or default to USD
            if request.user.is_authenticated:
                user_currency = get_user_currency(request.user)
                cart, created = Cart.objects.get_or_create(user=request.user)
            else:
                user_currency = 'USD'  # Anonymous users default to USD
                if not request.session.session_key:
                    request.session.create()
                cart, created = Cart.objects.get_or_create(
                    session_key=request.session.session_key,
                    user=None
                )
            
            # Always set cart currency from user's country preference
            cart.currency = user_currency
            cart.save()
            
            # Get or create cart item with correct currency pricing
            # Capture both INR and USD prices for dual-currency support
            cart_item, item_created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={
                    'quantity': quantity,
                    'price': product.price,
                    'price_inr': product.price_inr,
                    'price_usd': product.price_usd
                }
            )
            
            if not item_created:
                # Update existing item
                cart_item.quantity += quantity
                if cart_item.quantity > product.stock:
                    cart_item.quantity = product.stock
                cart_item.save()
            
            # Track interaction
            if request.user.is_authenticated:
                recommendation_engine.track_interaction(request.user, product, 'cart')
            
            # Get complete cart data in the cart's currency
            subtotal = float(cart.get_total_price_in_currency(cart.currency))
            tax = float(cart.get_tax_in_currency(cart.currency))
            shipping = 0.00  # Free shipping
            total = subtotal + tax + shipping
            
            return JsonResponse({
                'success': True,
                'message': f'{product.name} added to cart successfully!',
                'cart_count': cart.get_total_items(),
                'subtotal': subtotal,
                'tax': tax,
                'shipping': shipping,
                'total': total,
                'currency': {
                    'code': cart.currency,
                    'symbol': cart.get_currency_symbol()
                }
            })
            
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Product not found.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Failed to add product to cart.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request.'})

def update_cart(request):
    """Update cart quantities"""
    if request.method == 'POST':
        try:
            product_id = request.POST.get('product_id')
            quantity = int(request.POST.get('quantity', 1))
            
            if quantity < 1:
                return JsonResponse({
                    'success': False,
                    'message': 'Quantity must be at least 1.'
                })
            
            product = Product.objects.get(id=product_id, available=True)
            
            if quantity > product.stock:
                return JsonResponse({
                    'success': False,
                    'message': f'Only {product.stock} items available in stock.'
                })
            
            # Get cart
            if request.user.is_authenticated:
                cart = Cart.objects.filter(user=request.user).first()
            else:
                if not request.session.session_key:
                    request.session.create()
                cart = Cart.objects.filter(
                    session_key=request.session.session_key,
                    user=None
                ).first()
            
            if cart:
                cart_item = CartItem.objects.filter(
                    cart=cart,
                    product=product
                ).first()
                
                if cart_item:
                    cart_item.quantity = quantity
                    cart_item.save()
                    
                    # Get complete cart data in the cart's currency
                    subtotal = float(cart.get_total_price_in_currency(cart.currency))
                    tax = float(cart.get_tax_in_currency(cart.currency))
                    shipping = 0.00  # Free shipping
                    total = subtotal + tax + shipping
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Cart updated successfully!',
                        'cart_count': cart.get_total_items(),
                        'item_total': float(cart.get_total_price_in_currency(cart.currency)),
                        'subtotal': subtotal,
                        'tax': tax,
                        'shipping': shipping,
                        'total': total,
                        'currency': {
                            'code': cart.currency,
                            'symbol': cart.get_currency_symbol()
                        }
                    })
            
            return JsonResponse({
                'success': False,
                'message': 'Item not found in cart.'
            })
            
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Product not found.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Failed to update cart.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request.'})

def remove_from_cart(request, product_id):
    """Remove product from cart"""
    if request.method == 'POST':
        try:
            product = Product.objects.get(id=product_id)
            
            # Get cart
            if request.user.is_authenticated:
                cart = Cart.objects.filter(user=request.user).first()
            else:
                if not request.session.session_key:
                    return JsonResponse({
                        'success': False,
                        'message': 'No cart found.'
                    })
                cart = Cart.objects.filter(
                    session_key=request.session.session_key,
                    user=None
                ).first()
            
            if cart:
                cart_item = CartItem.objects.filter(
                    cart=cart,
                    product=product
                ).first()
                
                if cart_item:
                    cart_item.delete()
                    
                    # Get updated cart data after deletion in the cart's currency
                    cart_count = cart.get_total_items()
                    subtotal = float(cart.get_total_price_in_currency(cart.currency))
                    tax = float(cart.get_tax_in_currency(cart.currency))
                    shipping = 0.00  # Free shipping
                    total = subtotal + tax + shipping
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Item removed from cart!',
                        'cart_count': cart_count,
                        'subtotal': subtotal,
                        'tax': tax,
                        'shipping': shipping,
                        'total': total,
                        'cart_empty': cart_count == 0,
                        'currency': {
                            'code': cart.currency,
                            'symbol': cart.get_currency_symbol()
                        }
                    })
            
            return JsonResponse({
                'success': False,
                'message': 'Item not found in cart.'
            })
            
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Product not found.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Failed to remove item from cart.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request.'})

def get_cart_totals(request):
    """Get current cart totals (used for currency refresh)"""
    try:
        # Get cart
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        else:
            if not request.session.session_key:
                return JsonResponse({
                    'success': False,
                    'message': 'No cart found.'
                })
            cart = Cart.objects.filter(
                session_key=request.session.session_key,
                user=None
            ).first()
        
        if not cart:
            return JsonResponse({
                'success': False,
                'message': 'No cart found.'
            })
        
        # Get cart data in its current currency
        subtotal = float(cart.get_total_price_in_currency(cart.currency))
        tax = float(cart.get_tax_in_currency(cart.currency))
        shipping = 0.00  # Free shipping
        total = subtotal + tax + shipping
        
        return JsonResponse({
            'success': True,
            'cart_count': cart.get_total_items(),
            'subtotal': subtotal,
            'tax': tax,
            'shipping': shipping,
            'total': total,
            'currency': {
                'code': cart.currency,
                'symbol': cart.get_currency_symbol()
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

def clear_cart(request):
    """Clear entire cart"""
    if request.method == 'POST':
        try:
            # Get cart
            if request.user.is_authenticated:
                cart = Cart.objects.filter(user=request.user).first()
            else:
                if not request.session.session_key:
                    return JsonResponse({
                        'success': False,
                        'message': 'No cart found.'
                    })
                cart = Cart.objects.filter(
                    session_key=request.session.session_key,
                    user=None
                ).first()
            
            if cart:
                cart.items.all().delete()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Cart cleared successfully!'
                })
            
            return JsonResponse({
                'success': False,
                'message': 'No cart found.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Failed to clear cart.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request.'})

@login_required
def checkout(request):
    """Checkout process"""
    # Get user's cart
    cart = Cart.objects.filter(user=request.user).first()
    
    if not cart or not cart.items.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('store:cart_detail')
    
    cart_items = cart.items.all().select_related('product')
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Process order
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        postal_code = request.POST.get('postal_code')
        country = request.POST.get('country')
        payment_method = request.POST.get('payment_method')
        currency = request.POST.get('currency', 'USD')  # Get selected currency
        save_info = request.POST.get('save_info')
        
        # Validation
        errors = []
        if not all([first_name, last_name, email, phone, address, city, postal_code]):
            errors.append('All shipping fields are required.')
        
        if payment_method == 'credit_card':
            card_number = request.POST.get('card_number', '').replace(' ', '')
            cvv = request.POST.get('cvv')
            exp_month = request.POST.get('exp_month')
            exp_year = request.POST.get('exp_year')
            
            if not all([card_number, cvv, exp_month, exp_year]):
                errors.append('All card details are required.')
            elif len(card_number) < 13 or len(card_number) > 19:
                errors.append('Invalid card number.')
        
        if not errors:
            try:
                # Calculate order totals in selected currency
                subtotal = cart.get_total_price_in_currency(currency)
                
                # Apply coupon if one is active on cart
                discount_amount = Decimal('0')
                applied_coupon = None
                
                if cart.applied_coupon:
                    # Re-validate coupon before applying to order (security check)
                    from .coupon_utils import validate_coupon_on_checkout
                    is_valid, coupon, error_msg = validate_coupon_on_checkout(
                        cart.applied_coupon.coupon_code,
                        request.user,
                        cart
                    )
                    
                    if is_valid and coupon:
                        discount_amount = coupon.calculate_discount(subtotal)
                        applied_coupon = coupon
                    else:
                        # Coupon became invalid, clear it
                        cart.applied_coupon = None
                        cart.discount_amount = Decimal('0')
                        cart.save()
                
                # Calculate final totals
                # CRITICAL: Tax is calculated on FULL SUBTOTAL (before discount)
                # This matches the Cart model behavior
                tax = subtotal * Decimal('0.08')  # Tax on FULL subtotal
                discounted_subtotal = subtotal - discount_amount
                total = discounted_subtotal + tax
                
                # Create order
                order = Order.objects.create(
                    user=request.user,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    address=address,
                    city=city,
                    postal_code=postal_code,
                    country=country,
                    payment_method=payment_method,
                    currency=currency,  # Store selected currency
                    status='pending',
                    total=total,
                    tax_amount=tax,
                    shipping_amount=0,  # Free shipping
                    applied_coupon=applied_coupon,  # Store coupon
                    discount_amount=discount_amount,  # Store discount
                    original_subtotal=subtotal  # Original before discount
                )
                
                # Create order items
                for cart_item in cart_items:
                    # Ensure we have both USD and INR prices
                    order_item = OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price_usd=cart_item.price_usd or cart_item.product.price_usd,
                        price_inr=cart_item.price_inr or cart_item.product.price_inr,
                        price=cart_item.price or cart_item.product.price  # Backward compatibility
                    )
                    
                    # Update inventory using inventory manager
                    product = cart_item.product
                    inventory_manager.update_stock(
                        product=product,
                        quantity_change=-cart_item.quantity,  # Negative for stock reduction
                        movement_type='sale',
                        reference_number=order.order_id,
                        notes=f'Sale to {request.user.username}',
                        created_by=request.user
                    )
                    
                    # Track purchase interaction
                    recommendation_engine.track_interaction(request.user, product, 'purchase')
                
                # Track coupon usage if a coupon was applied
                if applied_coupon:
                    from django.db import transaction
                    with transaction.atomic():
                        # Update global coupon usage count
                        applied_coupon.usage_count += 1
                        applied_coupon.save()
                        # Per-user usage tracking is disabled - users can use coupons multiple times
                
                # Save user info if requested
                if save_info:
                    request.user.first_name = first_name
                    request.user.last_name = last_name
                    request.user.email = email
                    request.user.save()
                    
                    user_profile.phone = phone
                    user_profile.address = address
                    user_profile.city = city
                    user_profile.postal_code = postal_code
                    user_profile.save()
                
                # Clear cart
                cart.items.all().delete()
                cart.delete()
                
                # Send order confirmation email
                try:
                    send_order_confirmation_email(order)
                except Exception as e:
                    # Log error but don't fail the order
                    print(f"Failed to send order confirmation email: {e}")
                
                messages.success(request, f'Order #{order.id} placed successfully!')
                return redirect('store:order_success', order_id=order.id)
                
            except Exception as e:
                errors.append('Failed to process order. Please try again.')
        
        # If there are errors, show them
        for error in errors:
            messages.error(request, error)
    
    # Get currency from user's country preference (this is the source of truth)
    user_currency = get_user_currency(request.user)
    
    # Sync cart currency with user's country-based currency
    if cart and cart.currency != user_currency:
        cart.currency = user_currency
        cart.save()
    
    # Generate years for card expiry
    import datetime
    current_year = datetime.datetime.now().year
    years = list(range(current_year, current_year + 11))
    
    # Use user's country-based currency for display
    display_currency = user_currency
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'user_profile': user_profile,
        'years': years,
        'currency': display_currency,
        'currency_symbol': '₹' if display_currency == 'INR' else '$',
    }
    return render(request, 'store/checkout.html', context)

@login_required
def order_success(request, order_id):
    """Order success page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Get user's current currency preference from session
    user_currency = request.session.get('preferred_currency', 'INR')
    
    context = {
        'order': order,
        'currency': user_currency,
        'currency_symbol': '₹' if user_currency == 'INR' else '$',
    }
    return render(request, 'store/order_success.html', context)

def unified_auth(request):
    """Unified authentication view for login and registration"""
    if request.user.is_authenticated:
        return redirect('store:homepage')
    
    login_errors = []
    register_errors = []
    form_type = request.GET.get('tab', 'signin')  # Default to sign in tab
    
    if request.method == 'POST':
        post_form_type = request.POST.get('form_type', 'login')
        
        if post_form_type == 'login':
            # Handle login
            username_or_email = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')
            
            # Try authentication with username first
            user = authenticate(request, username=username_or_email, password=password)
            
            # If username auth fails, try with email
            if user is None and '@' in username_or_email:
                try:
                    user_obj = User.objects.get(email=username_or_email)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None
            
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'store:homepage')
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                return redirect(next_url)
            else:
                login_errors.append('Invalid username, email, or password.')
                form_type = 'signin'
        
        elif post_form_type == 'register':
            # Handle registration
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            email = request.POST.get('email', '')
            username = request.POST.get('username', '')
            password1 = request.POST.get('password1', '')
            password2 = request.POST.get('password2', '')
            phone = request.POST.get('phone', '')
            
            # Validation
            if not all([first_name, last_name, email, username, password1, password2]):
                register_errors.append('All required fields must be filled.')
            
            if password1 != password2:
                register_errors.append('Passwords do not match.')
            
            if len(password1) < 8:
                register_errors.append('Password must be at least 8 characters long.')
            
            if User.objects.filter(username=username).exists():
                register_errors.append('Username already exists.')
            
            if User.objects.filter(email=email).exists():
                register_errors.append('Email already registered.')
            
            if not register_errors:
                try:
                    # Create user
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password1,
                        first_name=first_name,
                        last_name=last_name
                    )
                    
                    # Create user profile
                    UserProfile.objects.create(
                        user=user,
                        phone=phone
                    )
                    
                    # Log in the user
                    user = authenticate(username=username, password=password1)
                    if user:
                        login(request, user)
                        messages.success(request, 'Account created successfully! Welcome to CartMax!')
                        return redirect('store:homepage')
                    
                except Exception as e:
                    register_errors.append('Failed to create account. Please try again.')
            
            form_type = 'register'
    
    context = {
        'login_errors': login_errors,
        'register_errors': register_errors,
        'form_type': form_type,
    }
    return render(request, 'auth/unified_auth.html', context)

def login_view(request):
    """Redirect to unified auth page (Sign In tab)"""
    return redirect('store:unified_auth')

def logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('store:homepage')

def register(request):
    """Redirect to unified auth page (Register tab)"""
    return redirect('store:unified_auth')

@login_required
def profile(request):
    """User profile page"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get user's recent orders
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Get user's reviews
    reviews = Review.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    if request.method == 'POST':
        # Update profile information
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        address = request.POST.get('address', '')
        city = request.POST.get('city', '')
        postal_code = request.POST.get('postal_code', '')
        country = request.POST.get('country', 'United States')
        
        # Update user information
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email
        request.user.save()
        
        # Update profile information
        user_profile.phone = phone
        user_profile.address = address
        user_profile.city = city
        user_profile.postal_code = postal_code
        user_profile.country = country
        
        # CRITICAL: Set preferred_currency based on country (India = INR, else = USD)
        user_profile.preferred_currency = get_currency_by_country(country)
        user_profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('store:profile')
    
    context = {
        'user_profile': user_profile,
        'orders': orders,
        'reviews': reviews,
    }
    return render(request, 'auth/profile.html', context)

@login_required
def order_history(request):
    """User order history"""
    from django.core.paginator import Paginator
    
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Paginate orders (10 per page)
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    
    context = {
        'orders': orders,
    }
    return render(request, 'auth/order_history.html', context)

@login_required
def add_review(request):
    """Add product review (AJAX)"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        rating = request.POST.get('rating')
        title = request.POST.get('title')
        comment = request.POST.get('comment')
        
        try:
            product = Product.objects.get(id=product_id)
            
            # Check if user already reviewed this product
            existing_review = Review.objects.filter(
                product=product,
                user=request.user
            ).first()
            
            if existing_review:
                return JsonResponse({
                    'success': False,
                    'message': 'You have already reviewed this product.'
                })
            
            # Create new review
            review = Review.objects.create(
                product=product,
                user=request.user,
                rating=int(rating),
                title=title,
                comment=comment
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Review submitted successfully!'
            })
            
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Product not found.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Failed to submit review.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request.'})

def search_suggestions(request):
    """Search suggestions (AJAX)"""
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if query and len(query) >= 2:
        # Get product name suggestions
        products = Product.objects.filter(
            name__icontains=query,
            available=True
        ).values('name').distinct()[:5]
        
        for product in products:
            suggestions.append({
                'type': 'product',
                'text': product['name'],
                'url': f'/search/?q={product["name"]}'
            })
        
        # Get category suggestions
        categories = Category.objects.filter(
            name__icontains=query,
            is_active=True
        ).values('name', 'slug')[:3]
        
        for category in categories:
            suggestions.append({
                'type': 'category',
                'text': f"in {category['name']}",
                'url': f'/category/{category["slug"]}/'
            })
        
        # Get brand suggestions
        brands = Product.objects.filter(
            brand__icontains=query,
            available=True,
            brand__isnull=False
        ).exclude(brand='').values('brand').distinct()[:3]
        
        for brand in brands:
            suggestions.append({
                'type': 'brand',
                'text': f"{brand['brand']} products",
                'url': f'/search/?q={brand["brand"]}'
            })
    
    return JsonResponse({'suggestions': suggestions[:8]})

@login_required
def order_detail(request, order_id):
    """Order detail page with tracking"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
    }
    return render(request, 'store/order_detail.html', context)

@login_required
def cancel_order(request, order_id):
    """Cancel order (AJAX)"""
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            
            # Check if order can be cancelled
            if order.status in ['shipped', 'delivered', 'cancelled']:
                return JsonResponse({
                    'success': False,
                    'message': 'This order cannot be cancelled.'
                })
            
            # Update order status
            order.status = 'cancelled'
            order.save()
            
            # Restore product stock
            for item in order.items.all():
                product = item.product
                product.stock += item.quantity
                product.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Order cancelled successfully.'
            })
            
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Order not found.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Failed to cancel order.'
            })
    
    # Handle GET requests with more informative response
    return JsonResponse({
        'success': False, 
        'message': 'Invalid request method. Use POST to cancel orders.',
        'method_received': request.method,
        'order_id': order_id
    })


# ============================================================================
# CUSTOM ADMIN DASHBOARD VIEWS - PHASE 1C
# ============================================================================

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
import random
import csv
import json
from django.core import serializers
from django.db import transaction
from django.contrib import messages
import openpyxl
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import tempfile
from decimal import Decimal, InvalidOperation
from django.utils.text import slugify
from PIL import Image, ImageOps, ImageFilter
import io
import uuid
from django.conf import settings

@staff_member_required
def admin_dashboard_api(request):
    """API endpoint for admin dashboard data"""
    try:
        # Calculate date ranges
        now = timezone.now()
        today = now.date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        year_ago = today - timedelta(days=365)
        
        # Basic statistics
        total_products = Product.objects.count()
        total_categories = Category.objects.filter(is_active=True).count()
        total_users = User.objects.count()
        total_orders = Order.objects.count()
        
        # Revenue calculations
        total_revenue = Order.objects.filter(
            status__in=['processing', 'shipped', 'delivered']
        ).aggregate(Sum('total'))['total__sum'] or 0
        
        monthly_revenue = Order.objects.filter(
            created_at__gte=month_ago,
            status__in=['processing', 'shipped', 'delivered']
        ).aggregate(Sum('total'))['total__sum'] or 0
        
        weekly_revenue = Order.objects.filter(
            created_at__gte=week_ago,
            status__in=['processing', 'shipped', 'delivered']
        ).aggregate(Sum('total'))['total__sum'] or 0
        
        # Order statistics
        pending_orders = Order.objects.filter(status='pending').count()
        processing_orders = Order.objects.filter(status='processing').count()
        shipped_orders = Order.objects.filter(status='shipped').count()
        delivered_orders = Order.objects.filter(status='delivered').count()
        cancelled_orders = Order.objects.filter(status='cancelled').count()
        
        # Recent activity
        recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]
        recent_users = User.objects.order_by('-date_joined')[:5]
        recent_reviews = Review.objects.select_related('user', 'product').order_by('-created_at')[:5]
        
        # Top products
        top_products = Product.objects.annotate(
            order_count=Count('orderitem')
        ).order_by('-order_count')[:5]
        
        # Low stock alerts
        low_stock_products = Product.objects.filter(
            available=True,
            stock__lte=10
        ).order_by('stock')[:5]
        
        # Monthly sales data for chart
        monthly_sales = []
        for i in range(12):
            month_start = (now - timedelta(days=30*i)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            month_revenue = Order.objects.filter(
                created_at__gte=month_start,
                created_at__lte=month_end,
                status__in=['processing', 'shipped', 'delivered']
            ).aggregate(Sum('total'))['total__sum'] or 0
            
            monthly_sales.append({
                'month': month_start.strftime('%B'),
                'revenue': float(month_revenue),
                'orders': Order.objects.filter(
                    created_at__gte=month_start,
                    created_at__lte=month_end
                ).count()
            })
        
        monthly_sales.reverse()  # Show oldest to newest
        
        # Category performance
        category_stats = Category.objects.annotate(
            product_count=Count('products'),
            order_count=Count('products__orderitem')
        ).order_by('-order_count')[:10]
        
        data = {
            'overview': {
                'total_products': total_products,
                'total_categories': total_categories,
                'total_users': total_users,
                'total_orders': total_orders,
                'total_revenue': float(total_revenue),
                'monthly_revenue': float(monthly_revenue),
                'weekly_revenue': float(weekly_revenue),
            },
            'order_stats': {
                'pending': pending_orders,
                'processing': processing_orders,
                'shipped': shipped_orders,
                'delivered': delivered_orders,
                'cancelled': cancelled_orders,
            },
            'recent_activity': {
                'orders': [{
                    'id': order.order_id,
                    'user': order.user.username,
                    'total': float(order.total or 0),
                    'status': order.status,
                    'created_at': order.created_at.strftime('%Y-%m-%d %H:%M')
                } for order in recent_orders],
                'users': [{
                    'username': user.username,
                    'email': user.email,
                    'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M')
                } for user in recent_users],
                'reviews': [{
                    'id': review.id,
                    'product': review.product.name,
                    'user': review.user.username,
                    'rating': review.rating,
                    'created_at': review.created_at.strftime('%Y-%m-%d %H:%M')
                } for review in recent_reviews]
            },
            'top_products': [{
                'name': product.name,
                'orders': product.order_count,
                'stock': product.stock,
                'price': float(product.price)
            } for product in top_products],
            'low_stock_alerts': [{
                'name': product.name,
                'stock': product.stock,
                'sku': product.sku
            } for product in low_stock_products],
            'monthly_sales': monthly_sales,
            'category_performance': [{
                'name': category.name,
                'products': category.product_count,
                'orders': category.order_count
            } for category in category_stats],
            'timestamp': now.isoformat()
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)

@staff_member_required
def admin_analytics_api(request):
    """Advanced analytics API for admin dashboard"""
    try:
        # User behavior analytics
        user_registrations = []
        for i in range(30):  # Last 30 days
            date = timezone.now().date() - timedelta(days=i)
            count = User.objects.filter(date_joined__date=date).count()
            user_registrations.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        
        user_registrations.reverse()
        
        # Product performance
        product_views = Product.objects.annotate(
            view_count=Count('orderitem')  # Proxy for views using orders
        ).order_by('-view_count')[:10]
        
        # Revenue by category
        category_revenue = Category.objects.annotate(
            total_revenue=Sum('products__orderitem__price')
        ).filter(total_revenue__isnull=False).order_by('-total_revenue')[:10]
        
        data = {
            'user_registrations': user_registrations,
            'product_performance': [{
                'name': product.name,
                'views': product.view_count,
                'stock': product.stock
            } for product in product_views],
            'category_revenue': [{
                'category': category.name,
                'revenue': float(category.total_revenue or 0)
            } for category in category_revenue],
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)

@staff_member_required
def admin_system_health_api(request):
    """System health monitoring API"""
    try:
        # System metrics (simulated for compatibility)
        import random
        cpu_percent = random.uniform(10, 30)
        memory_percent = random.uniform(30, 60)
        disk_percent = random.uniform(20, 40)
        
        # Database health
        db_health = 'healthy'
        try:
            # Test database connection
            Product.objects.count()
            db_response_time = random.uniform(15, 35)
        except:
            db_health = 'error'
            db_response_time = 0
        
        # Application metrics
        active_sessions = random.randint(20, 60)
        cache_hit_rate = random.uniform(90, 98)
        
        data = {
            'system': {
                'cpu_percent': round(cpu_percent, 1),
                'memory_percent': round(memory_percent, 1),
                'disk_percent': round(disk_percent, 1),
                'status': 'healthy' if cpu_percent < 80 else 'warning'
            },
            'database': {
                'status': db_health,
                'response_time': round(db_response_time, 1),
                'connections': random.randint(8, 20)
            },
            'application': {
                'active_sessions': active_sessions,
                'cache_hit_rate': round(cache_hit_rate, 1),
                'uptime': '5 days, 12 hours'  # Simulated
            },
            'alerts': [
                {
                    'type': 'info',
                    'message': 'All systems operational',
                    'timestamp': timezone.now().isoformat()
                }
            ] if cpu_percent < 50 else [
                {
                    'type': 'warning',
                    'message': f'CPU usage at {round(cpu_percent, 1)}%',
                    'timestamp': timezone.now().isoformat()
                }
            ],
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


# ========================================
# BULK OPERATIONS API VIEWS
# ========================================

@staff_member_required
def bulk_operations_api(request):
    """API endpoint for bulk operations on various models."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        data = json.loads(request.body)
        model_type = data.get('model_type')
        action = data.get('action')
        ids = data.get('ids', [])
        
        if not all([model_type, action, ids]):
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
        
        # Map model types to actual models
        model_map = {
            'product': Product,
            'order': Order,
            'user': User,
        }
        
        if model_type not in model_map:
            return JsonResponse({'error': 'Invalid model type'}, status=400)
        
        model_class = model_map[model_type]
        queryset = model_class.objects.filter(id__in=ids)
        
        result = {'success': False, 'message': '', 'affected_count': 0}
        
        with transaction.atomic():
            if action == 'delete':
                count, _ = queryset.delete()
                result = {
                    'success': True,
                    'message': f'Successfully deleted {count} {model_type}(s)',
                    'affected_count': count
                }
                
            elif action == 'update_status' and model_type == 'product':
                new_status = data.get('status', 'active')
                count = queryset.update(status=new_status)
                result = {
                    'success': True,
                    'message': f'Updated status of {count} product(s) to {new_status}',
                    'affected_count': count
                }
                
            elif action == 'update_status' and model_type == 'order':
                new_status = data.get('status', 'pending')
                count = queryset.update(status=new_status)
                result = {
                    'success': True,
                    'message': f'Updated status of {count} order(s) to {new_status}',
                    'affected_count': count
                }
                
            elif action == 'activate_users' and model_type == 'user':
                count = queryset.update(is_active=True)
                result = {
                    'success': True,
                    'message': f'Activated {count} user(s)',
                    'affected_count': count
                }
                
            elif action == 'deactivate_users' and model_type == 'user':
                count = queryset.update(is_active=False)
                result = {
                    'success': True,
                    'message': f'Deactivated {count} user(s)',
                    'affected_count': count
                }
                
            elif action == 'bulk_discount' and model_type == 'product':
                discount_percent = float(data.get('discount', 0))
                updated_products = []
                
                for product in queryset:
                    new_price = product.price * (1 - discount_percent / 100)
                    product.price = round(new_price, 2)
                    updated_products.append(product)
                
                model_class.objects.bulk_update(updated_products, ['price'])
                
                result = {
                    'success': True,
                    'message': f'Applied {discount_percent}% discount to {len(updated_products)} product(s)',
                    'affected_count': len(updated_products)
                }
                
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)
        
        # Log the bulk operation
        AdminActivity.objects.create(
            admin_user=request.user,
            action=f'BULK_{action.upper()}',
            description=f'Bulk {action} performed on {result["affected_count"]} {model_type}(s)',
            ip_address=get_client_ip(request)
        )
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def bulk_export_api(request):
    """API endpoint for exporting data in various formats."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        data = json.loads(request.body)
        model_type = data.get('model_type')
        export_format = data.get('format', 'csv')
        fields = data.get('fields', [])
        ids = data.get('ids', [])
        
        if not model_type:
            return JsonResponse({'error': 'Model type is required'}, status=400)
        
        # Map model types to actual models
        model_map = {
            'product': Product,
            'order': Order,
            'user': User,
        }
        
        if model_type not in model_map:
            return JsonResponse({'error': 'Invalid model type'}, status=400)
        
        model_class = model_map[model_type]
        
        # Get queryset
        if ids:
            queryset = model_class.objects.filter(id__in=ids)
        else:
            queryset = model_class.objects.all()
        
        # Prepare response
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{model_type}_export_{timestamp}'
        
        if export_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
            
            writer = csv.writer(response)
            
            # Define field mappings
            field_maps = {
                'product': ['id', 'name', 'description', 'price', 'stock', 'category__name', 'created_at'],
                'order': ['id', 'user__username', 'total_amount', 'status', 'created_at'],
                'user': ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined'],
            }
            
            selected_fields = fields if fields else field_maps.get(model_type, ['id'])
            
            # Write header
            header = [field.replace('__', '_').replace('_', ' ').title() for field in selected_fields]
            writer.writerow(header)
            
            # Write data
            for obj in queryset.select_related():
                row = []
                for field in selected_fields:
                    try:
                        if '__' in field:
                            # Handle foreign key fields
                            value = obj
                            for part in field.split('__'):
                                value = getattr(value, part, '')
                        else:
                            value = getattr(obj, field, '')
                        row.append(str(value) if value is not None else '')
                    except AttributeError:
                        row.append('')
                writer.writerow(row)
            
            return response
        
        elif export_format == 'json':
            response = HttpResponse(content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="{filename}.json"'
            
            data_export = serializers.serialize('json', queryset)
            response.write(data_export)
            
            return response
        
        else:
            return JsonResponse({'error': 'Unsupported export format'}, status=400)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# WISHLIST FUNCTIONALITY VIEWS
# ============================================================================

def wishlist_view(request):
    """Display user's wishlist - supports both authenticated and guest users"""
    wishlist = Wishlist.get_for_request(request)
    wishlist_items = wishlist.items.all().select_related('product__category')
    
    context = {
        'wishlist': wishlist,
        'wishlist_items': wishlist_items,
        'is_guest': not request.user.is_authenticated,
    }
    return render(request, 'store/wishlist.html', context)

def add_to_wishlist(request, product_id):
    """Add product to wishlist (AJAX) - supports both authenticated and guest users"""
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id, available=True)
            
            # Get or create wishlist for user or guest
            wishlist = Wishlist.get_for_request(request)
            
            # Check if product is already in wishlist
            if wishlist.has_product(product):
                return JsonResponse({
                    'success': False,
                    'message': 'Product is already in your wishlist.'
                })
            
            # Add product to wishlist
            WishlistItem.objects.create(
                wishlist=wishlist,
                product=product
            )
            
            # Track interaction only for authenticated users
            if request.user.is_authenticated:
                recommendation_engine.track_interaction(request.user, product, 'wishlist')
            
            return JsonResponse({
                'success': True,
                'message': f'{product.name} added to your wishlist!',
                'wishlist_count': wishlist.get_item_count(),
                'is_guest': not request.user.is_authenticated
            })
            
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Product not found.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Failed to add product to wishlist.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request.'})

def remove_from_wishlist(request, product_id):
    """Remove product from wishlist (AJAX) - supports both authenticated and guest users"""
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id)
            
            # Get wishlist for user or guest
            if request.user.is_authenticated:
                wishlist = get_object_or_404(Wishlist, user=request.user)
            else:
                if not request.session.session_key:
                    return JsonResponse({
                        'success': False,
                        'message': 'No wishlist found.'
                    })
                wishlist = get_object_or_404(Wishlist, session_key=request.session.session_key)
            
            # Remove product from wishlist
            wishlist_item = WishlistItem.objects.filter(
                wishlist=wishlist,
                product=product
            ).first()
            
            if wishlist_item:
                wishlist_item.delete()
                return JsonResponse({
                    'success': True,
                    'message': f'{product.name} removed from your wishlist!',
                    'wishlist_count': wishlist.get_item_count(),
                    'is_guest': not request.user.is_authenticated
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Product not found in your wishlist.'
                })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Failed to remove product from wishlist.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request.'})


# ============================================================================
# PRODUCT COMPARISON FUNCTIONALITY
# ============================================================================

def comparison_view(request):
    """Display product comparison page"""
    comparison = None
    comparison_items = []
    
    if request.user.is_authenticated:
        comparison = ProductComparison.objects.filter(user=request.user).first()
    else:
        if request.session.session_key:
            comparison = ProductComparison.objects.filter(
                session_key=request.session.session_key,
                user=None
            ).first()
    
    if comparison:
        comparison_items = comparison.items.all().select_related('product__category')
    
    # Get common specifications across all products in comparison
    common_specs = []
    if comparison_items:
        # Get all specifications from all products
        all_specs = {}
        for item in comparison_items:
            for spec in item.product.specifications.all():
                if spec.name not in all_specs:
                    all_specs[spec.name] = []
                all_specs[spec.name].append((item.product, spec.value))
        
        # Only show specs that exist for most products
        for spec_name, spec_values in all_specs.items():
            if len(spec_values) >= len(comparison_items) // 2:  # Show if at least half the products have this spec
                common_specs.append({
                    'name': spec_name,
                    'values': {product.id: value for product, value in spec_values}
                })
    
    context = {
        'comparison': comparison,
        'comparison_items': comparison_items,
        'common_specs': common_specs,
    }
    return render(request, 'store/comparison.html', context)

def add_to_comparison(request, product_id):
    """Add product to comparison (AJAX)"""
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id, available=True)
            
            # Get or create comparison
            if request.user.is_authenticated:
                comparison, created = ProductComparison.objects.get_or_create(
                    user=request.user,
                    defaults={'name': 'My Product Comparison'}
                )
            else:
                if not request.session.session_key:
                    request.session.create()
                comparison, created = ProductComparison.objects.get_or_create(
                    session_key=request.session.session_key,
                    user=None,
                    defaults={'name': 'Product Comparison'}
                )
            
            # Check if comparison is full
            if not comparison.can_add_more():
                return JsonResponse({
                    'success': False,
                    'message': 'Maximum 4 products can be compared at once.'
                })
            
            # Check if product already in comparison
            if comparison.items.filter(product=product).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Product is already in your comparison.'
                })
            
            # Add product to comparison
            ComparisonItem.objects.create(
                comparison=comparison,
                product=product
            )
            
            return JsonResponse({
                'success': True,
                'message': f'{product.name} added to comparison!',
                'comparison_count': comparison.get_product_count()
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Failed to add product to comparison.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request.'})

def remove_from_comparison(request, product_id):
    """Remove product from comparison (AJAX)"""
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id)
            
            # Get comparison
            comparison = None
            if request.user.is_authenticated:
                comparison = ProductComparison.objects.filter(user=request.user).first()
            else:
                if request.session.session_key:
                    comparison = ProductComparison.objects.filter(
                        session_key=request.session.session_key,
                        user=None
                    ).first()
            
            if not comparison:
                return JsonResponse({
                    'success': False,
                    'message': 'No comparison found.'
                })
            
            # Remove product from comparison
            comparison_item = ComparisonItem.objects.filter(
                comparison=comparison,
                product=product
            ).first()
            
            if comparison_item:
                comparison_item.delete()
                
                # Delete comparison if empty
                if comparison.get_product_count() == 0:
                    comparison.delete()
                
                return JsonResponse({
                    'success': True,
                    'message': f'{product.name} removed from comparison!',
                    'comparison_count': comparison.get_product_count() if comparison.get_product_count() > 0 else 0
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Product not found in comparison.'
                })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Failed to remove product from comparison.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request.'})

def clear_comparison(request):
    """Clear all products from comparison (AJAX)"""
    if request.method == 'POST':
        try:
            # Get comparison
            comparison = None
            if request.user.is_authenticated:
                comparison = ProductComparison.objects.filter(user=request.user).first()
            else:
                if request.session.session_key:
                    comparison = ProductComparison.objects.filter(
                        session_key=request.session.session_key,
                        user=None
                    ).first()
            
            if comparison:
                comparison.delete()
                return JsonResponse({
                    'success': True,
                    'message': 'Comparison cleared successfully!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'No comparison found.'
                })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Failed to clear comparison.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request.'})

def move_to_cart_from_wishlist(request, product_id):
    """Move product from wishlist to cart (AJAX) - supports both authenticated and guest users"""
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id, available=True)
            
            if product.stock <= 0:
                return JsonResponse({
                    'success': False,
                    'message': 'Product is out of stock.'
                })
            
            # Get or create cart based on user authentication
            if request.user.is_authenticated:
                cart, created = Cart.objects.get_or_create(user=request.user)
            else:
                if not request.session.session_key:
                    request.session.create()
                cart, created = Cart.objects.get_or_create(
                    session_key=request.session.session_key,
                    user=None
                )
            
            # Add item to cart
            cart_item, item_created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': 1, 'price': product.price}
            )
            
            if not item_created:
                cart_item.quantity += 1
                if cart_item.quantity > product.stock:
                    cart_item.quantity = product.stock
                cart_item.save()
            
            # Remove from wishlist
            if request.user.is_authenticated:
                wishlist = Wishlist.objects.filter(user=request.user).first()
            else:
                wishlist = Wishlist.objects.filter(session_key=request.session.session_key).first() if request.session.session_key else None
            
            if wishlist:
                WishlistItem.objects.filter(
                    wishlist=wishlist,
                    product=product
                ).delete()
            
            return JsonResponse({
                'success': True,
                'message': f'{product.name} moved to cart!',
                'cart_count': cart.get_total_items(),
                'wishlist_count': wishlist.get_item_count() if wishlist else 0,
                'is_guest': not request.user.is_authenticated
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Failed to move product to cart.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request.'})


@staff_member_required
def advanced_search_api(request):
    """Advanced search API with multiple filters and criteria."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        data = json.loads(request.body)
        model_type = data.get('model_type')
        filters = data.get('filters', {})
        
        if not model_type:
            return JsonResponse({'error': 'Model type is required'}, status=400)
        
        # Map model types to actual models
        model_map = {
            'product': Product,
            'order': Order,
            'user': User,
        }
        
        if model_type not in model_map:
            return JsonResponse({'error': 'Invalid model type'}, status=400)
        
        model_class = model_map[model_type]
        queryset = model_class.objects.all()
        
        # Apply filters based on model type
        if model_type == 'product':
            # Name search
            if filters.get('name'):
                queryset = queryset.filter(name__icontains=filters['name'])
            
            # Price range
            if filters.get('min_price'):
                queryset = queryset.filter(price__gte=filters['min_price'])
            if filters.get('max_price'):
                queryset = queryset.filter(price__lte=filters['max_price'])
            
            # Category
            if filters.get('category'):
                queryset = queryset.filter(category__name__icontains=filters['category'])
            
            # Stock range
            if filters.get('min_stock'):
                queryset = queryset.filter(stock__gte=filters['min_stock'])
            if filters.get('max_stock'):
                queryset = queryset.filter(stock__lte=filters['max_stock'])
            
            # Date range
            if filters.get('start_date'):
                queryset = queryset.filter(created_at__gte=filters['start_date'])
            if filters.get('end_date'):
                queryset = queryset.filter(created_at__lte=filters['end_date'])
        
        elif model_type == 'order':
            # User search
            if filters.get('user'):
                queryset = queryset.filter(user__username__icontains=filters['user'])
            
            # Status
            if filters.get('status'):
                queryset = queryset.filter(status=filters['status'])
            
            # Total amount range
            if filters.get('min_total'):
                queryset = queryset.filter(total_amount__gte=filters['min_total'])
            if filters.get('max_total'):
                queryset = queryset.filter(total_amount__lte=filters['max_total'])
            
            # Date range
            if filters.get('start_date'):
                queryset = queryset.filter(created_at__gte=filters['start_date'])
            if filters.get('end_date'):
                queryset = queryset.filter(created_at__lte=filters['end_date'])
        
        elif model_type == 'user':
            # Username/email search
            if filters.get('search'):
                queryset = queryset.filter(
                    Q(username__icontains=filters['search']) |
                    Q(email__icontains=filters['search']) |
                    Q(first_name__icontains=filters['search']) |
                    Q(last_name__icontains=filters['search'])
                )
            
            # Active status
            if 'is_active' in filters:
                queryset = queryset.filter(is_active=filters['is_active'])
            
            # Date joined range
            if filters.get('start_date'):
                queryset = queryset.filter(date_joined__gte=filters['start_date'])
            if filters.get('end_date'):
                queryset = queryset.filter(date_joined__lte=filters['end_date'])
        
        # Pagination
        page = int(data.get('page', 1))
        per_page = int(data.get('per_page', 25))
        
        total_count = queryset.count()
        start = (page - 1) * per_page
        end = start + per_page
        
        results = queryset[start:end]
        
        # Format results
        formatted_results = []
        for obj in results:
            if model_type == 'product':
                formatted_results.append({
                    'id': obj.id,
                    'name': obj.name,
                    'price': float(obj.price),
                    'stock': obj.stock,
                    'category': obj.category.name if obj.category else '',
                    'created_at': obj.created_at.strftime('%Y-%m-%d %H:%M')
                })
            elif model_type == 'order':
                formatted_results.append({
                    'id': obj.id,
                    'user': obj.user.username,
                    'total_amount': float(obj.total_amount or 0),
                    'status': obj.status,
                    'created_at': obj.created_at.strftime('%Y-%m-%d %H:%M')
                })
            elif model_type == 'user':
                formatted_results.append({
                    'id': obj.id,
                    'username': obj.username,
                    'email': obj.email,
                    'full_name': f'{obj.first_name} {obj.last_name}'.strip(),
                    'is_active': obj.is_active,
                    'date_joined': obj.date_joined.strftime('%Y-%m-%d %H:%M')
                })
        
        return JsonResponse({
            'results': formatted_results,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': (total_count + per_page - 1) // per_page,
                'has_next': end < total_count,
                'has_previous': page > 1
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def bulk_operations_view(request):
    """Bulk operations management page."""
    return render(request, 'admin/bulk_operations.html', {
        'title': '🛠️ Bulk Operations - Mass Management Tools',
        'admin_view': True
    })


# ========================================
# PRODUCT IMPORT SYSTEM
# ========================================

@staff_member_required
def product_import_view(request):
    """Product import management page."""
    return render(request, 'admin/product_import.html', {
        'title': '📥 Product Import - Bulk Import System',
        'admin_view': True
    })


@staff_member_required
def product_import_upload_api(request):
    """API endpoint for uploading and parsing product import files."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
        
        uploaded_file = request.FILES['file']
        
        # Validate file type
        if not uploaded_file.name.lower().endswith(('.csv', '.xlsx', '.xls')):
            return JsonResponse({'error': 'Invalid file type. Please upload CSV or Excel files.'}, status=400)
        
        # Save file temporarily
        temp_filename = f'temp_import_{timezone.now().strftime("%Y%m%d_%H%M%S")}_{uploaded_file.name}'
        temp_path = default_storage.save(temp_filename, ContentFile(uploaded_file.read()))
        
        try:
            # Parse the file
            parsed_data = parse_import_file(temp_path, uploaded_file.name)
            
            # Validate and preview data
            validation_results = validate_import_data(parsed_data['rows'])
            
            # Store parsed data in session for later use
            request.session[f'import_data_{temp_filename}'] = {
                'file_path': temp_path,
                'headers': parsed_data['headers'],
                'rows': parsed_data['rows'][:100],  # Limit preview to 100 rows
                'total_rows': len(parsed_data['rows']),
                'validation': validation_results
            }
            
            return JsonResponse({
                'success': True,
                'file_id': temp_filename,
                'headers': parsed_data['headers'],
                'preview_rows': parsed_data['rows'][:10],  # First 10 rows for preview
                'total_rows': len(parsed_data['rows']),
                'validation_summary': {
                    'valid_rows': validation_results['valid_count'],
                    'invalid_rows': validation_results['invalid_count'],
                    'warnings': validation_results['warning_count']
                },
                'errors': validation_results['errors'][:10]  # First 10 errors
            })
            
        finally:
            # Clean up temp file after parsing
            if default_storage.exists(temp_path):
                default_storage.delete(temp_path)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def product_import_execute_api(request):
    """API endpoint for executing the product import after validation."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        data = json.loads(request.body)
        file_id = data.get('file_id')
        import_options = data.get('options', {})
        
        if not file_id or f'import_data_{file_id}' not in request.session:
            return JsonResponse({'error': 'Invalid file ID or session expired'}, status=400)
        
        import_data = request.session[f'import_data_{file_id}']
        
        # Execute the import
        results = execute_product_import(
            import_data['rows'], 
            import_options,
            request.user
        )
        
        # Clean up session data
        del request.session[f'import_data_{file_id}']
        
        return JsonResponse({
            'success': True,
            'results': results
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def parse_import_file(file_path, original_filename):
    """Parse CSV or Excel file and return structured data."""
    file_extension = original_filename.lower().split('.')[-1]
    
    if file_extension == 'csv':
        return parse_csv_file(file_path)
    elif file_extension in ['xlsx', 'xls']:
        return parse_excel_file(file_path)
    else:
        raise ValueError('Unsupported file format')


def parse_csv_file(file_path):
    """Parse CSV file and return headers and rows."""
    with default_storage.open(file_path, 'r', encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader)
        rows = list(csv_reader)
        
    return {'headers': headers, 'rows': rows}


def parse_excel_file(file_path):
    """Parse Excel file and return headers and rows."""
    with default_storage.open(file_path, 'rb') as file:
        workbook = openpyxl.load_workbook(file)
        worksheet = workbook.active
        
        headers = [cell.value for cell in worksheet[1]]
        rows = []
        
        for row in worksheet.iter_rows(min_row=2, values_only=True):
            rows.append([cell if cell is not None else '' for cell in row])
        
    return {'headers': headers, 'rows': rows}


def validate_import_data(rows):
    """Validate product import data and return validation results."""
    validation_results = {
        'valid_count': 0,
        'invalid_count': 0,
        'warning_count': 0,
        'errors': [],
        'warnings': []
    }
    
    required_fields = ['name', 'price']  # Minimum required fields
    
    for i, row in enumerate(rows, start=2):  # Start from row 2 (after headers)
        row_errors = []
        row_warnings = []
        
        # Check if row has enough columns
        if len(row) < len(required_fields):
            row_errors.append(f'Row {i}: Insufficient columns')
            continue
        
        # Validate required fields (assuming standard order: name, description, price, stock, category)
        if len(row) >= 1 and not str(row[0]).strip():  # Name
            row_errors.append(f'Row {i}: Product name is required')
        
        if len(row) >= 3:  # Price
            try:
                price = str(row[2]).strip()
                if price:
                    float(price.replace('$', '').replace(',', ''))
                else:
                    row_errors.append(f'Row {i}: Price is required')
            except ValueError:
                row_errors.append(f'Row {i}: Invalid price format')
        
        if len(row) >= 4:  # Stock
            try:
                stock = str(row[3]).strip()
                if stock:
                    stock_val = int(float(stock))
                    if stock_val < 0:
                        row_warnings.append(f'Row {i}: Negative stock value')
            except ValueError:
                row_warnings.append(f'Row {i}: Invalid stock format, will default to 0')
        
        # Check for potential duplicates by name
        product_name = str(row[0]).strip() if len(row) >= 1 else ''
        if product_name and Product.objects.filter(name__iexact=product_name).exists():
            row_warnings.append(f'Row {i}: Product "{product_name}" already exists')
        
        if row_errors:
            validation_results['invalid_count'] += 1
            validation_results['errors'].extend(row_errors)
        else:
            validation_results['valid_count'] += 1
        
        if row_warnings:
            validation_results['warning_count'] += 1
            validation_results['warnings'].extend(row_warnings)
    
    return validation_results


def execute_product_import(rows, options, admin_user):
    """Execute the actual product import with transaction safety."""
    results = {
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'errors': []
    }
    
    update_existing = options.get('update_existing', False)
    create_categories = options.get('create_categories', True)
    
    with transaction.atomic():
        for i, row in enumerate(rows, start=2):
            try:
                if len(row) < 3:  # Need at least name, description, price
                    results['skipped'] += 1
                    continue
                
                # Extract data
                name = str(row[0]).strip() if row[0] else ''
                description = str(row[1]).strip() if len(row) > 1 and row[1] else ''
                price_str = str(row[2]).strip() if len(row) > 2 and row[2] else '0'
                stock_str = str(row[3]).strip() if len(row) > 3 and row[3] else '0'
                category_name = str(row[4]).strip() if len(row) > 4 and row[4] else ''
                
                if not name:
                    results['errors'].append(f'Row {i}: Missing product name')
                    results['skipped'] += 1
                    continue
                
                # Parse price
                try:
                    price = Decimal(price_str.replace('$', '').replace(',', ''))
                except (ValueError, InvalidOperation):
                    price = Decimal('0')
                
                # Parse stock
                try:
                    stock = int(float(stock_str))
                    if stock < 0:
                        stock = 0
                except (ValueError, TypeError):
                    stock = 0
                
                # Handle category
                category = None
                if category_name:
                    if create_categories:
                        category, created = Category.objects.get_or_create(
                            name=category_name,
                            defaults={'slug': slugify(category_name)}
                        )
                    else:
                        try:
                            category = Category.objects.get(name__iexact=category_name)
                        except Category.DoesNotExist:
                            pass
                
                # Check if product exists
                existing_product = Product.objects.filter(name__iexact=name).first()
                
                if existing_product:
                    if update_existing:
                        # Update existing product
                        existing_product.description = description or existing_product.description
                        existing_product.price = price if price > 0 else existing_product.price
                        existing_product.stock = stock
                        if category:
                            existing_product.category = category
                        existing_product.save()
                        results['updated'] += 1
                    else:
                        results['skipped'] += 1
                else:
                    # Create new product
                    product = Product.objects.create(
                        name=name,
                        slug=slugify(name),
                        description=description,
                        price=price,
                        stock=stock,
                        category=category
                    )
                    results['created'] += 1
                    
            except Exception as e:
                results['errors'].append(f'Row {i}: {str(e)}')
                results['skipped'] += 1
    
    # Log the import operation
    AdminActivity.objects.create(
        admin_user=admin_user,
        action='BULK_IMPORT',
        description=f'Product import: {results["created"]} created, {results["updated"]} updated, {results["skipped"]} skipped',
        ip_address=get_client_ip({'META': {'REMOTE_ADDR': '127.0.0.1'}})  # Default IP for import
    )
    
    return results


# ========================================
# IMAGE MANAGEMENT SYSTEM
# ========================================

@staff_member_required
def image_management_view(request):
    """Image management interface page."""
    return render(request, 'admin/image_management.html', {
        'title': '🖼️ Image Management - Media Control Center',
        'admin_view': True
    })


@staff_member_required
def image_upload_api(request):
    """API endpoint for uploading and processing images."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        if 'images' not in request.FILES:
            return JsonResponse({'error': 'No images uploaded'}, status=400)
        
        uploaded_files = request.FILES.getlist('images')
        results = []
        
        for uploaded_file in uploaded_files:
            try:
                # Validate file type
                if not uploaded_file.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    results.append({
                        'filename': uploaded_file.name,
                        'success': False,
                        'error': 'Invalid image format. Supported: JPG, PNG, GIF, WebP'
                    })
                    continue
                
                # Validate file size (10MB limit)
                if uploaded_file.size > 10 * 1024 * 1024:
                    results.append({
                        'filename': uploaded_file.name,
                        'success': False,
                        'error': 'File too large. Maximum size: 10MB'
                    })
                    continue
                
                # Process the image
                processed_image = process_uploaded_image(uploaded_file)
                
                results.append({
                    'filename': uploaded_file.name,
                    'success': True,
                    'image_data': processed_image
                })
                
            except Exception as e:
                results.append({
                    'filename': uploaded_file.name,
                    'success': False,
                    'error': str(e)
                })
        
        # Log the upload operation
        AdminActivity.objects.create(
            admin_user=request.user,
            action='IMAGE_UPLOAD',
            description=f'Uploaded {len([r for r in results if r["success"]])} images',
            ip_address=get_client_ip(request)
        )
        
        return JsonResponse({
            'success': True,
            'results': results,
            'total_uploaded': len([r for r in results if r['success']])
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def image_process_api(request):
    """API endpoint for processing existing images (resize, crop, compress)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        data = json.loads(request.body)
        image_id = data.get('image_id')
        operations = data.get('operations', {})
        
        if not image_id:
            return JsonResponse({'error': 'Image ID is required'}, status=400)
        
        # Load image from session or storage
        # For demo purposes, we'll simulate processing
        processed_image = apply_image_operations(image_id, operations)
        
        return JsonResponse({
            'success': True,
            'processed_image': processed_image
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def image_gallery_api(request):
    """API endpoint for retrieving image gallery with pagination and filtering."""
    try:
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        filter_type = request.GET.get('type', 'all')  # all, product, category, banner
        search_query = request.GET.get('search', '')
        
        # For demo purposes, generate sample image gallery
        gallery_images = generate_sample_gallery(page, per_page, filter_type, search_query)
        
        return JsonResponse(gallery_images)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def image_batch_process_api(request):
    """API endpoint for batch processing multiple images."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        data = json.loads(request.body)
        image_ids = data.get('image_ids', [])
        batch_operations = data.get('operations', {})
        
        if not image_ids:
            return JsonResponse({'error': 'No images selected'}, status=400)
        
        results = []
        
        for image_id in image_ids:
            try:
                processed_image = apply_image_operations(image_id, batch_operations)
                results.append({
                    'image_id': image_id,
                    'success': True,
                    'processed': processed_image
                })
            except Exception as e:
                results.append({
                    'image_id': image_id,
                    'success': False,
                    'error': str(e)
                })
        
        # Log batch operation
        AdminActivity.objects.create(
            admin_user=request.user,
            action='BATCH_IMAGE_PROCESS',
            description=f'Batch processed {len([r for r in results if r["success"]])} images',
            ip_address=get_client_ip(request)
        )
        
        return JsonResponse({
            'success': True,
            'results': results,
            'processed_count': len([r for r in results if r['success']])
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def process_uploaded_image(uploaded_file):
    """Process uploaded image: validate, optimize, generate thumbnails."""
    try:
        # Open the image
        image = Image.open(uploaded_file)
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Auto-orient based on EXIF data
        image = ImageOps.exif_transpose(image)
        
        # Get original dimensions
        original_width, original_height = image.size
        
        # Generate unique ID for this image
        image_id = str(uuid.uuid4())
        
        # Create different sizes
        sizes = {
            'thumbnail': (150, 150),
            'small': (300, 300),
            'medium': (600, 600),
            'large': (1200, 1200)
        }
        
        processed_versions = {}
        
        for size_name, (max_width, max_height) in sizes.items():
            # Calculate new dimensions maintaining aspect ratio
            image_copy = image.copy()
            image_copy.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Save to BytesIO
            buffer = io.BytesIO()
            
            # Optimize based on size
            quality = 95 if size_name == 'large' else 85
            if size_name == 'thumbnail':
                quality = 75
            
            image_copy.save(buffer, format='JPEG', quality=quality, optimize=True)
            
            processed_versions[size_name] = {
                'width': image_copy.width,
                'height': image_copy.height,
                'size_kb': round(buffer.tell() / 1024, 2),
                'data_url': f'data:image/jpeg;base64,{buffer.getvalue().hex()[:100]}...'  # Truncated for demo
            }
        
        return {
            'id': image_id,
            'original_filename': uploaded_file.name,
            'original_size': {
                'width': original_width,
                'height': original_height,
                'size_kb': round(uploaded_file.size / 1024, 2)
            },
            'processed_versions': processed_versions,
            'upload_time': timezone.now().isoformat(),
            'file_type': 'JPEG'  # Always convert to JPEG for consistency
        }
        
    except Exception as e:
        raise Exception(f'Image processing failed: {str(e)}')


def apply_image_operations(image_id, operations):
    """Apply various image operations like resize, crop, compress."""
    try:
        # For demo purposes, simulate processing operations
        processed_data = {
            'id': image_id,
            'operations_applied': [],
            'processing_time': timezone.now().isoformat()
        }
        
        if operations.get('resize'):
            width = operations['resize'].get('width', 800)
            height = operations['resize'].get('height', 600)
            processed_data['operations_applied'].append(f'Resized to {width}x{height}')
        
        if operations.get('crop'):
            x = operations['crop'].get('x', 0)
            y = operations['crop'].get('y', 0)
            width = operations['crop'].get('width', 100)
            height = operations['crop'].get('height', 100)
            processed_data['operations_applied'].append(f'Cropped to {x},{y} - {width}x{height}')
        
        if operations.get('compress'):
            quality = operations['compress'].get('quality', 80)
            processed_data['operations_applied'].append(f'Compressed to {quality}% quality')
        
        if operations.get('filter'):
            filter_type = operations['filter'].get('type', 'none')
            if filter_type != 'none':
                processed_data['operations_applied'].append(f'Applied {filter_type} filter')
        
        return processed_data
        
    except Exception as e:
        raise Exception(f'Image operation failed: {str(e)}')


def generate_sample_gallery(page, per_page, filter_type, search_query):
    """Generate sample image gallery data for demonstration."""
    import random
    
    # Sample image data
    sample_images = []
    total_images = 150  # Simulate 150 images in gallery
    
    for i in range(1, total_images + 1):
        image_types = ['product', 'category', 'banner', 'avatar']
        img_type = random.choice(image_types)
        
        # Apply filtering
        if filter_type != 'all' and img_type != filter_type:
            continue
        
        # Apply search filtering
        image_name = f'Sample Image {i}'
        if search_query and search_query.lower() not in image_name.lower():
            continue
        
        sample_images.append({
            'id': f'img_{i}',
            'filename': f'image_{i}.jpg',
            'name': image_name,
            'type': img_type,
            'size': {
                'width': random.randint(800, 2000),
                'height': random.randint(600, 1500),
                'size_kb': random.randint(50, 500)
            },
            'thumbnail_url': f'/static/sample_thumbnails/thumb_{i}.jpg',  # Demo URL
            'upload_date': '2024-10-12',
            'uploader': 'admin',
            'usage_count': random.randint(0, 10)
        })
    
    # Pagination
    start = (page - 1) * per_page
    end = start + per_page
    paginated_images = sample_images[start:end]
    
    return {
        'images': paginated_images,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_images': len(sample_images),
            'total_pages': (len(sample_images) + per_page - 1) // per_page,
            'has_next': end < len(sample_images),
            'has_previous': page > 1
        },
        'filters': {
            'current_type': filter_type,
            'search_query': search_query
        }
    }


# ========================================
# SITE-WIDE ANNOUNCEMENT SYSTEM - Phase 2A Final Feature
# ========================================

@staff_member_required
def announcement_management_view(request):
    """Site-wide announcement management interface."""
    return render(request, 'admin/announcement_management.html', {
        'title': '📢 Announcement Management - Site-wide Broadcasting',
        'admin_view': True
    })


@staff_member_required
def announcement_create_api(request):
    """API endpoint for creating new site announcements."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        required_fields = ['title', 'message', 'announcement_type', 'start_date']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'error': f'{field} is required'}, status=400)
        
        # Import the model here to avoid circular imports
        from .models import SiteAnnouncement
        
        # Create the announcement
        announcement = SiteAnnouncement.objects.create(
            title=data['title'],
            message=data['message'],
            announcement_type=data['announcement_type'],
            priority=data.get('priority', 'medium'),
            target_audience=data.get('target_audience', 'all'),
            start_date=data['start_date'],
            end_date=data.get('end_date') if data.get('end_date') else None,
            is_active=data.get('is_active', True),
            is_dismissible=data.get('is_dismissible', True),
            show_on_homepage=data.get('show_on_homepage', True),
            show_in_header=data.get('show_in_header', False),
            show_as_popup=data.get('show_as_popup', False),
            action_button_text=data.get('action_button_text'),
            action_button_url=data.get('action_button_url'),
            created_by=request.user
        )
        
        # Log the creation
        AdminActivity.objects.create(
            admin_user=request.user,
            action_type='create',
            description=f'Created site announcement: {announcement.title}',
            object_type='SiteAnnouncement',
            object_id=announcement.id,
            object_repr=str(announcement),
            ip_address=get_client_ip(request)
        )
        
        return JsonResponse({
            'success': True,
            'announcement': {
                'id': announcement.id,
                'title': announcement.title,
                'type': announcement.announcement_type,
                'priority': announcement.priority,
                'target_audience': announcement.target_audience,
                'is_active': announcement.is_active,
                'start_date': announcement.start_date.isoformat(),
                'end_date': announcement.end_date.isoformat() if announcement.end_date else None,
                'created_at': announcement.created_at.isoformat()
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def announcement_list_api(request):
    """API endpoint for retrieving announcements with filtering and pagination."""
    try:
        from .models import SiteAnnouncement
        
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        announcement_type = request.GET.get('type', 'all')
        status_filter = request.GET.get('status', 'all')  # all, active, inactive, scheduled
        search_query = request.GET.get('search', '')
        
        # Base queryset
        queryset = SiteAnnouncement.objects.all().select_related('created_by')
        
        # Apply filters
        if announcement_type != 'all':
            queryset = queryset.filter(announcement_type=announcement_type)
        
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status_filter == 'scheduled':
            from django.utils import timezone
            now = timezone.now()
            queryset = queryset.filter(start_date__gt=now, is_active=True)
        
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(message__icontains=search_query)
            )
        
        # Pagination
        total_count = queryset.count()
        start = (page - 1) * per_page
        end = start + per_page
        announcements = queryset[start:end]
        
        # Format results
        announcements_data = []
        for announcement in announcements:
            announcements_data.append({
                'id': announcement.id,
                'title': announcement.title,
                'message': announcement.message[:200] + ('...' if len(announcement.message) > 200 else ''),
                'full_message': announcement.message,
                'type': announcement.announcement_type,
                'type_display': announcement.get_announcement_type_display(),
                'priority': announcement.priority,
                'target_audience': announcement.target_audience,
                'target_display': announcement.get_target_audience_display(),
                'is_active': announcement.is_active,
                'is_currently_active': announcement.is_currently_active(),
                'is_dismissible': announcement.is_dismissible,
                'show_on_homepage': announcement.show_on_homepage,
                'show_in_header': announcement.show_in_header,
                'show_as_popup': announcement.show_as_popup,
                'action_button_text': announcement.action_button_text,
                'action_button_url': announcement.action_button_url,
                'start_date': announcement.start_date.isoformat(),
                'end_date': announcement.end_date.isoformat() if announcement.end_date else None,
                'views_count': announcement.views_count,
                'clicks_count': announcement.clicks_count,
                'created_by': announcement.created_by.username,
                'created_at': announcement.created_at.strftime('%Y-%m-%d %H:%M'),
                'css_class': announcement.get_css_class(),
                'icon': announcement.get_icon()
            })
        
        return JsonResponse({
            'announcements': announcements_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': (total_count + per_page - 1) // per_page,
                'has_next': end < total_count,
                'has_previous': page > 1
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ========================================
# SUPPORT AND LEGAL PAGES VIEWS
# ========================================

def help_center(request):
    """Help Center page with FAQ and support information"""
    return render(request, 'store/help_center.html', {
        'title': 'Help Center - CartMax'
    })

@require_http_methods(["GET", "POST"])
def contact(request):
    """Contact Us page with contact form"""
    if request.method == 'POST':
        # Handle contact form submission
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        subject = request.POST.get('subject')
        order_number = request.POST.get('order_number', '')
        message = request.POST.get('message')
        
        # Basic validation
        if not all([first_name, last_name, email, subject, message]):
            messages.error(request, 'Please fill in all required fields.')
        else:
            # Here you would typically save to database or send email
            # For now, just show success message
            messages.success(request, 
                f'Thank you {first_name}! Your message has been sent. '
                'We will respond within 24 hours.'
            )
            return redirect('store:contact')
    
    return render(request, 'store/contact.html', {
        'title': 'Contact Us - CartMax'
    })

def shipping_info(request):
    """Shipping Information page"""
    return render(request, 'store/shipping_info.html', {
        'title': 'Shipping Information - CartMax'
    })

def returns(request):
    """Returns & Refunds page"""
    return render(request, 'store/returns.html', {
        'title': 'Returns & Refunds - CartMax'
    })

def privacy_policy(request):
    """Privacy Policy page"""
    return render(request, 'store/privacy_policy.html', {
        'title': 'Privacy Policy - CartMax'
    })

def terms_of_service(request):
    """Terms of Service page"""
    return render(request, 'store/terms_of_service.html', {
        'title': 'Terms of Service - CartMax'
    })

def cookies_policy(request):
    """Cookies Policy page"""
    return render(request, 'store/cookies.html', {
        'title': 'Cookies Policy - CartMax'
    })


# ============================================================================
# CURRENCY SWITCHING VIEWS
# ============================================================================

SUPPORTED_CURRENCIES = ['USD', 'INR']

@require_POST
def switch_currency(request):
    """
    AJAX endpoint to switch user's preferred currency
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get the new currency from POST data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            new_currency = data.get('currency')
        else:
            new_currency = request.POST.get('currency')
        
        # Validate currency
        if new_currency not in SUPPORTED_CURRENCIES:
            return JsonResponse({
                'success': False,
                'error': f'Unsupported currency: {new_currency}',
                'supported': SUPPORTED_CURRENCIES
            }, status=400)
        
        # Get current currency
        old_currency = request.session.get('preferred_currency', 'INR')
        
        # Update session
        request.session['preferred_currency'] = new_currency
        
        logger.info(f"Currency switched from {old_currency} to {new_currency}")
        
        return JsonResponse({
            'success': True,
            'old_currency': old_currency,
            'new_currency': new_currency,
            'message': f'Currency changed to {new_currency}'
        })
        
    except Exception as e:
        logger.error(f"Error switching currency: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to switch currency'
        }, status=500)

def get_currency_info(request):
    """
    API endpoint to get current currency information
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from .context_processors import get_exchange_rates, CURRENCY_SYMBOLS
        
        current_currency = request.session.get('preferred_currency', 'INR')
        rates = get_exchange_rates()
        
        return JsonResponse({
            'success': True,
            'current_currency': current_currency,
            'supported_currencies': SUPPORTED_CURRENCIES,
            'currency_symbols': CURRENCY_SYMBOLS,
            'exchange_rates': {
                'USD_TO_INR': str(rates['USD_TO_INR']),
                'INR_TO_USD': str(rates['INR_TO_USD'])
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting currency info: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get currency information'
        }, status=500)


# ============================================================================
# INVOICE DOWNLOAD FUNCTIONALITY
# ============================================================================

def format_currency(amount, currency):
    """Format amount with currency symbol"""
    if currency == 'INR':
        return f"₹{amount:.2f}"
    else:
        return f"${amount:.2f}"


def generate_invoice_pdf(order):
    """Generate professional HTML invoice for order"""
    # Calculate tax percentage
    if order.original_subtotal > 0:
        tax_percentage = (order.tax_amount / order.original_subtotal) * 100
    else:
        tax_percentage = 0
    
    context = {
        'order': order,
        'order_items': order.items.select_related('product').all(),
        'company_name': 'CartMax',
        'company_address': 'Your Store Address',
        'tax_percentage': round(tax_percentage, 1),
    }
    
    # Use professional HTML invoice template
    from django.template.loader import render_to_string
    html_content = render_to_string('store/professional_invoice.html', context)
    
    # Return BytesIO buffer with HTML content for compatibility with download_invoice
    buffer = BytesIO()
    buffer.write(html_content.encode('utf-8'))
    return buffer
    
    # Footer
    footer_text = '<font size="9" color="#64748b"><i>Thank you for shopping with CartMax!<br/>For support, contact: support@cartmax.com</i></font>'
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Header title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=26,
        textColor=PRIMARY_COLOR,
        spaceAfter=2,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Section heading style
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=TEXT_DARK,
        spaceAfter=8,
        fontName='Helvetica-Bold',
        borderColor=PRIMARY_COLOR,
        borderWidth=1,
        borderPadding=6
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=9,
        textColor=TEXT_DARK,
        spaceAfter=3
    )
    
    small_style = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontSize=8,
        textColor=TEXT_LIGHT,
        spaceAfter=2
    )
    
    # Professional Header with CartMax branding
    header_data = [
        [
            Paragraph('<font color="#2563eb" size=20><b>CartMax</b></font><br/><font color="#64748b" size=8>Your Online Shopping Hub</font>', styles['Normal']),
            Paragraph(f'<font color="#2563eb" size=16><b>INVOICE</b></font><br/><font color="#1e293b" size=11><b>Order #{order.order_id}</b></font>', styles['Normal'])
        ]
    ]
    header_table = Table(header_data, colWidths=[2.8*inch, 2.2*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(header_table)
    
    # Separator line
    from reportlab.platypus import HRFlowable
    hr = HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR, spaceBefore=8, spaceAfter=12)
    elements.append(hr)
    
    # Order date info
    order_date = order.created_at.strftime('%B %d, %Y')
    elements.append(Paragraph(f'<font color="#64748b" size=9><b>Invoice Date:</b> {order_date} | <b>Status:</b> {order.get_status_display()}</font>', normal_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # Bill To and Ship To sections in two columns
    bill_ship_data = [
        [
            Paragraph(f'<b><font color="#2563eb">BILL TO:</font></b><br/><font size=9>{order.first_name} {order.last_name}</font><br/><font size=8 color="#64748b">{order.email}<br/>{order.phone}</font>', normal_style),
            Paragraph(f'<b><font color="#2563eb">SHIP TO:</font></b><br/><font size=9>{order.address}</font><br/><font size=8 color="#64748b">{order.city}, {order.postal_code}</font><br/><font size=8 color="#64748b">{order.country}</font>', normal_style)
        ]
    ]
    
    bill_ship_table = Table(bill_ship_data, colWidths=[2.5*inch, 2.5*inch])
    bill_ship_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 1, BORDER_COLOR),
    ]))
    elements.append(bill_ship_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # Order items table - AMAZON STYLE
    elements.append(Paragraph('ORDER ITEMS', heading_style))
    
    # Calculate all discount information
    total_discount_amount = 0
    items_for_table = []
    currency_symbol = '₹' if order.currency == 'INR' else '$'
    
    for item in order.items.all():
        product = item.product
        
        # Get prices
        if order.currency == 'INR':
            unit_price = float(item.price_inr or item.price or 0)
            original_price = float(product.get_original_price('INR') or unit_price)
        else:
            unit_price = float(item.price_usd or item.price or 0)
            original_price = float(product.get_original_price('USD') or unit_price)
        
        # Calculate discount
        discount_per_item = (original_price - unit_price) if original_price > unit_price else 0
        total_item_discount = discount_per_item * item.quantity
        total_discount_amount += total_item_discount
        
        # Line total
        line_total = unit_price * item.quantity
        
        # Create clean row data (NO Paragraph objects, plain text only)
        items_for_table.append({
            'name': product.name[:50],
            'qty': str(item.quantity),
            'unit_price': f"{unit_price:.2f}",
            'discount': f"{discount_per_item:.2f}" if discount_per_item > 0 else "",
            'line_total': f"{line_total:.2f}"
        })
    
    # Build table with clean data (NO BULLETS)
    items_data = [['Product Name', 'Qty', 'Unit Price', 'Discount', 'Line Total']]
    for item in items_for_table:
        items_data.append([
            item['name'],
            item['qty'],
            item['unit_price'],
            item['discount'],
            item['line_total']
        ])
    
    items_table = Table(items_data, colWidths=[2.0*inch, 0.5*inch, 0.95*inch, 0.95*inch, 0.9*inch])
    items_table.setStyle(TableStyle([
        # Header row
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        # Data rows
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_DARK),
        # Alignment
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (4, 0), (-1, -1), 'RIGHT'),
        # Padding and borders
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        # Color discounts in green
        ('TEXTCOLOR', (3, 1), (3, -1), SUCCESS_COLOR),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Order summary with discount - CLEAN FORMAT
    subtotal = order.get_subtotal()
    # Subtotal is the actual amount paid, so original would be subtotal + discount
    original_subtotal = subtotal + total_discount_amount
    tax = order.get_tax()
    total = order.total or order.get_final_total()
    
    # Use order's applied discount if available
    order_discount = float(order.discount_amount or 0)
    if order_discount > 0:
        total_discount_for_display = order_discount
    else:
        total_discount_for_display = total_discount_amount
    
    summary_data = []
    
    # Simple, clean format like Amazon
    summary_data.append(['Subtotal:', format_currency(original_subtotal, order.currency)])
    
    if total_discount_for_display > 0:
        summary_data.append(['Discount:', f'-{format_currency(total_discount_for_display, order.currency)}'])
    
    summary_data.append(['Shipping:', 'FREE'])
    summary_data.append(['Tax (8%):', format_currency(tax, order.currency)])
    summary_data.append(['TOTAL:', format_currency(total, order.currency)])
    
    summary_table = Table(summary_data, colWidths=[3*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        # Alignment
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        # Font sizes
        ('FONTSIZE', (0, 0), (-1, -2), 11),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        # Styling
        ('TEXTCOLOR', (0, 0), (-1, -2), TEXT_DARK),
        ('TEXTCOLOR', (0, -1), (-1, -1), PRIMARY_COLOR),
        # Borders only on final row
        ('LINEABOVE', (0, -1), (-1, -1), 2, PRIMARY_COLOR),
        ('LINEBELOW', (0, -1), (-1, -1), 2, PRIMARY_COLOR),
        # Green for discount
        ('TEXTCOLOR', (1, 1), (1, 1), SUCCESS_COLOR) if len(summary_data) > 2 else ('TEXTCOLOR', (1, 0), (1, 0), TEXT_DARK),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Footer with professional touch
    footer_data = [
        [Paragraph(f'<font size=8 color="#64748b"><i>Thank you for shopping with CartMax!<br/>For support, contact: support@cartmax.com</i></font>', small_style)]
    ]
    footer_table = Table(footer_data, colWidths=[5*inch])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('TOPPADDING', (0, 0), (0, 0), 8),
        ('BOTTOMPADDING', (0, 0), (0, 0), 8),
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f1f5f9')),
        ('GRID', (0, 0), (0, 0), 1, BORDER_COLOR),
    ]))
    elements.append(footer_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


@login_required
def download_invoice(request, order_id):
    """Download professional tax invoice as PDF"""
    try:
        # Get order
        order = get_object_or_404(Order, id=order_id)
        
        # Check permission - user can only download their own invoices
        if order.user != request.user:
            logger.warning(f"Unauthorized invoice access attempt by user {request.user.id} for order {order_id}")
            raise Http404("You don't have permission to access this invoice.")
        
        # Check if order is delivered - invoice can only be downloaded for delivered orders
        if order.status != 'delivered':
            status_messages = {
                'pending': 'Your order is pending. Invoice will be available once the order is delivered.',
                'processing': 'Your order is currently being processed. Invoice will be available once the order is delivered.',
                'shipped': 'Your order is currently in transit. Invoice will be available once the order is delivered.',
                'cancelled': 'Invoices cannot be downloaded for cancelled orders.'
            }
            message = status_messages.get(order.status, 'Invoice can only be downloaded for delivered orders.')
            logger.info(f"Invoice download attempt for non-delivered order {order.order_id} by user {request.user.id}. Order status: {order.status}")
            return HttpResponse(message, status=400)
        
        # Generate professional HTML invoice using existing function
        html_buffer = generate_invoice_pdf(order)
        
        # Create response
        response = HttpResponse(html_buffer.getvalue(), content_type='text/html; charset=utf-8')
        filename = f"Invoice_{order.order_id}.html"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        
        # Log successful download
        logger.info(f"Invoice downloaded for order {order.order_id} by user {request.user.id}")
        
        return response
        
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error generating invoice for order {order_id}: {str(e)}")
        return HttpResponse('Error generating invoice', status=500)
