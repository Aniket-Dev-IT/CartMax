from django.urls import path
from . import admin_views

app_name = 'admin_dashboard'

urlpatterns = [
    # Main Admin Control Dashboard
    path('', admin_views.admin_control_dashboard, name='admin_control_dashboard'),
    
    # Enhanced Admin Dashboard URLs
    path('pricing-dashboard/', admin_views.pricing_dashboard, name='pricing_dashboard'),
    path('product-performance/', admin_views.product_performance_dashboard, name='product_performance_dashboard'),
    path('category-analysis/<int:category_id>/', admin_views.category_pricing_analysis, name='category_pricing_analysis'),
    
    # Product Management
    path('products/', admin_views.product_list, name='product_list'),
    path('products/new/', admin_views.product_create, name='product_create'),
    path('products/<int:product_id>/', admin_views.product_detail, name='product_detail'),
    path('products/<int:product_id>/edit/', admin_views.product_edit, name='product_edit'),
    path('products/<int:product_id>/delete/', admin_views.product_delete, name='product_delete'),
    
    # Order Management  
    path('orders/', admin_views.order_list, name='order_list'),
    path('orders/<int:order_id>/', admin_views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/edit/', admin_views.order_edit, name='order_edit'),
    path('orders/<int:order_id>/delete/', admin_views.order_delete, name='order_delete'),
    path('orders/<int:order_id>/invoice/', admin_views.order_invoice, name='order_invoice'),
    path('orders/<int:order_id>/packing-slip/', admin_views.order_packing_slip, name='order_packing_slip'),
    path('orders/<int:order_id>/send-email/', admin_views.send_order_email, name='send_order_email'),
    
    # Category Management
    path('categories/', admin_views.category_list, name='category_list'),
    path('categories/new/', admin_views.category_create, name='category_create'),
    path('categories/<int:category_id>/edit/', admin_views.category_edit, name='category_edit'),
    path('categories/<int:category_id>/delete/', admin_views.category_delete, name='category_delete'),
    
    # Review Management
    path('reviews/', admin_views.review_list, name='review_list'),
    path('reviews/<int:review_id>/edit/', admin_views.review_edit, name='review_edit'),
    
    # User Management
    path('users/', admin_views.user_list, name='user_list'),
    path('users/<int:user_id>/', admin_views.user_detail, name='user_detail'),
    path('users/<int:user_id>/edit/', admin_views.user_edit, name='user_edit'),
    path('users/<int:user_id>/send-email/', admin_views.send_customer_email_view, name='send_customer_email'),
    path('users/bulk-operations/', admin_views.bulk_customer_operations, name='bulk_customer_operations'),
    
    # Discount Coupon Management
    path('coupons/', admin_views.coupon_list, name='coupon_list'),
    path('coupons/new/', admin_views.coupon_create, name='coupon_create'),
    path('coupons/<int:coupon_id>/', admin_views.coupon_detail, name='coupon_detail'),
    path('coupons/<int:coupon_id>/edit/', admin_views.coupon_edit, name='coupon_edit'),
    path('coupons/<int:coupon_id>/delete/', admin_views.coupon_delete, name='coupon_delete'),
    
    # API Endpoints
    path('api/pricing-recommendations/', admin_views.pricing_recommendations_api, name='pricing_recommendations_api'),
    path('api/customer-analytics/', admin_views.customer_analytics_api, name='customer_analytics_api'),
    
    # Currency and Bulk Operations
    path('currency-conversion/', admin_views.currency_conversion_view, name='currency_conversion'),
    path('bulk-operations/', admin_views.bulk_product_operations_view, name='bulk_operations'),
    
    # Export Functions
    path('export/pricing-data/', admin_views.export_pricing_data, name='export_pricing_data'),
]
