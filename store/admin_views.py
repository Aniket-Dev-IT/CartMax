from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Avg, Sum, Q, F, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.paginator import Paginator
from django.forms import modelform_factory
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import json
import logging

from .models import Product, Category, Order, OrderItem, Review, SearchQuery, DiscountCoupon, CouponUsage
from django.contrib.auth.models import User
from .admin_forms import EnhancedProductAdminForm, OrderManagementForm, ReviewModerationForm, CurrencyConversionForm
from .context_processors import convert_price, get_exchange_rates

# Setup logger
logger = logging.getLogger(__name__)

# =============================================================================
# ORDER PROCESSING HELPER FUNCTIONS
# =============================================================================

def send_order_notification(order, status):
    """Send email notification to customer about order status change"""
    try:
        subject_map = {
            'confirmed': f'Order {order.order_id} Confirmed',
            'shipped': f'Order {order.order_id} Shipped',
            'delivered': f'Order {order.order_id} Delivered',
            'cancelled': f'Order {order.order_id} Cancelled'
        }
        
        template_map = {
            'confirmed': 'emails/order_confirmed.html',
            'shipped': 'emails/order_shipped.html', 
            'delivered': 'emails/order_delivered.html',
            'cancelled': 'emails/order_cancelled.html'
        }
        
        subject = subject_map.get(status, f'Order {order.order_id} Update')
        template = template_map.get(status, 'emails/order_update.html')
        
        # Create email context
        context = {
            'order': order,
            'customer_name': order.user.get_full_name() or order.user.username,
            'order_items': order.items.select_related('product').all(),
            'site_name': 'CartMax',
        }
        
        # Render email content
        html_content = render_to_string(template, context)
        
        # Send email
        send_mail(
            subject=subject,
            message=f'Your order {order.order_id} status has been updated to {status}.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.email or order.user.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        logger.info(f'Order notification sent: {order.order_id} -> {status}')
        return True
        
    except Exception as e:
        logger.error(f'Failed to send order notification: {e}')
        return False

def process_order_refund(order):
    """Process refund for cancelled order"""
    try:
        # In a real implementation, this would integrate with payment gateway
        # For now, we'll just log the refund and update order status
        refund_amount = order.total
        
        # Here you would integrate with payment processor:
        # - Stripe: stripe.Refund.create()
        # - PayPal: paypal.refund()
        # - Razorpay: razorpay.payment.refund()
        
        # For demo purposes, simulate successful refund
        order.refund_amount = refund_amount
        order.refund_status = 'processed'
        order.save()
        
        logger.info(f'Refund processed for order {order.order_id}: {refund_amount}')
        return True
        
    except Exception as e:
        logger.error(f'Failed to process refund for order {order.order_id}: {e}')
        return False

def generate_invoice_pdf(order):
    """Generate professional HTML invoice for order"""
    try:
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
        html_content = render_to_string('store/professional_invoice.html', context)
        
        # Return as clean HTML that can be printed or saved as PDF via browser
        response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
        response['Content-Disposition'] = f'inline; filename="invoice_{order.order_id}.html"'
        return response
        
    except Exception as e:
        logger.error(f'Failed to generate invoice for order {order.order_id}: {e}')
        return HttpResponse('Invoice generation failed', status=500)


# =============================================================================
# CUSTOMER MANAGEMENT HELPER FUNCTIONS
# =============================================================================

def get_customer_favorite_categories(user):
    """Get customer's favorite product categories based on order history"""
    try:
        # Get categories from user's orders
        favorite_categories = Category.objects.filter(
            products__orderitem__order__user=user,
            products__orderitem__order__status__in=['delivered', 'shipped']
        ).annotate(
            order_count=Count('products__orderitem')
        ).order_by('-order_count')[:3]
        
        return list(favorite_categories)
    except Exception as e:
        logger.error(f'Failed to get favorite categories for user {user.id}: {e}')
        return []

def get_customer_lifetime_value(user):
    """Calculate customer lifetime value and metrics"""
    try:
        orders = Order.objects.filter(user=user, status__in=['delivered', 'shipped'])
        
        if not orders.exists():
            return {
                'total_spent': 0,
                'avg_order_value': 0,
                'order_frequency': 0,
                'lifetime_value': 0,
                'customer_segment': 'New'
            }
        
        total_spent = orders.aggregate(Sum('total'))['total__sum'] or 0
        total_orders = orders.count()
        avg_order_value = total_spent / total_orders
        
        # Calculate order frequency (orders per month)
        first_order = orders.order_by('created_at').first().created_at
        months_active = max(1, (timezone.now() - first_order).days / 30)
        order_frequency = total_orders / months_active
        
        # Simple lifetime value calculation
        lifetime_value = avg_order_value * order_frequency * 12  # Projected annual value
        
        # Customer segmentation
        if total_spent >= 10000:  # ₹10,000+
            segment = 'VIP'
        elif total_spent >= 5000:  # ₹5,000+
            segment = 'Premium'
        elif total_spent >= 1000:  # ₹1,000+
            segment = 'Regular'
        else:
            segment = 'Basic'
        
        return {
            'total_spent': total_spent,
            'avg_order_value': avg_order_value,
            'order_frequency': order_frequency,
            'lifetime_value': lifetime_value,
            'customer_segment': segment,
            'months_active': months_active
        }
        
    except Exception as e:
        logger.error(f'Failed to calculate CLV for user {user.id}: {e}')
        return {'error': str(e)}

def send_customer_email(user, subject, message, template=None):
    """Send email to customer with professional template"""
    try:
        context = {
            'customer_name': user.get_full_name() or user.username,
            'message': message,
            'site_name': 'CartMax',
        }
        
        if template:
            html_content = render_to_string(template, context)
        else:
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #007bff;">Hello {context['customer_name']}!</h2>
                <div style="padding: 20px; background: #f8f9fa; border-radius: 5px;">
                    {message}
                </div>
                <div style="margin-top: 20px; text-align: center; color: #666; font-size: 12px;">
                    Best regards,<br>CartMax Team
                </div>
            </div>
            """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        logger.info(f'Email sent to customer {user.id}: {subject}')
        return True
        
    except Exception as e:
        logger.error(f'Failed to send email to customer {user.id}: {e}')
        return False


@staff_member_required
def admin_control_dashboard(request):
    """
    Main admin control dashboard - landing page for all admin features.
    """
    # Gather quick stats
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_categories = Category.objects.count()
    total_users = User.objects.count()
    total_coupons = DiscountCoupon.objects.count()
    
    # Calculate revenue (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_orders = Order.objects.filter(
        created_at__gte=thirty_days_ago,
        status__in=['completed', 'delivered', 'shipped']  # Only count successful orders
    )
    total_revenue = recent_orders.aggregate(Sum('total'))['total__sum'] or 0
    
    # Calculate average order value
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'total_categories': total_categories,
        'total_users': total_users,
        'total_coupons': total_coupons,
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
    }
    
    return render(request, 'admin/admin_control_dashboard.html', context)


@staff_member_required
def pricing_dashboard(request):
    """Enhanced pricing analytics dashboard with dual currency support"""
    
    # Get selected currency from request (default to INR)
    selected_currency = request.GET.get('currency', 'INR').upper()
    if selected_currency not in ['INR', 'USD']:
        selected_currency = 'INR'
    
    # Define currency fields based on selection
    if selected_currency == 'USD':
        price_field = 'price_usd'
        original_price_field = 'original_price_usd'
        currency_symbol = '$'
        currency_name = 'USD'
    else:
        price_field = 'price_inr'
        original_price_field = 'original_price_inr'
        currency_symbol = '₹'
        currency_name = 'INR'
    
    # Basic pricing statistics for selected currency
    available_products = Product.objects.filter(available=True, **{f'{price_field}__isnull': False})
    total_products = available_products.count()
    
    if total_products > 0:
        avg_price_data = available_products.aggregate(Avg(price_field))
        avg_price = avg_price_data[f'{price_field}__avg'] or 0
        
        price_range_data = available_products.aggregate(
            min_price=Min(price_field), 
            max_price=Max(price_field)
        )
        price_range = {
            'min_price': round(float(price_range_data['min_price'] or 0), 2),
            'max_price': round(float(price_range_data['max_price'] or 0), 2)
        }
        
        # Products with discounts in selected currency
        discounted_products = available_products.filter(
            **{f'{original_price_field}__gt': F(price_field)}
        ).count()
    else:
        avg_price = 0
        price_range = {'min_price': 0, 'max_price': 0}
        discounted_products = 0
    
    # Category-wise pricing analysis for selected currency
    category_analysis = Category.objects.filter(
        is_active=True, 
        products__available=True,
        **{f'products__{price_field}__isnull': False}
    ).annotate(
        product_count=Count('products'),
        avg_price=Avg(f'products__{price_field}'),
        min_price=Min(f'products__{price_field}'),
        max_price=Max(f'products__{price_field}')
    ).filter(product_count__gt=0).order_by('-avg_price')
    
    # Price distribution based on selected currency
    if selected_currency == 'USD':
        price_ranges = [
            {'range': 'Under $10', 'count': available_products.filter(**{f'{price_field}__lt': 10}).count()},
            {'range': '$10 - $25', 'count': available_products.filter(**{f'{price_field}__gte': 10, f'{price_field}__lt': 25}).count()},
            {'range': '$25 - $50', 'count': available_products.filter(**{f'{price_field}__gte': 25, f'{price_field}__lt': 50}).count()},
            {'range': '$50 - $100', 'count': available_products.filter(**{f'{price_field}__gte': 50, f'{price_field}__lt': 100}).count()},
            {'range': '$100+', 'count': available_products.filter(**{f'{price_field}__gte': 100}).count()}
        ]
    else:
        price_ranges = [
            {'range': 'Under ₹500', 'count': available_products.filter(**{f'{price_field}__lt': 500}).count()},
            {'range': '₹500 - ₹1,000', 'count': available_products.filter(**{f'{price_field}__gte': 500, f'{price_field}__lt': 1000}).count()},
            {'range': '₹1,000 - ₹2,500', 'count': available_products.filter(**{f'{price_field}__gte': 1000, f'{price_field}__lt': 2500}).count()},
            {'range': '₹2,500 - ₹5,000', 'count': available_products.filter(**{f'{price_field}__gte': 2500, f'{price_field}__lt': 5000}).count()},
            {'range': '₹5,000+', 'count': available_products.filter(**{f'{price_field}__gte': 5000}).count()}
        ]
    
    # Revenue performance (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_orders = Order.objects.filter(
        created_at__gte=thirty_days_ago,
        status__in=['completed', 'delivered', 'shipped'],
        currency=selected_currency
    )
    
    total_revenue = recent_orders.aggregate(Sum('total'))['total__sum'] or 0
    avg_order_value = recent_orders.aggregate(Avg('total'))['total__avg'] or 0
    
    # Ensure values are floats and rounded
    total_revenue = round(float(total_revenue), 2)
    avg_order_value = round(float(avg_order_value), 2)
    
    # Top performing products by revenue for selected currency
    if selected_currency == 'USD':
        price_for_revenue = 'orderitem__price_usd'
    else:
        price_for_revenue = 'orderitem__price_inr'
    
    top_revenue_products = available_products.filter(
        orderitem__order__created_at__gte=thirty_days_ago,
        orderitem__order__status__in=['completed', 'delivered'],
        orderitem__order__currency=selected_currency
    ).annotate(
        revenue=Sum(F('orderitem__quantity') * F(price_for_revenue)),
        current_price=F(price_field)
    ).order_by('-revenue')[:10]
    
    # Pricing recommendations for selected currency
    pricing_recommendations = generate_pricing_recommendations(selected_currency)
    
    # Additional dual currency statistics
    dual_currency_stats = {
        'inr_products': Product.objects.filter(available=True, price_inr__isnull=False).count(),
        'usd_products': Product.objects.filter(available=True, price_usd__isnull=False).count(),
        'both_currencies': Product.objects.filter(available=True, price_inr__isnull=False, price_usd__isnull=False).count(),
    }
    
    context = {
        'selected_currency': selected_currency,
        'currency_symbol': currency_symbol,
        'currency_name': currency_name,
        'total_products': total_products,
        'avg_price': round(avg_price, 2),
        'price_range': price_range,
        'discounted_products': discounted_products,
        'category_analysis': category_analysis,
        'price_ranges': price_ranges,
        'total_revenue': total_revenue,
        'avg_order_value': round(avg_order_value, 2),
        'top_revenue_products': top_revenue_products,
        'pricing_recommendations': pricing_recommendations,
        'dual_currency_stats': dual_currency_stats,
    }
    
    return render(request, 'admin/pricing_dashboard.html', context)


@staff_member_required
def product_performance_dashboard(request):
    """Product performance analytics dashboard"""
    
    # Sales performance metrics
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Best selling products
    best_sellers = Product.objects.filter(
        available=True,
        orderitem__order__created_at__gte=thirty_days_ago,
        orderitem__order__status__in=['completed', 'delivered']
    ).annotate(
        units_sold=Sum('orderitem__quantity'),
        revenue=Sum(F('orderitem__quantity') * F('orderitem__price'))
    ).order_by('-units_sold')[:15]
    
    # Low performing products
    low_performers = Product.objects.filter(
        available=True,
        created_at__lte=thirty_days_ago  # At least 30 days old
    ).annotate(
        units_sold=Sum('orderitem__quantity'),
        revenue=Sum(F('orderitem__quantity') * F('orderitem__price'))
    ).filter(Q(units_sold__isnull=True) | Q(units_sold__lte=2)).order_by('created_at')[:10]
    
    # Stock analysis
    stock_alerts = Product.objects.filter(available=True, stock__lte=10).order_by('stock')
    out_of_stock = Product.objects.filter(available=True, stock=0).count()
    
    # Review analysis
    highly_rated = Product.objects.filter(
        available=True,
        reviews__is_approved=True
    ).annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    ).filter(avg_rating__gte=4.5, review_count__gte=5).order_by('-avg_rating')[:10]
    
    poorly_rated = Product.objects.filter(
        available=True,
        reviews__is_approved=True
    ).annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    ).filter(avg_rating__lte=3.0, review_count__gte=3).order_by('avg_rating')[:10]
    
    # Search performance
    popular_searches = SearchQuery.objects.filter(
        created_at__gte=thirty_days_ago
    ).values('query').annotate(
        search_count=Count('id')
    ).order_by('-search_count')[:10]
    
    context = {
        'best_sellers': best_sellers,
        'low_performers': low_performers,
        'stock_alerts': stock_alerts,
        'out_of_stock': out_of_stock,
        'highly_rated': highly_rated,
        'poorly_rated': poorly_rated,
        'popular_searches': popular_searches,
    }
    
    return render(request, 'admin/product_performance_dashboard.html', context)




@staff_member_required
def export_pricing_data(request):
    """
    Export pricing data to CSV
    """
    from django.http import HttpResponse
    import csv
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="pricing_data.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Product Name', 'Category', 'Current Price', 'Original Price', 'Discount %', 'Stock'])
    
    products = Product.objects.filter(available=True).select_related('category')
    for product in products:
        writer.writerow([
            product.name,
            product.category.name,
            product.price,
            product.original_price or product.price,
            product.get_discount_percentage(),
            product.stock
        ])
    
    return response


@staff_member_required
def pricing_recommendations_api(request):
    """API endpoint for dynamic pricing recommendations with currency support"""
    
    currency = request.GET.get('currency', 'INR').upper()
    recommendations = generate_pricing_recommendations(currency)
    
    return JsonResponse({
        'recommendations': recommendations,
        'currency': currency,
        'timestamp': timezone.now().isoformat()
    })


@staff_member_required
def category_pricing_analysis(request, category_id):
    """Detailed pricing analysis for a specific category"""
    
    try:
        category = Category.objects.get(id=category_id, is_active=True)
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)
    
    products = Product.objects.filter(category=category, available=True)
    
    # Basic statistics
    stats = products.aggregate(
        count=Count('id'),
        avg_price=Avg('price'),
        min_price=Min('price'),
        max_price=Max('price'),
        avg_rating=Avg('reviews__rating')
    )
    
    # Price distribution within category
    price_quartiles = []
    if products.exists():
        prices = list(products.values_list('price', flat=True))
        prices.sort()
        n = len(prices)
        
        price_quartiles = {
            'q1': prices[n//4] if n > 0 else 0,
            'median': prices[n//2] if n > 0 else 0,
            'q3': prices[3*n//4] if n > 0 else 0
        }
    
    # Competition analysis (products in similar price range from other categories)
    if stats['avg_price']:
        price_range_min = stats['avg_price'] * Decimal('0.8')  # 20% below average
        price_range_max = stats['avg_price'] * Decimal('1.2')  # 20% above average
        
        similar_priced_products = Product.objects.filter(
            available=True,
            price__gte=price_range_min,
            price__lte=price_range_max
        ).exclude(category=category).values(
            'category__name'
        ).annotate(
            count=Count('id'),
            avg_price=Avg('price')
        ).order_by('-count')[:5]
    else:
        similar_priced_products = []
    
    # Performance insights
    thirty_days_ago = timezone.now() - timedelta(days=30)
    performance_data = products.annotate(
        units_sold=Sum('orderitem__quantity'),
        revenue=Sum(F('orderitem__quantity') * F('orderitem__price')),
        avg_rating=Avg('reviews__rating')
    ).order_by('-revenue')
    
    context = {
        'category': category,
        'stats': stats,
        'price_quartiles': price_quartiles,
        'similar_priced_products': similar_priced_products,
        'performance_data': performance_data[:20],  # Top 20 products
    }
    
    if request.headers.get('Content-Type') == 'application/json':
        return JsonResponse(context)
    
    return render(request, 'admin/category_pricing_analysis.html', context)


def generate_pricing_recommendations(currency='INR'):
    """Generate intelligent pricing recommendations for specified currency"""
    recommendations = []
    
    # Define currency fields
    if currency == 'USD':
        price_field = 'price_usd'
        original_price_field = 'original_price_usd'
        currency_symbol = '$'
    else:
        price_field = 'price_inr'
        original_price_field = 'original_price_inr'
        currency_symbol = '₹'
    
    # Find products that could benefit from price increases
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # High demand, low stock products
    high_demand_products = Product.objects.filter(
        available=True,
        stock__lte=10,
        orderitem__order__created_at__gte=thirty_days_ago,
        **{f'{price_field}__isnull': False}
    ).annotate(
        demand_score=Sum('orderitem__quantity'),
        current_price=F(price_field)
    ).filter(demand_score__gte=5).order_by('-demand_score')[:5]
    
    for product in high_demand_products:
        current_price = getattr(product, price_field) or 0
        if current_price > 0:
            recommendations.append({
                'type': 'price_increase',
                'priority': 'high',
                'product_id': product.id,
                'product_name': product.name,
                'current_price': float(current_price),
                'suggested_price': float(current_price * Decimal('1.1')),  # 10% increase
                'reason': f'High demand ({product.demand_score} units sold) with low stock ({product.stock} remaining)',
                'potential_revenue_increase': float(current_price * Decimal('0.1') * product.demand_score),
                'currency': currency
            })
    
    # Products with low margins (high discounts) for selected currency
    discount_filter = {
        f'{original_price_field}__gt': F(price_field),
        f'{price_field}__isnull': False,
        f'{original_price_field}__isnull': False
    }
    
    high_discount_products = Product.objects.filter(
        available=True,
        **discount_filter
    ).annotate(
        current_price=F(price_field),
        orig_price=F(original_price_field),
        discount_percent=((F(original_price_field) - F(price_field)) / F(original_price_field)) * 100
    ).filter(discount_percent__gte=50).order_by('-discount_percent')[:5]
    
    for product in high_discount_products:
        current_price = getattr(product, price_field) or 0
        original_price = getattr(product, original_price_field) or 0
        
        if current_price > 0 and original_price > 0:
            discount_percent = ((original_price - current_price) / original_price) * 100
            recommendations.append({
                'type': 'reduce_discount',
                'priority': 'medium',
                'product_id': product.id,
                'product_name': product.name,
                'current_price': float(current_price),
                'suggested_price': float(original_price * Decimal('0.8')),  # 20% discount instead
                'reason': f'Currently at {discount_percent:.1f}% discount - consider reducing to 20%',
                'potential_revenue_increase': float((original_price * Decimal('0.8') - current_price) * 10),  # Assuming 10 units
                'currency': currency
            })
    
    # Underperforming products - consider price reduction for selected currency
    underperformers = Product.objects.filter(
        available=True,
        created_at__lte=thirty_days_ago,
        stock__gte=20,  # High stock
        **{f'{price_field}__isnull': False}
    ).annotate(
        units_sold=Sum('orderitem__quantity'),
        current_price=F(price_field)
    ).filter(Q(units_sold__isnull=True) | Q(units_sold__lte=2)).order_by('created_at')[:5]
    
    for product in underperformers:
        current_price = getattr(product, price_field) or 0
        
        if current_price > 0:
            # Get category average for comparison in selected currency
            category_avg_data = Product.objects.filter(
                category=product.category,
                available=True,
                **{f'{price_field}__isnull': False}
            ).exclude(id=product.id).aggregate(avg_price=Avg(price_field))
            
            category_avg = category_avg_data['avg_price'] or current_price
            
            if current_price > category_avg * Decimal('1.2'):  # 20% above category average
                price_diff_percent = ((current_price/category_avg-1)*100)
                recommendations.append({
                    'type': 'price_decrease',
                    'priority': 'medium',
                    'product_id': product.id,
                    'product_name': product.name,
                    'current_price': float(current_price),
                    'suggested_price': float(category_avg),
                    'reason': f'Poor sales with high stock ({product.stock}), price {price_diff_percent:.1f}% above category average',
                    'potential_sales_increase': 'Estimated 25% sales increase',
                    'currency': currency
                })
    
    return recommendations


@staff_member_required
def export_pricing_data(request):
    """Export pricing data to CSV with dual currency support"""
    import csv
    from django.http import HttpResponse
    
    currency = request.GET.get('currency', 'INR').upper()
    filename = f"pricing_analysis_{currency.lower()}.csv"
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['Product Name', 'Category', f'Current Price ({currency})', f'Original Price ({currency})', 
                    f'Discount % ({currency})', 'Stock', 'Avg Rating', 'Units Sold (30d)', 'Revenue (30d)',
                    'INR Price', 'USD Price'])
    
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    products = Product.objects.filter(available=True).annotate(
        units_sold=Sum('orderitem__quantity'),
        revenue=Sum(F('orderitem__quantity') * F('orderitem__price')),
        avg_rating=Avg('reviews__rating')
    )
    
    for product in products:
        discount_percent = product.get_discount_percentage(currency)
        current_price = product.get_price(currency)
        original_price = product.get_original_price(currency)
        
        writer.writerow([
            product.name,
            product.category.name,
            current_price or '',
            original_price or '',
            f'{discount_percent}%' if discount_percent else '',
            product.stock,
            round(product.avg_rating, 1) if product.avg_rating else '',
            product.units_sold or 0,
            round(product.revenue, 2) if product.revenue else 0,
            product.price_inr or '',
            product.price_usd or ''
        ])
    
    return response


# =============================================================================
# PRODUCT MANAGEMENT VIEWS
# =============================================================================

@staff_member_required
def product_list(request):
    """List all products with search and filtering"""
    products = Product.objects.select_related('category').all()
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(sku__icontains=search) |
            Q(brand__icontains=search)
        )
    
    # Status filtering
    status = request.GET.get('status')
    if status == 'active':
        products = products.filter(available=True)
    elif status == 'inactive':
        products = products.filter(available=False)
    elif status == 'low_stock':
        products = products.filter(stock__lte=10)
    elif status == 'out_of_stock':
        products = products.filter(stock=0)
    
    # Category filtering
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Ordering
    order_by = request.GET.get('order_by', '-created_at')
    products = products.order_by(order_by)
    
    # Pagination
    paginator = Paginator(products, 25)  # 25 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all categories for filter dropdown
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'products': page_obj,
        'categories': categories,
        'search': search,
        'status': status,
        'category_id': int(category_id) if category_id else None,
        'order_by': order_by,
        'total_count': products.count(),
    }
    
    return render(request, 'admin/products/product_list.html', context)


@staff_member_required
def product_detail(request, product_id):
    """View product details"""
    product = get_object_or_404(Product, id=product_id)
    
    # Get related data
    images = product.images.all()
    specifications = product.specifications.all()
    recent_orders = OrderItem.objects.filter(product=product).select_related('order')[:10]
    reviews = product.reviews.filter(is_approved=True)[:10]
    
    context = {
        'product': product,
        'images': images,
        'specifications': specifications,
        'recent_orders': recent_orders,
        'reviews': reviews,
    }
    
    return render(request, 'admin/products/product_detail.html', context)


@staff_member_required
def product_create(request):
    """Create new product with manual dual currency pricing"""
    
    if request.method == 'POST':
        form = EnhancedProductAdminForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            
            # Handle manual dual currency pricing - no conversion, admin sets both
            product.price_inr = form.cleaned_data['price_inr']
            product.price_usd = form.cleaned_data['price_usd']
            product.original_price_inr = form.cleaned_data.get('original_price_inr')
            product.original_price_usd = form.cleaned_data.get('original_price_usd')
            
            # Maintain backward compatibility (can be removed later)
            product.price = form.cleaned_data['price_inr']  # Default to INR
            product.original_price = form.cleaned_data.get('original_price_inr')
            
            product.save()
            
            messages.success(
                request, 
                f'Product "{product.name}" created successfully! '
                f'INR: ₹{product.price_inr}, USD: ${product.price_usd}'
            )
            return redirect('admin_dashboard:product_list')
    else:
        form = EnhancedProductAdminForm()
    
    context = {
        'form': form,
        'title': 'Add New Product - Manual Currency Pricing',
        'submit_text': 'Create Product',
        'currency_mode': 'manual',
        'help_text': 'Set both INR and USD prices manually. No automatic conversion will be applied.',
    }
    
    return render(request, 'admin/products/product_form.html', context)


@staff_member_required
def product_edit(request, product_id):
    """Edit existing product with manual dual currency pricing"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = EnhancedProductAdminForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            # Handle manual dual currency pricing - no conversion
            updated_product = form.save(commit=False)
            
            # Update dual currency fields
            updated_product.price_inr = form.cleaned_data['price_inr']
            updated_product.price_usd = form.cleaned_data['price_usd']
            updated_product.original_price_inr = form.cleaned_data.get('original_price_inr')
            updated_product.original_price_usd = form.cleaned_data.get('original_price_usd')
            
            # Maintain backward compatibility (can be removed later)
            updated_product.price = form.cleaned_data['price_inr']  # Default to INR
            updated_product.original_price = form.cleaned_data.get('original_price_inr')
            
            # Handle slug changes if requested
            old_slug = product.slug
            new_slug = form.cleaned_data.get('slug')
            update_slug = form.cleaned_data.get('update_slug', False)
            
            if update_slug and new_slug and new_slug != old_slug:
                # Save the old slug for redirection
                from .models import ProductSlug
                try:
                    ProductSlug.objects.get_or_create(
                        product=updated_product, 
                        slug=old_slug
                    )
                except:
                    pass  # Ignore if already exists
                    
                # Update to new slug
                updated_product.slug = new_slug
                
                messages.info(
                    request, 
                    f'Slug updated from "{old_slug}" to "{new_slug}". '
                    f'Old URLs will redirect automatically.'
                )
            
            updated_product.save()
                
            messages.success(
                request, 
                f'Product "{updated_product.name}" updated successfully! '
                f'INR: ₹{updated_product.price_inr}, USD: ${updated_product.price_usd}'
            )
            return redirect('admin_dashboard:product_list')
    else:
        form = EnhancedProductAdminForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'title': f'Edit Product: {product.name}',
        'submit_text': 'Update Product',
        'currency_mode': 'manual',
        'help_text': 'Update both INR and USD prices manually. No automatic conversion will be applied.',
    }
    
    return render(request, 'admin/products/product_form.html', context)


