from django.urls import path
from . import views
from . import api_views

app_name = 'store'

urlpatterns = [
    # Homepage and category pages
    path('', views.homepage, name='homepage'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('categories/', views.category_list, name='category_list'),
    
    # Product pages
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('search/', views.search_products, name='search_products'),
    
    # Cart functionality
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    
    # Wishlist functionality
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/move-to-cart/<int:product_id>/', views.move_to_cart_from_wishlist, name='move_to_cart_from_wishlist'),
    
    # Product comparison functionality
    path('comparison/', views.comparison_view, name='comparison'),
    path('comparison/add/<int:product_id>/', views.add_to_comparison, name='add_to_comparison'),
    path('comparison/remove/<int:product_id>/', views.remove_from_comparison, name='remove_from_comparison'),
    path('comparison/clear/', views.clear_comparison, name='clear_comparison'),
    
    # Checkout
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('order/<int:order_id>/invoice/', views.download_invoice, name='download_invoice'),
    
    # User authentication and profile
    path('account/auth/', views.unified_auth, name='unified_auth'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('orders/', views.order_history, name='order_history'),
    
    # Support pages
    path('help/', views.help_center, name='help_center'),
    path('contact/', views.contact, name='contact'),
    path('shipping/', views.shipping_info, name='shipping_info'),
    path('returns/', views.returns, name='returns'),
    
    # Legal pages
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('cookies-policy/', views.cookies_policy, name='cookies_policy'),
    
    # AJAX endpoints
    path('ajax/add-review/', views.add_review, name='add_review'),
    path('ajax/search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('ajax/track-search-click/', views.track_search_click, name='track_search_click'),
    
    # Currency switching
    path('ajax/set-cart-currency/', views.set_cart_currency, name='set_cart_currency'),
    path('cart/get-totals/', views.get_cart_totals, name='get_cart_totals'),
    
    # Custom Admin Dashboard APIs - Phase 1C
    path('admin-api/dashboard/', views.admin_dashboard_api, name='admin_dashboard_api'),
    path('admin-api/analytics/', views.admin_analytics_api, name='admin_analytics_api'),
    path('admin-api/system-health/', views.admin_system_health_api, name='admin_system_health_api'),
    
    # Bulk Operations APIs - Phase 2A
    path('admin-api/bulk-operations/', views.bulk_operations_api, name='bulk_operations_api'),
    path('admin-api/bulk-export/', views.bulk_export_api, name='bulk_export_api'),
    path('admin-api/advanced-search/', views.advanced_search_api, name='advanced_search_api'),
    
    # Bulk Operations Interface
    path('admin/bulk-operations/', views.bulk_operations_view, name='bulk_operations'),
    
    # Product Import System
    path('admin/product-import/', views.product_import_view, name='product_import'),
    path('admin-api/product-import/upload/', views.product_import_upload_api, name='product_import_upload_api'),
    path('admin-api/product-import/execute/', views.product_import_execute_api, name='product_import_execute_api'),
    
    # Image Management System
    path('admin/image-management/', views.image_management_view, name='image_management'),
    path('admin-api/image/upload/', views.image_upload_api, name='image_upload_api'),
    path('admin-api/image/process/', views.image_process_api, name='image_process_api'),
    path('admin-api/image/gallery/', views.image_gallery_api, name='image_gallery_api'),
    path('admin-api/image/batch-process/', views.image_batch_process_api, name='image_batch_process_api'),
    
    # Site-wide Announcement System
    path('admin/announcements/', views.announcement_management_view, name='announcement_management'),
    path('admin-api/announcements/', views.announcement_list_api, name='announcement_list_api'),
    path('admin-api/announcements/create/', views.announcement_create_api, name='announcement_create_api'),
    
    # Coupon/Discount System APIs
    path('api/cart/apply-coupon/', api_views.apply_coupon_api, name='apply_coupon_api'),
    path('api/cart/remove-coupon/', api_views.remove_coupon_api, name='remove_coupon_api'),
    path('api/coupon/validate/', api_views.validate_coupon_api, name='validate_coupon_api'),
    path('api/cart/summary/', api_views.get_cart_summary_api, name='get_cart_summary_api'),
    path('api/cart/coupon/', api_views.get_applied_coupon_api, name='get_applied_coupon_api'),
]