@staff_member_required
def product_delete(request, product_id):
    """Delete product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return redirect('admin_dashboard:product_list')
    
    context = {
        'product': product,
        'title': f'Delete Product: {product.name}',
    }
    
    return render(request, 'admin/products/product_delete.html', context)


# =============================================================================
# ORDER MANAGEMENT VIEWS  
# =============================================================================

@staff_member_required
def order_list(request):
    """List all orders with filtering"""
    orders = Order.objects.select_related('user').all()
    
    # Status filtering
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        orders = orders.filter(
            Q(order_id__icontains=search) |
            Q(email__icontains=search) |
            Q(user__username__icontains=search)
        )
    
    orders = orders.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'orders': page_obj,
        'search': search,
        'status': status,
        'status_choices': Order._meta.get_field('status').choices,
        'total_count': orders.count(),
    }
    
    return render(request, 'admin/orders/order_list.html', context)


@staff_member_required
def order_detail(request, order_id):
    """View order details with complete order processing functionality"""
    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.select_related('product').all()
    
    # Handle order actions (status updates, cancellations, etc.)
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'confirm' and order.status == 'pending':
            order.status = 'processing'
            order.save()
            # Send confirmation email to customer
            send_order_notification(order, 'confirmed')
            messages.success(request, f'Order {order.order_id} confirmed and customer notified.')
            
        elif action == 'ship' and order.status in ['processing', 'confirmed']:
            tracking_number = request.POST.get('tracking_number', '')
            if tracking_number:
                order.tracking_number = tracking_number
            order.status = 'shipped'
            order.save()
            # Send shipping notification to customer
            send_order_notification(order, 'shipped')
            messages.success(request, f'Order {order.order_id} marked as shipped and customer notified.')
            
        elif action == 'deliver' and order.status == 'shipped':
            order.status = 'delivered'
            order.save()
            # Send delivery confirmation to customer
            send_order_notification(order, 'delivered')
            messages.success(request, f'Order {order.order_id} marked as delivered.')
            
        elif action == 'cancel':
            cancellation_reason = request.POST.get('cancellation_reason', '')
            if cancellation_reason:
                order.status = 'cancelled'
                order.cancellation_reason = cancellation_reason
                order.cancelled_at = timezone.now()
                order.save()
                # Process refund if payment was made
                if hasattr(order, 'is_paid') and order.is_paid:
                    process_order_refund(order)
                # Send cancellation notification
                send_order_notification(order, 'cancelled')
                messages.success(request, f'Order {order.order_id} cancelled successfully.')
            else:
                messages.error(request, 'Cancellation reason is required.')
        
        return redirect('admin_dashboard:order_detail', order_id=order.id)
    
    # Get customer order history for context
    customer_orders = Order.objects.filter(user=order.user).exclude(id=order.id)[:5]
    
    context = {
        'order': order,
        'order_items': order_items,
        'customer_orders': customer_orders,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'admin/orders/order_detail.html', context)


@staff_member_required
def order_edit(request, order_id):
    """Edit order (mainly status updates)"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status and new_status != order.status:
            old_status = order.status
            order.status = new_status
            order.save()
            messages.success(request, f'Order status updated from "{old_status}" to "{new_status}"')
            return redirect('admin_dashboard:order_detail', order_id=order.id)
    
    context = {
        'order': order,
        'status_choices': Order._meta.get_field('status').choices,
    }
    
    return render(request, 'admin/orders/order_edit.html', context)


@staff_member_required
def order_delete(request, order_id):
    """Delete order from database"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        if 'confirm_delete' in request.POST:
            order_id_display = order.order_id
            try:
                order.delete()
                messages.success(request, f'Order #{order_id_display} has been successfully deleted from the system.')
                logger.info(f'Admin {request.user.username} deleted order {order_id_display}')
                return redirect('admin_dashboard:order_list')
            except Exception as e:
                logger.error(f'Failed to delete order {order_id_display}: {e}')
                messages.error(request, f'Failed to delete order. Error: {str(e)}')
                return redirect('admin_dashboard:order_list')
        else:
            messages.error(request, 'Please confirm the deletion by checking the confirmation box.')
            return redirect('admin_dashboard:order_edit', order_id=order.id)
    
    context = {
        'order': order,
    }
    
    return render(request, 'admin/orders/order_delete.html', context)


# =============================================================================
# CATEGORY MANAGEMENT VIEWS
# =============================================================================

@staff_member_required
def category_list(request):
    """List all categories"""
    categories = Category.objects.all().order_by('name')
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        categories = categories.filter(name__icontains=search)
    
    context = {
        'categories': categories,
        'search': search,
    }
    
    return render(request, 'admin/categories/category_list.html', context)


@staff_member_required
def category_create(request):
    """Create new category"""
    CategoryForm = modelform_factory(Category, exclude=['slug', 'created_at', 'updated_at'])
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('admin_dashboard:category_list')
    else:
        form = CategoryForm()
    
    context = {
        'form': form,
        'title': 'Add New Category',
        'submit_text': 'Create Category',
    }
    
    return render(request, 'admin/categories/category_form.html', context)


@staff_member_required
def category_edit(request, category_id):
    """Edit existing category"""
    category = get_object_or_404(Category, id=category_id)
    CategoryForm = modelform_factory(Category, exclude=['slug', 'created_at', 'updated_at'])
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('admin_dashboard:category_list')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'title': f'Edit Category: {category.name}',
        'submit_text': 'Update Category',
    }
    
    return render(request, 'admin/categories/category_form.html', context)


@staff_member_required
def category_delete(request, category_id):
    """Delete category with confirmation"""
    category = get_object_or_404(Category, id=category_id)
    
    # Check if category has products
    product_count = category.product_set.count()
    
    if request.method == 'POST':
        # Handle category deletion
        if 'confirm_delete' in request.POST:
            category_name = category.name
            category.delete()
            messages.success(request, f'Category "{category_name}" deleted successfully!')
            return redirect('admin_dashboard:category_list')
        else:
            messages.error(request, 'Please confirm the deletion by checking the confirmation box.')
    
    context = {
        'category': category,
        'product_count': product_count,
    }
    
    return render(request, 'admin/categories/category_delete.html', context)


# =============================================================================
# REVIEW MANAGEMENT VIEWS
# =============================================================================

@staff_member_required
def review_list(request):
    """List all reviews with moderation"""
    reviews = Review.objects.select_related('product', 'user').all()
    
    # Filter by approval status
    approval = request.GET.get('approval')
    if approval == 'pending':
        reviews = reviews.filter(is_approved=False)
    elif approval == 'approved':
        reviews = reviews.filter(is_approved=True)
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        reviews = reviews.filter(
            Q(product__name__icontains=search) |
            Q(user__username__icontains=search) |
            Q(title__icontains=search)
        )
    
    reviews = reviews.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(reviews, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'reviews': page_obj,
        'search': search,
        'approval': approval,
        'total_count': reviews.count(),
        'pending_count': Review.objects.filter(is_approved=False).count(),
    }
    
    return render(request, 'admin/reviews/review_list.html', context)


@staff_member_required
def review_edit(request, review_id):
    """Edit/moderate review"""
    review = get_object_or_404(Review, id=review_id)
    ReviewForm = modelform_factory(Review, fields=['rating', 'title', 'comment', 'is_approved'])
    
    if request.method == 'POST':
        # Handle quick actions
        quick_action = request.POST.get('quick_action')
        if quick_action == 'approve':
            review.is_approved = True
            review.save()
            messages.success(request, 'Review approved successfully!')
            return redirect('admin_dashboard:review_list')
        elif quick_action == 'unapprove':
            review.is_approved = False
            review.save()
            messages.success(request, 'Review set to pending!')
            return redirect('admin_dashboard:review_list')
        elif quick_action == 'flag':
            review.is_approved = False
            review.save()
            messages.warning(request, 'Review flagged as inappropriate!')
            return redirect('admin_dashboard:review_list')
        else:
            # Handle regular form submission
            form = ReviewForm(request.POST, instance=review)
            if form.is_valid():
                # Handle admin response
                admin_response = request.POST.get('admin_response', '')
                if hasattr(review, 'admin_response'):
                    review.admin_response = admin_response
                review = form.save()
                messages.success(request, 'Review updated successfully!')
                return redirect('admin_dashboard:review_list')
    else:
        form = ReviewForm(instance=review)
    
    context = {
        'review': review,
        'form': form,
    }
    
    return render(request, 'admin/reviews/review_edit.html', context)


# =============================================================================
# USER MANAGEMENT VIEWS
# =============================================================================

@staff_member_required
def user_list(request):
    """List all users"""
    users = User.objects.all()
    
    # Filter by user type
    user_type = request.GET.get('user_type')
    if user_type == 'staff':
        users = users.filter(is_staff=True)
    elif user_type == 'customers':
        users = users.filter(is_staff=False)
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    users = users.order_by('-date_joined')
    
    # Pagination
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'users': page_obj,
        'search': search,
        'user_type': user_type,
        'total_count': users.count(),
    }
    
    return render(request, 'admin/users/user_list.html', context)


@staff_member_required
def user_detail(request, user_id):
    """View comprehensive user details with analytics"""
    user = get_object_or_404(User, id=user_id)
    
    # Get user's profile if exists
    try:
        profile = user.profile
    except:
        profile = None
    
    # Comprehensive order analytics
    orders = Order.objects.filter(user=user)
    recent_orders = orders.order_by('-created_at')[:10]
    
    # Customer analytics
    total_orders = orders.count()
    completed_orders = orders.filter(status='delivered').count()
    cancelled_orders = orders.filter(status='cancelled').count()
    total_spent = orders.filter(status__in=['delivered', 'shipped']).aggregate(Sum('total'))['total__sum'] or 0
    avg_order_value = total_spent / total_orders if total_orders > 0 else 0
    
    # Order status breakdown
    status_breakdown = orders.values('status').annotate(count=Count('id')).order_by('-count')
    
    # Customer activity timeline
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_activity = {
        'orders_last_30_days': orders.filter(created_at__gte=thirty_days_ago).count(),
        'last_order_date': orders.order_by('-created_at').first().created_at if orders.exists() else None,
        'favorite_categories': get_customer_favorite_categories(user),
        'payment_methods': orders.exclude(payment_method__isnull=True).values_list('payment_method', flat=True).distinct(),
    }
    
    # Customer reviews and engagement
    reviews = Review.objects.filter(user=user)
    review_stats = {
        'total_reviews': reviews.count(),
        'approved_reviews': reviews.filter(is_approved=True).count(),
        'avg_rating': reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
    }
    
    # Customer lifetime value analysis
    clv_data = get_customer_lifetime_value(user)
    
    context = {
        'user': user,
        'profile': profile,
        'recent_orders': recent_orders,
        'customer_analytics': {
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'cancelled_orders': cancelled_orders,
            'total_spent': total_spent,
            'avg_order_value': avg_order_value,
            'status_breakdown': status_breakdown,
        },
        'recent_activity': recent_activity,
        'review_stats': review_stats,
        'customer_since_days': (timezone.now().date() - user.date_joined.date()).days,
        'clv_data': clv_data,
    }
    
    return render(request, 'admin/users/user_detail.html', context)


@staff_member_required
def user_edit(request, user_id):
    """Edit user details"""
    user = get_object_or_404(User, id=user_id)
    UserForm = modelform_factory(User, fields=['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff'])
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.username}" updated successfully!')
            return redirect('admin_dashboard:user_detail', user_id=user.id)
    else:
        form = UserForm(instance=user)
    
    context = {
        'form': form,
        'user': user,
        'title': f'Edit User: {user.username}',
        'submit_text': 'Update User',
    }
    
    return render(request, 'admin/users/user_form.html', context)


# =============================================================================
# CURRENCY CONVERSION AND BULK OPERATIONS
# =============================================================================

@staff_member_required
def currency_conversion_view(request):
    """Currency conversion tool for admin"""
    form = CurrencyConversionForm()
    conversion_results = []
    
    if request.method == 'POST':
        form = CurrencyConversionForm(request.POST)
        if form.is_valid():
            from_currency = form.cleaned_data['from_currency']
            to_currency = form.cleaned_data['to_currency']
            apply_to_products = form.cleaned_data['apply_to_products']
            update_original = form.cleaned_data['update_original_prices']
            
            rates = get_exchange_rates()
            conversion_rate = form.get_conversion_rate()
            
            if apply_to_products:
                products = Product.objects.filter(available=True)
                conversion_results = []
                
                for product in products:
                    old_price = product.price
                    new_price = convert_price(product.price, from_currency, to_currency, rates)
                    
                    old_original = product.original_price
                    new_original = None
                    if update_original and old_original:
                        new_original = convert_price(old_original, from_currency, to_currency, rates)
                    
                    conversion_results.append({
                        'product': product,
                        'old_price': old_price,
                        'new_price': new_price,
                        'old_original': old_original,
                        'new_original': new_original,
                        'price_change': new_price - old_price,
                        'conversion_rate': conversion_rate
                    })
                    
                    # Apply conversion (uncomment when ready to implement)
                    # product.price = new_price
                    # if update_original and new_original:
                    #     product.original_price = new_original
                    # product.save()
                
                messages.success(request, f'Currency conversion preview completed. {len(conversion_results)} products would be affected.')
            
    context = {
        'form': form,
        'conversion_results': conversion_results,
        'current_rates': get_exchange_rates(),
    }
    
    return render(request, 'admin/currency_conversion.html', context)


@staff_member_required
def bulk_product_operations_view(request):
    """Bulk operations on products"""
    from .admin_forms import BulkProductOperationForm
    
    form = BulkProductOperationForm()
    operation_results = []
    
    if request.method == 'POST':
        form = BulkProductOperationForm(request.POST)
        selected_products = request.POST.getlist('selected_products')
        
        if form.is_valid() and selected_products:
            operation = form.cleaned_data['operation']
            products = Product.objects.filter(id__in=selected_products)
            
            if operation == 'activate':
                updated = products.update(available=True)
                messages.success(request, f'{updated} products activated successfully.')
                
            elif operation == 'deactivate':
                updated = products.update(available=False)
                messages.success(request, f'{updated} products deactivated successfully.')
                
            elif operation == 'update_category':
                new_category = form.cleaned_data['new_category']
                if new_category:
                    updated = products.update(category=new_category)
                    messages.success(request, f'{updated} products moved to category "{new_category.name}".')
                    
            elif operation == 'apply_discount':
                discount_percent = form.cleaned_data['discount_percentage']
                if discount_percent:
                    for product in products:
                        if not product.original_price:
                            product.original_price = product.price
                        
                        discount_multiplier = 1 - (discount_percent / 100)
                        product.price = (product.original_price * discount_multiplier).quantize(Decimal('0.01'))
                        product.save()
                        
                    messages.success(request, f'{discount_percent}% discount applied to {products.count()} products.')
                    
            elif operation == 'update_stock':
                stock_adjustment = form.cleaned_data['stock_adjustment']
                if stock_adjustment is not None:
                    for product in products:
                        new_stock = max(0, product.stock + stock_adjustment)
                        product.stock = new_stock
                        product.save()
                        
                    action = 'increased' if stock_adjustment > 0 else 'decreased'
                    messages.success(request, f'Stock {action} by {abs(stock_adjustment)} for {products.count()} products.')
                    
            elif operation == 'convert_currency':
                target_currency = form.cleaned_data['target_currency']
                if target_currency:
                    rates = get_exchange_rates()
                    base_currency = 'INR'  # Assuming INR is base
                    
                    for product in products:
                        if target_currency != base_currency:
                            product.price = convert_price(product.price, base_currency, target_currency, rates)
                            if product.original_price:
                                product.original_price = convert_price(product.original_price, base_currency, target_currency, rates)
                            product.save()
                            
                    messages.success(request, f'Currency converted to {target_currency} for {products.count()} products.')
            
            return redirect('admin_dashboard:product_list')
        else:
            if not selected_products:
                messages.error(request, 'Please select products to perform bulk operations.')
    
    # Get all products for selection
    products = Product.objects.select_related('category').all()[:100]  # Limit for performance
    
    context = {
        'form': form,
        'products': products,
        'operation_results': operation_results,
    }
    
    return render(request, 'admin/bulk_operations.html', context)


# =============================================================================
# ORDER DOCUMENTS AND COMMUNICATION
# =============================================================================

@staff_member_required
def order_invoice(request, order_id):
    """Generate and display order invoice"""
    order = get_object_or_404(Order, id=order_id)
    return generate_invoice_pdf(order)

@staff_member_required  
def order_packing_slip(request, order_id):
    """Generate packing slip for order"""
    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.select_related('product').all()
    
    context = {
        'order': order,
        'order_items': order_items,
        'company_name': 'CartMax',
        'packing_date': timezone.now().date(),
    }
    
    return render(request, 'admin/orders/packing_slip.html', context)

@staff_member_required
def send_order_email(request, order_id):
    """Send custom email to order customer"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        email_type = request.POST.get('type', 'status_update')
        custom_message = request.POST.get('message', '')
        
        try:
            # Send notification based on type
            if email_type in ['confirmed', 'shipped', 'delivered', 'cancelled']:
                success = send_order_notification(order, email_type)
            else:
                # Custom message
                send_mail(
                    subject=f'Update about your order {order.order_id}',
                    message=custom_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.email or order.user.email],
                    fail_silently=False,
                )
                success = True
            
            if success:
                return JsonResponse({'success': True, 'message': 'Email sent successfully!'})
            else:
                return JsonResponse({'success': False, 'error': 'Failed to send email'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# =============================================================================
# CUSTOMER COMMUNICATION AND MANAGEMENT
# =============================================================================

@staff_member_required
def send_customer_email_view(request, user_id):
    """Send email to specific customer"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        subject = request.POST.get('subject', '')
        message = request.POST.get('message', '')
        email_type = request.POST.get('email_type', 'custom')
        
        if not subject or not message:
            return JsonResponse({'success': False, 'error': 'Subject and message are required'})
        
        try:
            success = send_customer_email(user, subject, message)
            
            if success:
                return JsonResponse({'success': True, 'message': 'Email sent successfully!'})
            else:
                return JsonResponse({'success': False, 'error': 'Failed to send email'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@staff_member_required
def customer_analytics_api(request):
    """API endpoint for customer analytics data"""
    try:
        # Get customer segments
        total_customers = User.objects.filter(is_staff=False).count()
        active_customers = User.objects.filter(
            is_staff=False,
            orders__created_at__gte=timezone.now() - timedelta(days=90)
        ).distinct().count()
        
        # Customer segmentation
        segments = {
            'VIP': User.objects.filter(
                orders__status__in=['delivered', 'shipped']
            ).annotate(
                total_spent=Sum('orders__total')
            ).filter(total_spent__gte=10000).count(),
            
            'Premium': User.objects.filter(
                orders__status__in=['delivered', 'shipped']
            ).annotate(
                total_spent=Sum('orders__total')
            ).filter(total_spent__gte=5000, total_spent__lt=10000).count(),
            
            'Regular': User.objects.filter(
                orders__status__in=['delivered', 'shipped']
            ).annotate(
                total_spent=Sum('orders__total')
            ).filter(total_spent__gte=1000, total_spent__lt=5000).count(),
        }
        
        # Monthly customer acquisition
        monthly_data = []
        for i in range(12):
            month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
            next_month = month_start + timedelta(days=32)
            next_month = next_month.replace(day=1)
            
            new_customers = User.objects.filter(
                is_staff=False,
                date_joined__gte=month_start,
                date_joined__lt=next_month
            ).count()
            
            monthly_data.append({
                'month': month_start.strftime('%b %Y'),
                'new_customers': new_customers
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'total_customers': total_customers,
                'active_customers': active_customers,
                'segments': segments,
                'monthly_acquisition': list(reversed(monthly_data))
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@staff_member_required
def bulk_customer_operations(request):
    """Bulk operations on customers"""
    if request.method == 'POST':
        operation = request.POST.get('operation')
        customer_ids = request.POST.getlist('customer_ids')
        
        if not customer_ids:
            messages.error(request, 'Please select customers to perform operations on.')
            return redirect('admin_dashboard:user_list')
        
        customers = User.objects.filter(id__in=customer_ids, is_staff=False)
        
        if operation == 'activate':
            updated = customers.update(is_active=True)
            messages.success(request, f'{updated} customers activated successfully.')
            
        elif operation == 'deactivate':
            updated = customers.update(is_active=False)
            messages.success(request, f'{updated} customers deactivated successfully.')
            
        elif operation == 'send_email':
            subject = request.POST.get('email_subject', '')
            message = request.POST.get('email_message', '')
            
            if subject and message:
                success_count = 0
                for customer in customers:
                    if send_customer_email(customer, subject, message):
                        success_count += 1
                
                messages.success(request, f'Email sent to {success_count} out of {customers.count()} customers.')
            else:
                messages.error(request, 'Email subject and message are required.')
        
        return redirect('admin_dashboard:user_list')
    
    return redirect('admin_dashboard:user_list')


# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

@staff_member_required
def export_pricing_data(request):
    """Export product pricing data as CSV"""
    import csv
    from django.http import HttpResponse
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="pricing_data.csv"'},
    )
    
    writer = csv.writer(response)
    
    # Write CSV header
    writer.writerow([
        'Product ID',
        'Product Name',
        'SKU',
        'Category',
        'Current Price',
        'Original Price',
        'Discount %',
        'Stock',
        'Status',
        'Created Date',
        'Last Updated'
    ])
    
    # Get all products with related data
    products = Product.objects.select_related('category').all()
    
    for product in products:
        # Calculate discount percentage
        discount_percent = 0
        if product.original_price and product.original_price > 0:
            discount_percent = round(
                ((product.original_price - product.price) / product.original_price) * 100, 2
            )
        
        writer.writerow([
            product.id,
            product.name,
            product.sku or 'N/A',
            product.category.name if product.category else 'Uncategorized',
            float(product.price),
            float(product.original_price) if product.original_price else float(product.price),
            discount_percent,
            product.stock,
            'Active' if product.available else 'Inactive',
            product.created_at.strftime('%Y-%m-%d'),
            product.updated_at.strftime('%Y-%m-%d')
        ])
    
    return response


# =============================================================================
# DISCOUNT COUPON MANAGEMENT VIEWS
# =============================================================================

@staff_member_required
def coupon_list(request):
    """List all discount coupons"""
    coupons = DiscountCoupon.objects.all()
    
    # Filter by status
    status = request.GET.get('status')
    if status == 'active':
        coupons = coupons.filter(is_active=True)
    elif status == 'inactive':
        coupons = coupons.filter(is_active=False)
    elif status == 'expired':
        coupons = coupons.filter(expiration_date__lt=timezone.now())
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        coupons = coupons.filter(
            Q(coupon_code__icontains=search) |
            Q(description__icontains=search)
        )
    
    coupons = coupons.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(coupons, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'coupons': page_obj,
        'search': search,
        'status': status,
        'total_count': coupons.count(),
    }
    
    return render(request, 'admin/coupons/coupon_list.html', context)


@staff_member_required
def coupon_detail(request, coupon_id):
    """View coupon details with usage statistics"""
    coupon = get_object_or_404(DiscountCoupon, id=coupon_id)
    coupon_usages = CouponUsage.objects.filter(coupon=coupon).select_related('user')
    
    # Calculate usage statistics
    total_uses = coupon.usage_count
    unique_users = coupon_usages.values('user').distinct().count()
    remaining_uses = coupon.max_usage_limit - total_uses if coupon.max_usage_limit else 'Unlimited'
    
    context = {
        'coupon': coupon,
        'coupon_usages': coupon_usages[:10],
        'total_uses': total_uses,
        'unique_users': unique_users,
        'remaining_uses': remaining_uses,
    }
    
    return render(request, 'admin/coupons/coupon_detail.html', context)


@staff_member_required
def coupon_create(request):
    """Create new discount coupon"""
    CouponForm = modelform_factory(
        DiscountCoupon,
        exclude=['usage_count', 'created_at', 'updated_at', 'created_by']
    )
    
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            coupon = form.save(commit=False)
            coupon.coupon_code = coupon.coupon_code.upper().strip()
            coupon.created_by = request.user
            coupon.save()
            messages.success(
                request,
                f'Coupon "{coupon.coupon_code}" created successfully! '
                f'Discount: {coupon.discount_value} {"% off" if coupon.discount_type == "percentage" else "off"}'
            )
            return redirect('admin_dashboard:coupon_list')
    else:
        form = CouponForm()
    
    context = {
        'form': form,
        'title': 'Create New Discount Coupon',
        'submit_text': 'Create Coupon',
    }
    
    return render(request, 'admin/coupons/coupon_form.html', context)


@staff_member_required
def coupon_edit(request, coupon_id):
    """Edit existing discount coupon"""
    coupon = get_object_or_404(DiscountCoupon, id=coupon_id)
    CouponForm = modelform_factory(
        DiscountCoupon,
        exclude=['usage_count', 'created_at', 'updated_at', 'created_by']
    )
    
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            coupon = form.save(commit=False)
            coupon.coupon_code = coupon.coupon_code.upper().strip()
            coupon.save()
            messages.success(
                request,
                f'Coupon "{coupon.coupon_code}" updated successfully!'
            )
            return redirect('admin_dashboard:coupon_list')
    else:
        form = CouponForm(instance=coupon)
    
    context = {
        'form': form,
        'coupon': coupon,
        'title': f'Edit Coupon: {coupon.coupon_code}',
        'submit_text': 'Update Coupon',
    }
    
    return render(request, 'admin/coupons/coupon_form.html', context)


@staff_member_required
def coupon_delete(request, coupon_id):
    """Delete discount coupon"""
    coupon = get_object_or_404(DiscountCoupon, id=coupon_id)
    
    if request.method == 'POST':
        if 'confirm_delete' in request.POST:
            coupon_code = coupon.coupon_code
            coupon.delete()
            messages.success(request, f'Coupon "{coupon_code}" deleted successfully!')
            return redirect('admin_dashboard:coupon_list')
        else:
            messages.error(request, 'Please confirm the deletion.')
    
    context = {
        'coupon': coupon,
        'title': f'Delete Coupon: {coupon.coupon_code}',
    }
    
    return render(request, 'admin/coupons/coupon_delete.html', context)
